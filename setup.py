import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from build_utils.property_preprocessor import preprocess_properties
from build_utils.constants_preprocessor import preprocess_constants

import multiprocessing
import os
import platform
import shutil
from multiprocessing import cpu_count
import numpy as np

from setuptools import Extension, setup

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


class BuildExt(_build_ext):
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

        py_pxd_files = list(prep_pxd_py_files())

        preprocessed_files = []
        for src_file in py_pxd_files:
            build_file = src_file.replace(".py", ".build.py")
            shutil.copy(src_file, build_file)
            preprocessed_files.append(build_file)

        preprocessed_files = preprocess_properties(preprocessed_files)
        preprocessed_files = preprocess_constants(preprocessed_files)

        cythonize_files = map(
            lambda src: Extension(
                src.split(".")[0].replace(os.sep, "."),
                [src],
                extra_compile_args=cflags,
                extra_link_args=[] if DEBUG else ["-s", "-w"],
                include_dirs=[np.get_include()],
            ),
            preprocessed_files,
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
    ignore_py_files = ["__main__.py", "__init__.py", "conftest.py"]
    # Cython doesn't trigger a recompile on .py files, where only the .pxd file has changed. So we fix this here.
    # We also yield the py_files that have a .pxd file, as we feed these into the cythonize call.
    for root, dirs, files in os.walk(ROOT_DIR):
        for f in files:
            base, ext = f.split(".", 1)
            if ext == "py" and f not in ignore_py_files:
                yield os.path.join(root, f)
            if ext == "pxd":
                py_file = os.path.join(root, base) + ".py"
                if os.path.isfile(py_file):
                    if os.path.getmtime(os.path.join(root, f)) > os.path.getmtime(py_file):
                        os.utime(py_file)


setup(
    cmdclass={
        "build_ext": BuildExt,
    },
    ext_modules=[Extension("", [""])],  # Added to trigger a binary wheel
)
