esm_version_checker
===================

Mini package to check versions of diverse esm_tools software

Usage
-----

Provides two commands::

        $ esm_versions check
        You are using the following esm_tools versions:
        -----------------------------------------------
        esm_archiving : unknown version!
        esm_autotests : unknown version!
        esm_calendar : 3.0.0
        esm_database : unknown version!
        esm_environment : 3.0.0
        esm_master : 3.1.3
        esm_parser : 3.0.0
        esm_profile : 3.0.0
        esm_rcfile : 3.0.0
        esm_runscripts : 3.1.2
        esm_tools : 3.1.4
        esm_version_checker : 3.0.1 
        
        $ esm_versions upgrade [package]
        # If specified, updates just one package. Otherwise, updates all
        # packages that it can import from the esm_project.


Installation
------------

Automatically installed when you install the top level esm_tools package. Otherwise; use::

        pip install git+https://gitlab.awi.de/esm_tools/esm_version_checker


Authors
-------

`esm_version_checker` was written by `Paul Gierz <pgierz@awi.de>`_.
