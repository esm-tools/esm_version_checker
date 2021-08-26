# -*- coding: utf-8 -*-

"""Console script for esm_version_checker."""
import getpass
import importlib
import os
import pathlib
import re
import site
import subprocess
import sys
import shutil
import time
from packaging.version import parse as version_parse

from git import Repo
from git.exc import GitCommandError
from github import Github, GithubException
import click
import esm_rcfile
from tabulate import tabulate
import requests
import colorama
from colorama import Fore, Style
from bs4 import BeautifulSoup


class GlobalVars:
    """A struct-like class for holding the global variables. GlobalVars 
    instance should only be updated by the main function and should be 
    'read-only' by the other functions
    
    Attributes
    ----------
    from_github : bool
        top-level command-line option flag for connecting to the GitHub repo
    esm_tools_github_url : str
        repository URL of the ESM-Tools
    esm_tools_installed : dict
        each key is the specidif ESM-Tools package and value is bool
    """
    from_github = False  
    esm_tools_github_url = "https://github.com/esm-tools/"
    esm_tools_installed = {}
    
    # All tools and binaries are hard-coded here to avoid problems arising from
    # using globbing and matching (eg. esm-*)
    # NOTE: not all of these tools might be installed in the users setup. This
    # will be checked later on
    ESM_TOOLS_MODULES = [
        "esm_archiving",
        "esm_calendar",
        "esm_cleanup",
        "esm_database",
        "esm_environment",
        "esm_master",
        "esm_motd",
        "esm_parser",
        "esm_plugin_manager",
        "esm_profile",
        "esm_rcfile",
        "esm_runscripts",
        "esm_tools",
        "esm_utilities",
        "esm_version_checker"
    ]
    
    ESM_TOOLS_BINARIES = [
        "esm_database", 
        "esm_master",
        "esm_runscripts",
        "esm_versions"
    ] 


global_vars = GlobalVars()

# this option will be provided to the main command (eg. esm_versions) and will
# get passed to all subcommands (eg. check, clean, ...)
_global_options_list = [click.option("--from_github", is_flag=True, help=" will retrieve information from GitHub. Default behavior is offline (local) data retrieval")]

def global_options_decorator(func):
    """decorator function for the global option"""
    for option in reversed(_global_options_list):
        func = option(func)
    return func


@click.group()
@global_options_decorator
def main(**kwargs):
    """Console script for esm_versions."""
    # help_message = "Please use the subcommands check or update"
    # click.echo(help_message)

    # if esm_versions --from_github is provided then turn on the global 
    # from_github flag
    global global_vars
    
    # turn on the from_github flag in the global settings
    if kwargs["from_github"] == True:
       global_vars.from_github = True 
       
    # initialize the list of install packages as false
    esm_tools_modules =  get_esm_packages()
    global_vars.esm_tools_installed = {tool: False for tool in esm_tools_modules}
    
    return 0



def get_esm_packages():
    """Gets the list of the installed ESM-Tools packages either locally or from 
    the GitHub repository
    
    Returns
    -------
    esm_tools_modules : list
        list of strings where each item corresponds to a ESM-Tools package name
    """
    global global_vars

    # simple static variable trick to print GitHub connection message only once
    if not hasattr(get_esm_packages, "only_once"):
        get_esm_packages.only_once = True
    
    # if --from_github is provided in the call to esm_versions
    # connect to GitHub and get the list of modules from there. This can 
    # sometimes be problematic since sometimes GitHub may refuse the
    # connection request:
    # https://docs.github.com/en/enterprise-server@2.19/rest/overview/resources-in-the-rest-api#rate-limiting
    if global_vars.from_github == True:
        g = Github()
        try:
            if get_esm_packages.only_once:
                print("Connecting to GitHub")
                get_esm_packages.only_once = False  # turn off the static flag
            repos = g.get_organization("esm-tools").get_repos()
            esm_tools_modules = [repo.full_name.replace("esm-tools/", "") for repo in repos]
        except: 
            print ("ERROR: No repos found or request to GitHub got rejected.")
            sys.exit(1)

    # or use the hard coded ones given in the beginning
    else:
        esm_tools_modules = global_vars.ESM_TOOLS_MODULES
            
    # retrieve the package list from the locally installed modules
    # else:
        # installed_packages = list(pkg_resources.working_set)
        # esm_tools_modules = [lib.key for lib in installed_packages if lib.key.startswith('esm-')]
        # project names have hyphen but the module names have underscore
        # esm_tools_modules = [mod.replace('-', '_') for mod in esm_tools_modules]

    # esm_tools_modules.sort()


    return esm_tools_modules



