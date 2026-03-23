import ast
from dataclasses import dataclass
from os import PathLike


def preprocess_properties(file_paths: list[str | PathLike]) -> list[str | PathLike]:
    """
    Preprocessor that converts @property and @property.setter decorators
    to explicit getter and setter methods, and replaces all property usages with
    method calls.
    """
    file_asts = {}
    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            source_code = f.read()
            file_asts[file_path] = ast.parse(source_code)

    collector = PropertyCollector()
    for tree in file_asts.values():
        collector.current_class = None
        collector.visit(tree)

    for file, tree in file_asts.items():
        transformer = PropertyTransformer(collector.class_properties)
        tree = transformer.visit(tree)

        replacer = PropertyUsageReplacer(collector.class_properties)
        tree = replacer.visit(tree)

        ast.fix_missing_locations(tree)

        preprocessed_code = ast.unparse(tree)

        with open(file, "w", encoding="utf-8") as f:
            f.write(preprocessed_code)

    return file_paths


@dataclass
class PropertyInfo:
    name: str
    getter_lineno: int
    getter_func: ast.FunctionDef | None = None
    setter_func: ast.FunctionDef | None = None


class PropertyCollector(ast.NodeVisitor):
    """Collects all @property decorators and their associated methods."""

    def __init__(self):
        self.current_class = None
        self.class_properties: dict[str, dict[str, PropertyInfo]] = {}

    def visit_ClassDef(self, node: ast.ClassDef):
        previous_class = self.current_class
        self.current_class = node.name

        if self.current_class not in self.class_properties:
            self.class_properties[self.current_class] = {}

        self.generic_visit(node)
        self.current_class = previous_class

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.current_class is None:
            return

        for decorator in node.decorator_list:
            # Check for @property
            if isinstance(decorator, ast.Name) and decorator.id == "property":
                prop_info = PropertyInfo(node.name, node.lineno)
                prop_info.getter_func = node
                self.class_properties[self.current_class][node.name] = prop_info

            # Check for @<name>.setter
            elif isinstance(decorator, ast.Attribute):
                if decorator.attr == "setter" and isinstance(decorator.value, ast.Name):
                    prop_name = decorator.value.id
                    self.class_properties[self.current_class][prop_name].setter_func = node


class PropertyUsageReplacer(ast.NodeTransformer):
    """Replaces property accesses with getter/setter method calls."""

    def __init__(self, properties: dict[str, dict[str, PropertyInfo]]):
        self.current_class = None
        self.property_names = set(
            [prop for class_props in properties.values() for prop in class_props.keys()]
        )

    def visit_ClassDef(self, node: ast.ClassDef):
        previous_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = previous_class
        return node

    def visit_Assign(self, node: ast.Assign):
        # Check for property assignment: obj.property_name = value
        if (
            len(node.targets) == 1
            and isinstance(node.targets[0], ast.Attribute)
            and node.targets[0].attr in self.property_names
        ):
            attr = node.targets[0]
            setter_name = f"set_{attr.attr}"

            # Visit the value side to replace any property accesses there
            new_value = self.visit(node.value)

            # Replace with setter call: obj.set_property_name(value)
            return ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=attr.value,
                        attr=setter_name,
                        ctx=ast.Load(),
                    ),
                    args=[new_value],
                    keywords=[],
                )
            )

        self.generic_visit(node)
        return node

    def visit_AugAssign(self, node: ast.AugAssign):
        # Check for property augmented assignment (e.g. obj.property_name += value)
        if isinstance(node.target, ast.Attribute) and node.target.attr in self.property_names:
            attr = node.target
            prop_name = attr.attr

            getter_name = f"get_{prop_name}"
            setter_name = f"set_{prop_name}"

            # obj.get_prop()
            getter_call = ast.Call(
                func=ast.Attribute(
                    value=attr.value,
                    attr=getter_name,
                    ctx=ast.Load(),
                ),
                args=[],
                keywords=[],
            )

            # Visit the value side to replace any property accesses there
            value = self.visit(node.value)

            # Build: obj.get_prop() <op> value
            new_value = ast.BinOp(
                left=getter_call,
                op=node.op,
                right=value,
            )

            # Replace with: obj.set_prop(obj.get_prop() <op> value)
            return ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=attr.value,
                        attr=setter_name,
                        ctx=ast.Load(),
                    ),
                    args=[new_value],
                    keywords=[],
                )
            )

        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        self.generic_visit(node)

        # Check if this is a property access (e.g. self.property_name or obj.property_name)
        if isinstance(node.ctx, ast.Load) and node.attr in self.property_names:
            # Replace with getter call: obj.get_property_name()
            getter_name = f"get_{node.attr}"
            return ast.Call(
                func=ast.Attribute(
                    value=node.value,
                    attr=getter_name,
                    ctx=ast.Load(),
                ),
                args=[],
                keywords=[],
            )

        return node


class PropertyTransformer(ast.NodeTransformer):
    """Transforms @property decorators into explicit getter/setter methods."""

    def __init__(self, properties: dict[str, dict[str, PropertyInfo]]):
        self.properties = properties
        self.current_class = None

    def visit_ClassDef(self, node: ast.ClassDef):
        previous_class = self.current_class
        self.current_class = node.name

        if node.name in self.properties:
            new_body = []

            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name in self.properties[node.name]:
                    prop_info = self.properties[node.name][item.name]
                    if prop_info.getter_func and prop_info.getter_func == item:
                        getter_method = self._create_getter_method(item)
                        new_body.append(getter_method)
                    elif prop_info.setter_func and prop_info.setter_func == item:
                        setter_method = self._create_setter_method(prop_info.setter_func, item.name)
                        new_body.append(setter_method)
                    else:
                        new_body.append(item)
                else:
                    new_body.append(item)

            node.body = new_body

        self.generic_visit(node)
        self.current_class = previous_class
        return node

    def _create_getter_method(self, original_func: ast.FunctionDef):
        getter_name = f"get_{original_func.name}"

        # Remove @property decorator
        decorators = [d for d in original_func.decorator_list if not self._is_property_decorator(d)]

        return ast.FunctionDef(
            name=getter_name,
            args=original_func.args,
            body=original_func.body,
            decorator_list=decorators,
            returns=original_func.returns,
            type_comment=original_func.type_comment,
        )

    def _create_setter_method(self, setter_func: ast.FunctionDef, property_name: str):
        setter_name = f"set_{property_name}"

        # Remove @property.setter decorator
        decorators = [
            d for d in setter_func.decorator_list if not self._is_property_setter_decorator(d)
        ]

        return ast.FunctionDef(
            name=setter_name,
            args=setter_func.args,
            body=setter_func.body,
            decorator_list=decorators,
            returns=setter_func.returns,
            type_comment=setter_func.type_comment,
        )

    @staticmethod
    def _is_property_decorator(decorator: ast.expr) -> bool:
        return isinstance(decorator, ast.Name) and decorator.id == "property"

    @staticmethod
    def _is_property_setter_decorator(decorator: ast.expr) -> bool:
        return (
            isinstance(decorator, ast.Attribute)
            and decorator.attr == "setter"
            and isinstance(decorator.value, ast.Name)
        )
