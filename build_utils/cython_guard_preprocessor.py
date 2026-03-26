import os
import re


def preprocess_cython_guards(file_paths: list[str | os.PathLike]) -> list[str | os.PathLike]:
    """
    Remove code blocks guarded by '# ifndef CYTHON' ... '# endif'.
    """
    start_re = re.compile(r"^\s*#\s*ifndef\s+CYTHON\b", flags=re.IGNORECASE)
    end_re = re.compile(r"^\s*#\s*endif\b", flags=re.IGNORECASE)

    for file_path in file_paths:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        out_lines = []
        in_guard = False

        for line in lines:
            if not in_guard and start_re.match(line):
                in_guard = True
                continue
            if in_guard and end_re.match(line):
                in_guard = False
                continue
            if not in_guard:
                out_lines.append(line)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("".join(out_lines))

    return file_paths
