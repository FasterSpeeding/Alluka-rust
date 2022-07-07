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

import pathlib
import shutil
import tempfile

import nox

nox.options.sessions = ["test"]  # type: ignore


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


@nox.session(name="upgrade-dev-deps", reuse_venv=True)
def upgrade_dev_deps(session: nox.Session) -> None:
    """Upgrade the dev dependencies."""
    session.install("--upgrade", "-r", "dev-requirements.txt")
    session.run(
        "pip-compile",
        ".\dev-requirements.in",
        "--output-file",
        "dev-requirements.txt",
        "--upgrade",
    )


@nox.session(reuse_venv=True)
def test(session: nox.Session) -> None:
    """Run this project's tests using pytest."""
    with tempfile.TemporaryDirectory() as directory:
        target = pathlib.Path(directory) / "alluka"
        session.run(
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            "v0.1.2",
            "https://github.com/FasterSpeeding/Alluka.git",
            str(target),
            external=True,
        )
        install_requirements(
            session,
            "-r",
            "./dev-requirements.txt",
            "-r",
            str(target / "dev-requirements/tests.txt"),
        )
        shutil.copyfile("./conftest.py", str(target / "conftest.py"))
        session.run("maturin", "develop")
        session.run(
            "pytest",
            str(target / "tests"),
            "-n",
            "auto",
            "--import-mode",
            "importlib",
        )