def get_esm_package_attributes(tool):
    """Gets the attributes of the ESM-Tools package
    
    Parameters
    ----------
    tool : str
        name of the ESM-Tools package
   
    Returns
    -------
    attr_dict : dict
        dictionary of attributes. 
    """

    home_dir = os.path.expanduser('~')
    home_dir = os.path.realpath(home_dir)
# 
    # initialize the package table information
    version = ""
    file_path = ""
    branch = ""
    describe = ""
    latest_version = ""
    upgrade_required = False
    import_passed = False
    
    # try to get the package information
    try: 
        tool_module = importlib.import_module(tool)
        import_passed = True
    except ModuleNotFoundError: 
        tool_module = None
        # print(f"ERROR: {tool} can not be imported. Exiting")
        # sys.exit(1)

    if import_passed:
        # importlib will read the version information from __init__.py
        # source: https://packaging.python.org/guides/single-sourcing-package-version/
        # version imported from pkg_resources does NOT read the correct version.
        # __init__.py and setup.py are always updated by bumpversion and store 
        # the correct version number
        version = getattr(tool_module, "__version__", None)
        
        # __path__ holds the directory that hosts __init__.py
        file_path = os.path.realpath(tool_module.__path__[0])
        file_path = file_path.split(os.path.sep)[:-1]
        file_path = os.path.sep.join(file_path) + os.path.sep
        if home_dir in file_path:
            file_path = file_path.replace(home_dir, "${HOME}")

        # message = f"{tool} : unknown version!"
        if dist_is_editable(tool):
            repo_path = editable_dist_location(tool)
            repo = Repo(repo_path)
            try:
                # describe = repo.git.describe(tags=True, dirty=True)
                describe = repo.head.object.hexsha[:6]
                if repo.untracked_files or repo.is_dirty():
                    describe = f"{describe} (uncommitted changes)"
            except GitCommandError:
                describe = "Error"
                
            if not repo.head.is_detached:
                branch = repo.active_branch.name
            else:
                sha = repo.head.commit.name_rev[:7]
                branch = f"DETACHED at {sha}"
            # message += f" (development install, on branch: {repo.active_branch.name}, describe={describe})"
            
            # Returns eg. 5.1.7 if succesful or None
            latest_version = get_latest_version(tool)
            
            upgrade_required = version_parse(version) < version_parse(latest_version)
            
        attr_dict = {
            'version' : version,
            'file_path' : file_path,
            'branch' : branch,
            'describe' : describe,
            'latest_version' : latest_version,
            'upgrade_required' : upgrade_required,
            'importable' : True
        }

    # import failed for some reason
    else:
        attr_dict = {
            'version' : "Not installed",
            'file_path' : None,
            'branch' : None,
            'describe' : None, 
            'latest_version' : None,
            'upgrade_required' : False,
            'importable' : False
        }

    return attr_dict


def user_owns(binary):
    """True or False if user owns binary"""
    owner = pathlib.Path(binary).owner()
    return owner == getpass.getuser()



@main.command()
@global_options_decorator
def clean(**kwargs):
    """Removes (with force) the whole ESM-Tools system."""
    print("You're pushing the red button. Duck and cover!")
    print("----------------------------------------------")

    esm_tools_modules = get_esm_packages()
    remove_list = []
    for package in os.listdir(site.getusersitepackages()):
        for tool_name in esm_tools_modules:
            if tool_name in package or tool_name.replace("_", "-") in package:
                remove_list.append(os.path.join(site.getusersitepackages(), package))
    print("Will remove the following")
    print("  Python packages:")
    for package in remove_list:
        print(f"    {package}")
    print("  Binary programs:")
    for path_part in os.environ.get("PATH").split(":"):
        if os.path.exists(path_part):
            for binary in os.listdir(path_part):
                binary_path = os.path.join(path_part, binary)
                if binary.startswith("esm_") and user_owns(binary_path):
                    remove_list.append(binary_path)
                    print(f"    {binary_path}")
    if click.confirm("Do you want to continue?"):
        for esm_thing in remove_list:
            print(f"* Removing {esm_thing}")
            subprocess.run(["rm", "-rf", esm_thing])



