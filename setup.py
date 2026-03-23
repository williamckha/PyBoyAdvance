import ast
import logging
import multiprocessing
import os
import platform
import sys
from multiprocessing import cpu_count
import numpy as np

from setuptools import Extension, setup, Command

CYTHON = platform.python_implementation() == "CPython"
ROOT_DIR = "pyboy_advance"
DEBUG = bool(os.getenv("GITHUB_ACTIONS"))

if not CYTHON:
    setup()
    exit(0)

from Cython.Build import cythonize  # noqa
from Cython.Compiler import DebugFlags, Errors  # noqa
from Cython.Distutils import build_ext as _build_ext  # noqa


def patched_error(position, message):
    if message == "Python object cannot be passed as a varargs parameter":
        # We ignore this error to pass PyObject* to logging
        return
    else:
        # print("Errors.error:", repr(position), repr(message)) ###
        if position is None:
            raise Errors.InternalError(message)
        err = Errors.CompileError(position, message)
        if DebugFlags.debug_exception_on_error:
            raise Exception(err)  # debug
        Errors.report_error(err)
        return err


Errors.error = patched_error


class build_ext(_build_ext):
    def initialize_options(self):
        super().initialize_options()
        # This is only for Cythonize. See finalize_options.
        if sys.platform == "win32":
            thread_count = 0  # Disables multiprocessing
        else:
            thread_count = cpu_count()

        # Fixing issue with nthreads in Cython
        if ((3, 8) <= sys.version_info[:2] and sys.platform == "darwin") or (
            (3, 14) <= sys.version_info[:2] and sys.platform == "linux"
        ):
            multiprocessing.set_start_method("fork", force=True)

        cflags = ["-O3"]
        if not DEBUG:
            cflags.append("-DCYTHON_WITHOUT_ASSERTIONS")
        # NOTE: For performance. Check if other platforms need an equivalent change.
        if sys.platform == "darwin":
            cflags.append(
                "-DCYTHON_INLINE=inline __attribute__ ((__unused__)) __attribute__((always_inline))"
            )

        py_pxd_files = prep_pxd_py_files()
        cythonize_files = map(
            lambda src: Extension(
                src.split(".")[0].replace(os.sep, "."),
                [src],
                extra_compile_args=cflags,
                extra_link_args=[] if DEBUG else ["-s", "-w"],
                include_dirs=[np.get_include()],
            ),
            list(py_pxd_files),
        )
        self.distribution.ext_modules = cythonize(
            [*cythonize_files],
            nthreads=thread_count,
            annotate=True,
            gdb_debug=False,
            language_level=3,
            compiler_directives={
                "annotation_typing": False,
                "boundscheck": False,
                "cdivision": True,
                "cdivision_warnings": False,
                "infer_types": True,
                "initializedcheck": False,
                "nonecheck": False,
                "overflowcheck": False,
                "wraparound": False,
                "legacy_implicit_noexcept": True,
            },
        )

    def finalize_options(self):
        # Use '-j' on the commandline to specify parallelism. Otherwise auto-detect.
        if getattr(self, "parallel", None) is None:
            self.parallel = cpu_count()
        super().finalize_options()


def prep_pxd_py_files():
    ignore_py_files = ["__main__.py", "conftest.py", "constants.py"]
    # Cython doesn't trigger a recompile on .py files, where only the .pxd file has changed. So we fix this here.
    # We also yield the py_files that have a .pxd file, as we feed these into the cythonize call.
    for root, dirs, files in os.walk(ROOT_DIR):
        for f in files:
            if os.path.splitext(f)[1] in [".py", ".pyx"] and f not in ignore_py_files:
                yield os.path.join(root, f)
            if os.path.splitext(f)[1] == ".pxd":
                py_file = os.path.join(root, os.path.splitext(f)[0]) + ".py"
                if os.path.isfile(py_file):
                    if os.path.getmtime(os.path.join(root, f)) > os.path.getmtime(py_file):
                        os.utime(py_file)


class GenerateConstantsPyxCommand(Command):
    description = "Generate .pyx files from Python files containing enums and constants"

    CONSTANTS_PY_FILES = [
        f"{ROOT_DIR}/cpu/constants.py",
        f"{ROOT_DIR}/memory/constants.py",
        f"{ROOT_DIR}/ppu/constants.py",
    ]

    def initialize_options(self):
        return

    def finalize_options(self):
        return

    def run(self):
        for file_path in self.CONSTANTS_PY_FILES:
            if os.path.isfile(file_path):
                pyx_path = self.generate_constants_pyx(file_path)
                if pyx_path:
                    self.announce(f"Generated: {pyx_path}", level=logging.INFO)
                else:
                    self.warn(f"Failed to generate .pyx for: {file_path}")
            else:
                self.warn(f"File not found: {file_path}")

    def generate_constants_pyx(self, py_file_path):
        """
        Generate a .pyx file from a Python file containing enums and constants.
        IntEnum/IntFlag/Enum definitions are converted to named cpdef enum definitions.
        Global constants are placed in an anonymous cdef enum.
        """
        try:
            with open(py_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            tree = ast.parse(content)

            pyx_lines = [
                f"# This file was auto-generated using `setup.py generate_constants_pyx`",
                f"# Generated from {py_file_path}",
                f"",
            ]

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

            pyx_path = py_file_path.replace(".py", ".pyx")
            with open(pyx_path, "w", encoding="utf-8") as f:
                f.write("\n".join(pyx_lines) + "\n")
            return pyx_path
        except Exception as e:
            self.announce(f"Could not generate pyx for {py_file_path}: {e}")


setup(
    cmdclass={
        "build_ext": build_ext,
        "generate_constants_pyx": GenerateConstantsPyxCommand,
    },
    ext_modules=[Extension("", [""])],  # Added to trigger a binary wheel
)
