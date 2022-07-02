# Alluka

A performant Rust implementation of Alluka DI.

# Usage

For more information on how to use Alluka as a whole see `https://alluka.cursed.solutions/usage/`
as this followed the same interface (`alluka_rust.Client` and `alluka_rust.BasicContext`
can be used like `alluka.Client` and `alluka.BasicContext`)

If you want to patch the default Alluka implementation with this you can simply
set the `ALLUKA_RUST_PATCH` env variable before importing alluka_rust or call
`alluka_rust.patch_alluka` before starting anything which uses Alluka.

# Limitations

While this is a full Alluka implementation, it should be noted that (unlike
the pure Python implementation) this implementation only works with context
implementations which directly inherit from `alluka_rust.BasicContext` and won't
use any overloaded behaviour for most of the python methods during the DI process.
