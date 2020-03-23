# -*- coding: utf-8 -*-

"""Console script for esm_version_checker."""
import importlib
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
        except ImportError:
            import_successful = False
            print(tool, "could not be imported!")
        if import_successful:
            try:
                print(tool, ":", tool_mod.__version__)
            except AttributeError:
                print("Oops! %s has no version??" % tool)



if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
