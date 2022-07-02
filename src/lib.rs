// BSD 3-Clause License
//
// Copyright (c) 2022, Lucina
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
// * Redistributions of source code must retain the above copyright notice, this
//   list of conditions and the following disclaimer.
//
// * Redistributions in binary form must reproduce the above copyright notice,
//   this list of conditions and the following disclaimer in the documentation
//   and/or other materials provided with the distribution.
//
// * Neither the name of the copyright holder nor the names of its contributors
//   may be used to endorse or promote products derived from this software
//   without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
#![allow(clippy::borrow_deref_ref)] // Leads to a ton of false positives around args of py types.
#![feature(arbitrary_self_types)]
#![feature(hash_raw_entry)]
#![feature(once_cell)]
use client::{BasicContext, Client};
use pyo3::types::{PyModule, PyType};
use pyo3::{wrap_pyfunction, PyResult, Python};

mod client;
mod types;
mod visitor;

const PATCH_ENV_VAR: &str = "ALLUKA_RUST_PATCH";

#[pyo3::pyfunction]
#[pyo3(pass_module)]
fn patch_alluka(module: &PyModule, py: Python) -> PyResult<()> {
    let alluka = py.import("alluka")?;

    alluka.setattr("Client", module.getattr("Client")?)?;
    alluka.setattr("BasicContext", module.getattr("BasicContext")?)?;

    Ok(())
}


#[pyo3::pymodule]
fn alluka_rust(py: Python, module: &PyModule) -> PyResult<()> {
    let abc = py.import("alluka")?.getattr("abc")?;

    module.add("__author__", "Faster Speeding")?;
    module.add("__ci__", "https://github.com/FasterSpeeding/Alluka-rust/actions")?;
    module.add("__copyright__", "© 2022 Faster Speeding")?;
    module.add(
        "__coverage__",
        "https://codeclimate.com/github/FasterSpeeding/Alluka-rust",
    )?;
    module.add("__docs__", "https://alluka_rust.cursed.solutions/")?;
    module.add("__email__", "lucina@lmbyrne.dev")?;
    module.add(
        "__issue_tracker__",
        "https://github.com/FasterSpeeding/Alluka-rust/issues",
    )?;
    module.add("__license__", "BSD")?;
    module.add("__url__", "https://github.com/FasterSpeeding/Alluka-rust")?;
    module.add("__version__", "0.1.1")?;
    module.add_class::<Client>()?;
    module.add_class::<BasicContext>()?;
    module.add_function(wrap_pyfunction!(patch_alluka, module)?)?;

    abc.getattr("Client")?
        .call_method1("register", (PyType::new::<Client>(py),))?;

    abc.getattr("Context")?
        .call_method1("register", (PyType::new::<BasicContext>(py),))?;

    if std::env::var_os(PATCH_ENV_VAR).is_some()
        || !py.import("os")?.call_method1("getenv", (PATCH_ENV_VAR,))?.is_none()
    {
        patch_alluka(module, py)?;
    }

    Ok(())
}
