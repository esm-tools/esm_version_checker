# -*- coding: utf-8 -*-

"""Console script for esm_version_checker."""
import importlib
import os
import pkg_resources
import subprocess
import sys

import click

esm_tools_modules = [
        "esm_archiving",
        "esm_autotests",
        "esm_calendar",
        "esm_database",
        "esm_environment",
        "esm_master",
        "esm_parser",
        "esm_profile",
        "esm_rcfile",
        "esm_runscripts",
        "esm_tools",
        "esm_version_checker",
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
        except ImportError as e:
            import_successful = False
        if import_successful:
            try:
                print(tool, ":", tool_mod.__version__)
            except AttributeError:
                try:
                    print(tool, ":", pkg_resources.get_distribution(tool).version)
                except:
                    #print("Oops! %s has no version??" % tool)
                    raise
        else:
            print(tool, ": unknown version!")


# PG: Blatant theft:
# https://stackoverflow.com/questions/42582801/check-whether-a-python-package-has-been-installed-in-editable-egg-link-mode
def dist_is_editable(dist):
    """Is distribution an editable install?"""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.replace("_", "-") + '.egg-link')
        if os.path.isfile(egg_link):
            return True
    return False

def pip_install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", "git+https://gitlab.awi.de/esm_tools/"+package])

def pip_uninstall(package):
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", package])

def pip_upgrade(package):
    if not dist_is_editable(package):
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "git+https://gitlab.awi.de/esm_tools/"+package])
    else:
        print(package, "is installed in editable mode! No upgrade performed. You may consider doing a git pull...")



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
        if esm_tools_installed[tool_to_upgrade]:
            pip_upgrade(tool_to_upgrade)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
