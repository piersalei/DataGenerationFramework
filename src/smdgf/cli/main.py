"""CLI entrypoint for smdgf."""

import typer

from smdgf.cli import contracts, sampling


app = typer.Typer(no_args_is_help=True)
app.add_typer(contracts.app, name="contracts")
app.add_typer(sampling.app, name="sampling")
