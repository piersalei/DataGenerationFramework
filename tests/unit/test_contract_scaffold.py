import importlib


def test_package_imports() -> None:
    smdgf = importlib.import_module("smdgf")
    assert smdgf.__version__ == "0.1.0"


def test_cli_entrypoint_module_exists() -> None:
    cli_main = importlib.import_module("smdgf.cli.main")
    assert hasattr(cli_main, "app")
