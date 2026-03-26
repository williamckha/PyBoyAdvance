import ast
import os
import re
from dataclasses import dataclass


@dataclass
class Constant:
    scope: str | None
    name: str
    replacement_name: str | None
    value: int


def preprocess_constants(file_paths: list[str | os.PathLike]) -> list[str | os.PathLike]:
    """
    Generate constants.pxd and constants.pyx files for constants.py files containing
    enums and global constants.

    IntEnum/IntFlag/Enum definitions are converted to named cdef enum definitions.
    Global constants are placed in an anonymous cdef enum.

    Name mangling is applied to avoid name conflicts (in C, all enum members share
    the same namespace).
    """
    preprocessed = []
    constants: dict[tuple[str | None, str], Constant] = {}
    constant_names: set[str] = set()

    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        base, ext = os.path.splitext(file_name)
        if "constants" in base:
            generated_pyx_file = generate_constants_pxd_pyx(
                file_path,
                constants,
                constant_names,
            )
            preprocessed.append(generated_pyx_file)
        else:
            preprocessed.append(file_path)

    replace_constant_names(preprocessed, constants)

    return preprocessed


def generate_constants_pxd_pyx(
    py_file_path: str | os.PathLike,
    constants: dict[tuple[str | None, str], Constant],
    constant_names: set[str],
) -> str | os.PathLike:
    with open(py_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)

    pxd_lines = []
    global_constants = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            # Convert IntEnum/IntFlag/Enum classes to cdef enum definitions
            bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
            if not any(base in ("IntEnum", "IntFlag", "Enum") for base in bases):
                continue

            pxd_lines.append(f"cdef enum {node.name}:")

            for item in node.body:
                if isinstance(item, ast.Assign):
                    if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                        member_name = item.targets[0].id
                        member_value = _eval_int_expr(item.value, constants, node.name)

                        if member_name in constant_names:
                            new_member_name = node.name + "_" + member_name
                            constants[(node.name, member_name)] = Constant(
                                node.name,
                                member_name,
                                new_member_name,
                                member_value,
                            )
                            constant_names.add(new_member_name)
                            pxd_lines.append(f"    {new_member_name} = {member_value}")
                        else:
                            constants[(node.name, member_name)] = Constant(
                                node.name,
                                member_name,
                                None,
                                member_value,
                            )
                            constant_names.add(member_name)
                            pxd_lines.append(f"    {member_name} = {member_value}")

            pxd_lines.append("")

        elif isinstance(node, ast.Assign):
            # Collect global constants
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                constant_name = node.targets[0].id
                constant_value = _eval_int_expr(node.value, constants, None)

                if constant_name in constant_names:
                    new_constant_name = "GLOB_" + constant_name
                    constants[(None, constant_name)] = Constant(
                        None,
                        constant_name,
                        new_constant_name,
                        constant_value,
                    )
                    constant_names.add(new_constant_name)
                else:
                    constants[(None, constant_name)] = Constant(
                        None,
                        constant_name,
                        None,
                        constant_value,
                    )
                    constant_names.add(constant_name)

                global_constants.append(constants[(None, constant_name)])

    if global_constants:
        pxd_lines.append("cdef enum:")
        for constant in global_constants:
            if constant.replacement_name:
                pxd_lines.append(f"    {constant.replacement_name} = {constant.value}")
            else:
                pxd_lines.append(f"    {constant.name} = {constant.value}")
        pxd_lines.append("")

    base = py_file_path.split(".", 1)[0]

    pxd_path = base + ".pxd"
    with open(pxd_path, "w", encoding="utf-8") as f:
        f.write("\n".join(pxd_lines) + "\n")

    pyx_path = base + ".pyx"
    with open(pyx_path, "w", encoding="utf-8") as f:
        f.write("")

    return pyx_path


def replace_constant_names(
    file_paths: list[str | os.PathLike],
    constants: dict[tuple[str | None, str], Constant],
):
    replacements = {}
    for constant in constants.values():
        if constant.replacement_name:
            if constant.scope:
                pattern = constant.scope + "\\." + constant.name
                replacements[pattern] = constant.scope + "." + constant.replacement_name
            else:
                pattern = "[^.]" + constant.name
                replacements[pattern] = constant.replacement_name

    print(replacements)

    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

            for pattern, replacement in replacements.items():
                content = re.sub(pattern, replacement, content)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)


def _eval_int_expr(
    node: ast.AST, constants: dict[tuple[str | None, str], Constant], scope: str | None
) -> int:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.Name):
        if (scope, node.id) in constants:
            return constants[(scope, node.id)].value
        if (None, node.id) in constants:
            return constants[(None, node.id)].value
        raise ValueError(f"Unknown name: ({scope}, {node.id})")
    if isinstance(node, ast.BinOp):
        left = _eval_int_expr(node.left, constants, scope)
        right = _eval_int_expr(node.right, constants, scope)
        op = node.op
        if isinstance(op, ast.Add):
            return left + right
        if isinstance(op, ast.Sub):
            return left - right
        if isinstance(op, ast.Mult):
            return left * right
        if isinstance(op, ast.FloorDiv):
            return left // right
        if isinstance(op, ast.Mod):
            return left % right
        if isinstance(op, ast.LShift):
            return left << right
        if isinstance(op, ast.RShift):
            return left >> right
        if isinstance(op, ast.BitOr):
            return left | right
        if isinstance(op, ast.BitAnd):
            return left & right
        if isinstance(op, ast.BitXor):
            return left ^ right
        raise ValueError(f"Unsupported binary operator: {type(op).__name__}")
    if isinstance(node, ast.UnaryOp):
        operand = _eval_int_expr(node.operand, constants, scope)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.Invert):
            return ~operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
    raise ValueError(f"Unsupported expression node: {type(node).__name__}")
