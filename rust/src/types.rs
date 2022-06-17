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
use pyo3::types::PyTuple;
use pyo3::{Py, PyAny, PyErr, PyObject, PyResult, Python};

use crate::{BasicContext, Client};

pyo3::import_exception!(alluka._errors, MissingDependencyError);

pub type InjectedTuple = (String, Injected);

pub struct InjectedCallback {
    callback: PyObject,
}

impl InjectedCallback {
    pub fn resolve(&self, py: Python, client: &mut Client, ctx: Py<BasicContext>) -> PyResult<PyObject> {
        unimplemented!("Custom contexts are not yet supported")
    }

    pub fn resolve_rust(&self, py: Python, client: &mut Client, ctx: Py<BasicContext>) -> PyResult<PyObject> {
        let callback = client
            .get_callback_override(py, self.callback.as_ref(py))?
            .unwrap_or_else(|| self.callback.clone_ref(py));
        client.call_with_ctx_rust(py, ctx, callback, PyTuple::empty(py), None)
    }

    pub fn resolve_async(&self, py: Python, client: &mut Client, ctx: PyObject) -> PyResult<PyObject> {
        unimplemented!("Custom contexts are not yet supported")
    }

    pub fn resolve_rust_async(&self, py: Python, client: &mut Client, ctx: Py<BasicContext>) -> PyResult<PyObject> {
        let callback = client
            .get_callback_override(py, self.callback.as_ref(py))?
            .unwrap_or_else(|| self.callback.clone_ref(py));
        client.call_with_ctx_async_rust(py, ctx, callback, PyTuple::empty(py), None)
    }
}


pub struct InjectedType {
    default: Option<PyObject>,
    repr_type: String,
    types: Vec<PyObject>,
    type_ids: Vec<isize>,
}

impl InjectedType {
    pub fn resolve(&self, py: Python, ctx: &PyObject) -> PyResult<PyObject> {
        unimplemented!("Custom contexts are not yet supported")
    }

    pub fn resolve_rust(&self, py: Python, ctx: Py<BasicContext>) -> PyResult<PyObject> {
        if let Some(value) = self
            .type_ids
            .iter()
            .filter_map(|cls| {
                ctx.borrow(py)
                    .get_type_dependency_rust(cls)
                    .map(|value| value.clone_ref(py))
            })
            .next()
        {
            return Ok(value);
        }

        if let Some(default) = &self.default {
            return Ok(default.clone_ref(py));
        }

        return Err(PyErr::new::<MissingDependencyError, _>(format!(
            "Couldn't resolve injected type(s) {} to actual value",
            self.repr_type
        )));
    }
}


pub enum Injected {
    Callback(InjectedCallback),
    Type(InjectedType),
}

impl Injected {
    pub fn new_callback(callback: PyObject) -> Self {
        Injected::Callback(InjectedCallback { callback })
    }

    pub fn new_type(
        py: Python,
        default: Option<PyObject>,
        repr_type: PyObject,
        types: Vec<PyObject>,
    ) -> PyResult<Self> {
        Ok(Injected::Type(InjectedType {
            default,
            repr_type: repr_type.as_ref(py).repr()?.to_string(),
            type_ids: types
                .iter()
                .map(|type_| type_.as_ref(py).hash())
                .collect::<PyResult<Vec<isize>>>()?,
            types,
        }))
    }
}