@main.command()
@global_options_decorator
@click.option("--package", "package", default=None, help="get information about this package only")
@click.option("--no-color", is_flag=True, help="use default console colors, rather than red, green, yellow")
def check(**kwargs):
    """Prints the ESM-Tools package information.
    
    Either the specified package (--package <package>) or all available packages installed
    in the system are retrieved. 
    
    When --from_github option is provided to esm_versions (esm_versions --from_github check ...)
    it will get the package list from GitHub (online), otherwise it will be done locally (offline)
    
    Results will be printed as a table or line-by-line if the terminal width is small 
    """
    colorama.init(autoreset=True)
    
    # 2D list that contains the information table
    headers = ['package_name', 'version', 'file', 'branch', 'commit ID']
    table = []   

    esm_tools_modules = get_esm_packages()    

    # --package is passed on the command-line, we are dealing with a single package
    if kwargs["package"] is not None:
        package = kwargs["package"]
        if package not in esm_tools_modules:
            print(f"ERROR: {package} is not found in the installed packages")
            sys.exit(1)
        else:
            esm_tools_modules = [package]

    attr_dict_all = {}  # attributes for all tools
    extra_messages = []

    for index, tool in enumerate(esm_tools_modules, start=1):
        # mini progress bar
        msg = f"::: Obtaining information for the tool: {tool:<20} [{index}/{len(esm_tools_modules)}]"
        sys.stdout.write(msg)
        sys.stdout.flush()

        # get the package attributes
        attr_dict = get_esm_package_attributes(tool)
        attr_dict_all[tool] = attr_dict

        attr_dict_all[tool]['tool'] = tool
        attr_dict_all[tool]['tool_print'] = tool

        # _print variables have color formatting and they will get printed
        tool_print     = tool
        version        = version_print        = attr_dict['version']
        file_path      = file_path_print      = attr_dict['file_path']
        branch         = branch_print         = attr_dict['branch']
        describe       = describe_print       = attr_dict['describe']
        latest_version = latest_version_print = attr_dict['latest_version']
        upgrade_required = upgrade_required_print = attr_dict['upgrade_required']
        importable       = importable_print   = attr_dict["importable"]

        # color code:
        # - GREEN: the tools is up to date
        # - YELLOW: upgrade required
        # - RED: tool is not installed or not importable
        upgrade_color = Fore.YELLOW if upgrade_required else Fore.GREEN
        not_available_color = Fore.RED
        
        # if --no-color is provided then cancel the color formatting. This can
        # be useful for the color blind people.
        if kwargs["no_color"]:
            upgrade_color = not_available_color = colorama.Style.RESET_ALL

        # mark the tag if the repository has uncommitted changes. Eg. it is 
        # a dirty repo
        if describe_print is not None and "uncommitted" in describe:
            if not kwargs["no_color"]:
                describe = f"{colorama.Back.RED}{colorama.Fore.WHITE}{describe}"

        tool_print      = f"{upgrade_color}{tool}{Style.RESET_ALL}"
        version_print   = f"{upgrade_color}{version}{Style.RESET_ALL}"
        if upgrade_required:
            version_print += f"{upgrade_color} (Latest: {latest_version}){Style.RESET_ALL}"
        file_path_print = f"{upgrade_color}{file_path}{Style.RESET_ALL}"
        branch_print    = f"{upgrade_color}{branch}{Style.RESET_ALL}"
        describe_print  = f"{upgrade_color}{describe}{Style.RESET_ALL}"

        if not importable:
            tool_print      = f"{not_available_color}{tool}{Style.RESET_ALL}"
            version_print   = f"{not_available_color}{version}{Style.RESET_ALL}"
            file_path_print = f"{not_available_color}{file_path}{Style.RESET_ALL}"
            branch_print    = f"{not_available_color}{branch}{Style.RESET_ALL}"
            describe_print  = f"{not_available_color}{describe}{Style.RESET_ALL}"

        if upgrade_required:
            extra_messages.append(
                f"- upgrade required for {tool}. Use: "\
                f"{upgrade_color}esm_versions upgrade {tool}{Style.RESET_ALL}")

        # also set these for the all single package prints
        attr_dict_all[tool]['tool_print'] = tool_print
        attr_dict_all[tool]['version_print'] = version_print
        attr_dict_all[tool]['file_path_print'] = file_path_print
        attr_dict_all[tool]['branch_print'] = branch_print
        attr_dict_all[tool]['describe_print'] = describe_print

        # construct the table for tabular output
        table.append([tool_print, version_print, file_path_print, 
            branch_print, describe_print])

        # pause for a little to show the beautiful progress bar
        time.sleep(0.5)  
        clear_line(len(msg))

    # ===
    # print the results
    # ===
    terminal_width = shutil.get_terminal_size().columns

    # if only a single package is selected then print without a table
    if kwargs["package"] is not None:
        report_single_package(tool, version, file_path, branch, describe)

    # we are on a small terminal. Thus report package by package
    elif terminal_width < 150:
        for tool in esm_tools_modules:
            # report_single_package(tool, version, file_path, branch, describe)
            report_single_package(attr_dict_all[tool]['tool_print'],
                attr_dict_all[tool]['version_print'], 
                attr_dict_all[tool]['file_path_print'], 
                attr_dict_all[tool]['branch_print'], 
                attr_dict_all[tool]['describe_print'])
            print()

    # print the full table 
    else: 
        print(tabulate(table, headers, tablefmt='psql')) 

    # Print the extra messages such as upgrades 
    for line in extra_messages:
        print(line)


