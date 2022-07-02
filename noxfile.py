# -*- coding: utf-8 -*-
# cython: language_level=3
# BSD 3-Clause License
#
# Copyright (c) 2020-2022, Faster Speeding
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
from __future__ import annotations

import itertools
import pathlib
import shutil
import tempfile
from collections import abc as collections

import nox

nox.options.sessions = ["spell-check", "test"]  # type: ignore
GENERAL_TARGETS = ["./noxfile.py", "./tests"]
_BLACKLISTED_TARGETS = {"_vendor", "__pycache__"}
for path in pathlib.Path("./alluka").glob("*"):
    if path.name not in _BLACKLISTED_TARGETS:
        GENERAL_TARGETS.append(str(path))


PYTHON_VERSIONS = ["3.9", "3.10"]  # TODO: @nox.session(python=["3.6", "3.7", "3.8"])?
_DEV_DEP_DIR = pathlib.Path("./dev-requirements")


def _dev_dep(*values: str) -> collections.Iterator[str]:
    return itertools.chain.from_iterable(
        ("-r", str(_DEV_DEP_DIR / f"{value}.txt")) for value in values
    )


def install_requirements(
    session: nox.Session, *other_requirements: str, first_call: bool = True
) -> None:
    # --no-install --no-venv leads to it trying to install in the global venv
    # as --no-install only skips "reused" venvs and global is not considered reused.
    if not _try_find_option(session, "--skip-install", when_empty="True"):
        if first_call:
            session.install("--upgrade", "wheel")

        session.install("--upgrade", *map(str, other_requirements))


def _try_find_option(
    session: nox.Session, name: str, *other_names: str, when_empty: str | None = None
) -> str | None:
    args_iter = iter(session.posargs)
    names = {name, *other_names}

    for arg in args_iter:
        if arg in names:
            return next(args_iter, when_empty)


@nox.session(venv_backend="none")
def cleanup(session: nox.Session) -> None:
    """Cleanup any temporary files made in this project by its nox tasks."""
    import shutil

    # Remove directories
    for raw_path in ["./site", "./.nox"]:
        path = pathlib.Path(raw_path)
        try:
            shutil.rmtree(str(path.absolute()))

        except Exception as exc:
            session.warn(f"[ FAIL ] Failed to remove '{raw_path}': {exc!s}")

        else:
            session.log(f"[  OK  ] Removed '{raw_path}'")

    # Remove individual files
    for raw_path in ["./.coverage", "./coverage_html.xml"]:
        path = pathlib.Path(raw_path)
        try:
            path.unlink()

        except Exception as exc:
            session.warn(f"[ FAIL ] Failed to remove '{raw_path}': {exc!s}")

        else:
            session.log(f"[  OK  ] Removed '{raw_path}'")


def _pip_compile(session: nox.Session, /, *args: str) -> None:
    install_requirements(session, *_dev_dep("publish"))
    for path in pathlib.Path("./dev-requirements/").glob("*.in"):
        session.run(
            "pip-compile",
            str(path),
            "--output-file",
            str(path.with_name(path.name.removesuffix(".in") + ".txt")),
            *args
            # "--generate-hashes",
        )


@nox.session(name="freeze-dev-deps", reuse_venv=True)
def freeze_dev_deps(session: nox.Session) -> None:
    """Freeze the dev dependencies."""
    _pip_compile(session)


@nox.session(name="upgrade-dev-deps", reuse_venv=True)
def upgrade_dev_deps(session: nox.Session) -> None:
    """Upgrade the dev dependencies."""
    _pip_compile(session, "--upgrade")


@nox.session(name="generate-docs", reuse_venv=True)
def generate_docs(session: nox.Session) -> None:
    """Generate docs for this project using Mkdoc."""
    install_requirements(session, *_dev_dep("docs"))
    output_directory = _try_find_option(session, "-o", "--output") or "./site"
    session.run("mkdocs", "build", "-d", output_directory)
    for path in ("./CHANGELOG.md", "./README.md"):
        shutil.copy(path, pathlib.Path(output_directory) / path)


@nox.session(reuse_venv=True, name="spell-check")
def spell_check(session: nox.Session) -> None:
    """Check this project's text-like files for common spelling mistakes."""
    install_requirements(
        session, *_dev_dep("lint")
    )  # include_standard_requirements=False
    session.run(
        "codespell",
        *GENERAL_TARGETS,
        ".gitignore",
        "LICENSE",
        "pyproject.toml",
        "CHANGELOG.md",
        "CODE_OF_CONDUCT.md",
        # "CONTRIBUTING.md",
        "README.md",
        "./github",
        ".pre-commit-config.yaml",
        "./docs",
    )


@nox.session(reuse_venv=True)
def test(session: nox.Session) -> None:
    """Run this project's tests using pytest."""
    install_requirements(
        session, ".", "--use-feature=in-tree-build", *_dev_dep("tests")
    )
    # TODO: can import-mode be specified in the config.
    session.run("pytest", "-n", "auto", "--import-mode", "importlib")
