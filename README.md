<div align="center">
  <img src=docs/_static/mkwind.png width="500"><br>
</div>

# What is mkwind?

mkwind is an accompanying package to mkite for running tasks on client workers.
This package allows running simulations without installing all the database requirements, thus protecting the server from modifications on the client side.
mkwind offers a set of tools for building, running, and postprocessing the tasks, and sending them back to mkite through `mkite_engines`.

## Documentation

General tutorial for `mkite` and its plugins are available in the [main documentation](https://www.mkite.org).
Complete API documentation is pending.

## Installation

To install `mkwind`, install the main dependencies `mkite_core` and `mkite_engines`:

```bash
pip install mkite_core mkite_engines
pip install mkwind
```

Alternatively, for a development version, use:

```bash
pip install -U git+https://github.com/mkite-group/mkwind
```

## Contributions

Contributions to the entire mkite suite are welcomed.
You can send a pull request or open an issue for this plugin or either of the packages in mkite.
When doing so, please adhere to the [Code of Conduct](CODE_OF_CONDUCT.md) in the mkite suite.

The mkite package was created by Daniel Schwalbe-Koda <dskoda@llnl.gov>.

### Citing mkite

If you use mkite in a publication, please cite the following paper:

```bibtex
@article{mkite2023,
    title = {mkite: A distributed computing platform for high-throughput materials simulations},
    author = {Schwalbe-Koda, Daniel},
    year = {2023},
    journal = {arXiv:2301.08841},
    doi = {10.48550/arXiv.2301.08841},
    url = {https://doi.org/10.48550/arXiv.2301.08841},
    arxiv={2301.08841},
}
```

## License

The mkite suite is distributed under the following license: Apache 2.0 WITH LLVM exception.

All new contributions must be made under this license.

SPDX: Apache-2.0, LLVM-exception

LLNL-CODE-848161
