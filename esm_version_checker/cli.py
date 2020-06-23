# -*- coding: utf-8 -*-

"""Console script for esm_version_checker."""
import importlib
import os
import pkg_resources
import subprocess
import sys
import re

from git import Repo
import click
import esm_rcfile

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
    "esm_plugin_manager",
    "esm_version_checker",
]

esm_tools_installed = {tool: False for tool in esm_tools_modules}


@click.group()
def main(args=None):
    """Console script for esm_archiving."""
    # help_message = "Please use the subcommands check or update"
    # click.echo(help_message)
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
        if import_successful:
            try:
                print(tool, ":", tool_mod.__version__)
            except AttributeError:
                try:
                    print(tool, ":", pkg_resources.get_distribution(tool).version)
                except:
                    # print("Oops! %s has no version??" % tool)
                    raise
        else:
            print(tool, ": unknown version!")


# PG: Blatant theft:
# https://stackoverflow.com/questions/42582801/check-whether-a-python-package-has-been-installed-in-editable-egg-link-mode
def dist_is_editable(dist):
    """Is distribution an editable install?"""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.replace("_", "-") + ".egg-link")
        if os.path.isfile(egg_link):
            return True
    return False


def pip_install(package):
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "git+https://github.com/esm-tools/" + package,
        ]
    )


def pip_uninstall(package):
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", package])


def pip_upgrade(package, version=None):
    if not dist_is_editable(package):

        package_name = package
        if version is not None:
            package = package + "@" + version
        try:
            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "git+https://github.com/esm-tools/" + package,
                ]
            )
        except subprocess.CalledProcessError:
            print("Installation failed. ")
            print("One reason might be that you provided an invalid version number.")
            print(
                "A list of vaild version numbers is available at https://github.com/esm-tools/"
                + package_name
                + "/releases"
            )

    else:
        print(
            package,
            "is installed in editable mode! No upgrade performed. You may consider doing a git pull here:",
        )
        package = importlib.import_module(package)
        print("/".join(package.__file__.split("/")[:-2]))


def pip_or_pull(tool, version=None):
    if tool == "esm_tools":
        print("esm_versions automatically does git operations for %s" % tool)
        FUNCTION_PATH = esm_rcfile.get_rc_entry("FUNCTION_PATH")
        esm_tools_dir = os.path.dirname(FUNCTION_PATH)
        esm_tools_repo = Repo(esm_tools_dir)
        try:
            assert not esm_tools_repo.is_dirty()
        except AssertionError:
            print("Your esm_tools directory is not clean!")
            print(
                "Please make sure you check in and commit everything before proceeding!"
            )
            raise
        try:
            assert esm_tools_repo.active_branch.name in ["release", "develop"]
            remote = esm_tools_repo.remote()
            remote.pull()
            print("Pulled new version of ", tool)
        except AssertionError:
            print("Only allowed to pull on release or develop!")
            print("You are on a branch: %s" % esm_tools_repo.active_branch.name)
            print("Please pull or change branches by yourself!")
            raise
    else:
        pip_upgrade(tool, version)


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
    if tool_to_upgrade == "esm_versions":
        tool_to_upgrade = "esm_version_checker"
    check_importable_tools()
    if tool_to_upgrade == "all":
        for tool in esm_tools_modules:
            if esm_tools_installed[tool]:
                pip_or_pull(tool)
    else:
        # allow the syntax esm_versions updgrade <name_of_tool>=vX.Y.Z or <name_of_tool>==vX.Y.Z
        # to install a specific version of a tool, default is None which means that the latest version
        # will be installed
        version = None
        if "=" in tool_to_upgrade:
            if "==" in tool_to_upgrade:
                tool_to_upgrade, version = tool_to_upgrade.split("==")
            else:
                tool_to_upgrade, version = tool_to_upgrade.split("=")
            # regex to catch version numbers with format vX.Y.Z e.g. v4.10.2
            if not re.match(r"v(?:(\d+\.(?:\d+\.)*\d+))", version):
                print("Ignoring invalid version number ", version)
                version = None

        if esm_tools_installed[tool_to_upgrade]:
            pip_or_pull(tool_to_upgrade, version)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
