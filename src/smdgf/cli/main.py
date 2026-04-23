"""CLI entrypoint for smdgf."""

import typer

from smdgf.cli import contracts, sampling, yaml_prompt
from smdgf.generation.cli import generate_cmd


app = typer.Typer(no_args_is_help=True)
app.add_typer(contracts.app, name="contracts")
app.add_typer(sampling.app, name="sampling")
app.add_typer(yaml_prompt.app, name="yaml")
app.command("generate")(generate_cmd)