# PG: Blatant theft:
# https://stackoverflow.com/questions/42582801/check-whether-a-python-package-has-been-installed-in-editable-egg-link-mode
def dist_is_editable(dist):
    """Is distribution an editable install?"""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.replace("_", "-") + ".egg-link")
        if os.path.isfile(egg_link):
            return True
    return False


def editable_dist_location(dist):
    """Determines where an editable dist is installed"""
    for path_item in sys.path:
        egg_link = os.path.join(path_item, dist.replace("_", "-") + ".egg-link")
        if os.path.isfile(egg_link):
            return open(egg_link).readlines()[0].strip()
    return None


def pip_install(package):
    url = global_vars.esm_tools_github_url
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            f"git+{url}" + package,
        ]
    )


def pip_uninstall(package):
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", package])


def pip_upgrade(package, version=None):
    url = global_vars.esm_tools_github_url

    if not dist_is_editable(package):
        package_name = package
        if version is not None:
            package = package + "@" + version
        try:
            # --user causes an error in a venv (which is used e.g. in CI)
            # explanation: https://github.com/pypa/pip/issues/4141
            if bool(os.environ.get("VIRTUAL_ENV")):
                subprocess.check_call(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "--upgrade",
                        f"git+{url}" + package,
                    ]
                )
            else:
                subprocess.check_call(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "--user",
                        "--upgrade",
                        f"git+{url}" + package,
                    ]
                )
        except subprocess.CalledProcessError:
            print("Installation failed. Possible reasons are:")
            print("- You tried to pull a branch that does not exist")
            print(
                f"  A list of vaild branches is available at {url}"
                + package_name
                + "/branches"
            )
            print("- You provided an invalid version number.")
            print(
                f"  A list of valid version numbers is available at {url}"
                + package_name
                + "/releases"
            )

    else:
        print(
            "  WARNING:", package,
            "is installed in editable mode! No upgrade performed. You may consider doing a git pull here:",
        )
        package = importlib.import_module(package)
        print("/".join(package.__file__.split("/")[:-2]))


def pip_or_pull(tool, version=None):
    if tool == "esm_tools":
        print("esm_versions automatically does git operations for %s" % tool)
        # deniz: FUNCTION_PATH is obsolete. The solution below is more portable
        # FUNCTION_PATH = esm_rcfile.get_rc_entry("FUNCTION_PATH")
        # esm_tools_dir = os.path.dirname(FUNCTION_PATH)
        
        # esm_tools_dir will be something like /myhomedir/esm_packages/esm_tools
        attr_dict = get_esm_package_attributes("esm_tools")
        esm_tools_dir = attr_dict["file_path"]
        esm_tools_repo = Repo(esm_tools_dir)
        try:
            assert not esm_tools_repo.is_dirty()
        except AssertionError:
            print("WARNING: Your esm_tools directory" + esm_tools_dir + "is not clean and cannot be updated!")
            print(
                "WARNING: Please make sure you check in and commit everything before proceeding!"
            )
        try:
            assert esm_tools_repo.active_branch.name in ["release", "develop"]
            remote = esm_tools_repo.remote()
            remote.pull()
            print("Pulled new version of ", tool)
        except AssertionError:
            print("WARNING: Only allowed to pull on release or develop!")
            print("WARNING: You are on a branch: %s" % esm_tools_repo.active_branch.name)
            print("WARNING: Please pull or change branches by yourself!")

    else:
        pip_upgrade(tool, version)


def check_importable_tools():
    global global_vars
    esm_tools_modules = get_esm_packages()
    
    # check each tool and turn on the global setting if the module is installed
    for tool in esm_tools_modules:
        try:
            importlib.import_module(tool)
            import_successful = True
            global_vars.esm_tools_installed[tool] = True
        except ImportError:
            import_successful = False


