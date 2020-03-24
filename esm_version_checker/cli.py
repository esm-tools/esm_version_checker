# -*- coding: utf-8 -*-

"""Console script for esm_version_checker."""
import importlib
import pkg_resources
import subprocess
import sys

import click

esm_tools_modules = [
        "esm_archiving",
        "esm_autotests",
        "esm_calender",
        "esm_database",
        "esm_environment",
        "esm_master",
        "esm_parser",
        "esm_profile",
        "esm_rcfile",
        "esm_tools",
]

esm_tools_installed = {tool: False for tool in esm_tools_modules}

@click.group()
def main(args=None):
    """Console script for esm_archiving."""
    #help_message = "Please use the subcommands check or update"
    #click.echo(help_message)
    return 0

@main.command()
def check(args=None):
    print("You are using the following esm_tools versions:")
    print("-----------------------------------------------")
    for tool in esm_tools_modules:
        try:
            tool_mod = importlib.import_module(tool)
            import_successful = True
            esm_tools_installed[tool] = True
        except ImportError:
            import_successful = False
            print(tool, "could not be imported!")
        if import_successful:
            try:
                print(tool, ":")
                print("__version__ attribute:", tool_mod.__version__)
                print("pkg_version in setup.py:", pkg_resources.get_distribution(tool).version)
            except AttributeError:
                print("Oops! %s has no version??" % tool)
                raise
        print("\n")


def pip_install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "git+https://gitlab.awi.de/esm_tools/"+package])

def pip_uninstall(package):
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", package])

def pip_upgrade(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "git+https://gitlab.awi.de/esm_tools/"+package])

def check_importable_tools():
    for tool in esm_tools_modules:
        try:
            importlib.import_module(tool)
            import_successful = True
            esm_tools_installed[tool] = True
        except ImportError:
            import_successful = False

@main.command()
@click.argument("tool_to_upgrade", default="all")
def upgrade(tool_to_upgrade="all"):
    check_importable_tools()
    if tool_to_upgrade == "all":
        for tool in esm_tools_modules:
            if esm_tools_installed[tool]:
                pip_upgrade(tool)
    else:
        if esm_tools_installed[tool]:
            pip_upgrade(tool)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
