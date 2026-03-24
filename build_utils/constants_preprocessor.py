import ast
import os


def preprocess_constants(file_paths: list[str | os.PathLike]) -> list[str | os.PathLike]:
    """
    Find all constants files in the given directory and generate corresponding .pyx files.
    """
    preprocessed = []

    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        base, ext = os.path.splitext(file_name)
        if "constants" in base:
            generated_pyx_file = generate_constants_pyx(file_path)
            preprocessed.append(generated_pyx_file)
        else:
            preprocessed.append(file_path)

    return preprocessed


def generate_constants_pyx(py_file_path: str | os.PathLike) -> str | os.PathLike:
    """
    Generate a .pyx file from a Python file containing enums and constants.

    IntEnum/IntFlag/Enum definitions are converted to named cpdef enum definitions.
    Global constants are placed in an anonymous cdef enum.
    """
    with open(py_file_path, "r", encoding="utf-8") as f:
        content = f.read()

    tree = ast.parse(content)

    pyx_lines = []
    global_constants = []
    constants: dict[str, int] = {}

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            # Convert IntEnum/IntFlag/Enum classes to cdef enum definitions
            bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
            if not any(base in ("IntEnum", "IntFlag", "Enum") for base in bases):
                continue

            pyx_lines.append(f"cpdef enum {node.name}:")

            for item in node.body:
                if isinstance(item, ast.Assign):
                    if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                        member_name = item.targets[0].id
                        if member_name in constants:
                            raise ValueError(f"Duplicate constant name: {member_name}")
                        member_value = _eval_int_expr(item.value, constants)
                        constants[member_name] = member_value
                        pyx_lines.append(f"    {member_name} = {member_value}")

            pyx_lines.append("")

        elif isinstance(node, ast.Assign):
            # Collect global constants
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                member_name = node.targets[0].id
                if member_name in constants:
                    raise ValueError(f"Duplicate constant name: {member_name}")
                member_value = _eval_int_expr(node.value, constants)
                constants[member_name] = member_value
                global_constants.append((member_name, member_value))

    if global_constants:
        pyx_lines.append("cdef enum:")
        for const_name, const_value in global_constants:
            pyx_lines.append(f"    {const_name} = {const_value}")
        pyx_lines.append("")

    base = py_file_path.split(".", 1)[0]

    pxd_path = base + ".pxd"
    with open(pxd_path, "w", encoding="utf-8") as f:
        f.write("\n".join(pyx_lines) + "\n")

    pyx_path = base + ".pyx"
    with open(pyx_path, "w", encoding="utf-8") as f:
        f.write("")

    return pyx_path


def _eval_int_expr(node: ast.AST, constants: dict[str, int]) -> int:
    if isinstance(node, ast.Constant) and isinstance(node.value, int):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in constants:
            return constants[node.id]
        raise ValueError(f"Unknown name: {node.id}")
    if isinstance(node, ast.BinOp):
        left = _eval_int_expr(node.left, constants)
        right = _eval_int_expr(node.right, constants)
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
        operand = _eval_int_expr(node.operand, constants)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        if isinstance(node.op, ast.Invert):
            return ~operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
    raise ValueError(f"Unsupported expression node: {type(node).__name__}")