@main.command()
@click.argument("tool_to_upgrade", default="all")
def upgrade(tool_to_upgrade="all"):
    """Upgrades the whole ESM-Tools system or only the selected package.

    Arguments
    ---------
    tool_to_upgrade : str
        ESM-Tools package to upgrade. Default is 'all' which upgrades all packages
    """
    global global_vars
    esm_tools_modules = get_esm_packages()
    
    if tool_to_upgrade == "esm_versions":
        tool_to_upgrade = "esm_version_checker"

    # check all modules and modify the global 'esm_tools_installed' flag
    check_importable_tools()
    
    if tool_to_upgrade == "all":
        for tool in esm_tools_modules:
            if global_vars.esm_tools_installed[tool]:
                print(f"\033[91mupgrading the tool: {tool}\033[0m")
                pip_or_pull(tool)
                print()
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

        if global_vars.esm_tools_installed[tool_to_upgrade]:
            pip_or_pull(tool_to_upgrade, version)


# PG: People never know what word to use. So, we allow both...
@main.command()
@click.argument("tool_to_upgrade", default="all")
def update(tool_to_upgrade="all"):
    """Like upgrate"""
    upgrade(tool_to_upgrade)


@main.command()
@global_options_decorator
@click.argument("package", nargs=1, type=str)
@click.argument("attribute", nargs=1, type=str, default="all")
def get(package, attribute="all", **kwargs):
    """Prints an attribute of a package.
    
    Arguments
    ---------
    package : str
        ESM-Tools package
    attribute : str
        One of the following: version, file_path, branch, describe
    """
    esm_tools_modules = get_esm_packages()
    
    # error checks
    if package not in esm_tools_modules:
        print(f"ERROR: {package} is not found in the installed packages")
        sys.exit(1)
    
    attr_dict = get_esm_package_attributes(package)
    # error check
    if attribute != "all":
        attributes = ["version", "file_path", "branch", "describe"]
        if attribute not in attributes:
            print(f"ERROR: {attribute} is not a valid attribute. List of valid package attributes:")
            for attribute in attributes:
                print("  " + attribute)
            sys.exit(1)
        # get the package attributes
        print(attr_dict[attribute])
    else:
        print(package)
        print("-"*len(package))
        print(f"Version:\t {attr_dict['version']}")
        print(f"File Path:\t {attr_dict['file_path']}")
        print(f"Branch:\t\t {attr_dict['branch']}")
        print(f"Git Describe:\t {attr_dict['describe']}")


def report_single_package(package, version, file_path, branch, describe):
    """Nice output similar to the tree command in Linux"""
    tee = u"\u251C"
    hline = u"\u2500"
    elbow = u"\u2514"
    print(package)
    print(tee + hline + f" version: {version}")
    print(tee + hline + f" path: {file_path}")
    print(tee + hline + f" branch: {branch}")
    print(elbow + hline + f" commit ID: {describe}")


def clear_line(nchars):    
    """Clears the printed characters on the current line"""
    line_eraser = '\b' * nchars   # go back nchars
    line_eraser += ' ' * nchars   # overwrite with whitespace
    line_eraser += '\b' * nchars  # go back again
    sys.stdout.write(line_eraser)
    sys.stdout.flush()


def get_latest_version(tool):
    """uses web scraping to retrieve the latest version of the tool. `tool`
    is the selected ESM-Tools string (eg. esm_master). Returns the version if
    http request returns succesful and regex is matched. If not None is 
    returned.
    """
    url = f"https://github.com/esm-tools/{tool}/tags"
    
    try: 
        page = requests.get(url)
    except requests.exceptions.RequestException:
        print(f"Warning: unable to retrieve the latest version information for {tool}")
        sys.exit()

        version = None
        return version

    soup = BeautifulSoup(page.content, 'html.parser')
    
    # get the first h4
    # repo_content = soup.find("div", id="repo-content-pjax-container")
    repo_content = soup.find("div", {"class": "commit js-details-container Details"})
    h4 = repo_content.find_all('h4')[0]
    latest_tag_link = h4.find("a", href=re.compile(".*/releases/tag/.*"))
    # check if the correct version can be found
    if latest_tag_link is None:
        print(f"WARNING: esm_versions can't read the version from {url}")
        version = None
        return None

    version = latest_tag_link.text.strip()
    if version.startswith('v'):
        version = version[1:]

    return version


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
