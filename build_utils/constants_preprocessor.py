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
                        if isinstance(item.value, ast.Constant):
                            member_value = item.value.value
                            pyx_lines.append(f"    {member_name} = {member_value}")

            pyx_lines.append("")

        elif isinstance(node, ast.Assign):
            # Collect global constants
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                member_name = node.targets[0].id
                if isinstance(node.value, ast.Constant):
                    member_value = node.value.value
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
