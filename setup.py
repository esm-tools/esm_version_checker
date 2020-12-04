import io
import os
import re

from setuptools import find_packages
from setuptools import setup


def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type(u"")
    with io.open(filename, mode="r", encoding="utf-8") as fd:
        return re.sub(text_type(r":[a-z]+:`~?(.*?)`"), text_type(r"``\1``"), fd.read())


setup(
    name="esm_version_checker",
    version="4.7.0",
    url="https://github.com/esm-tools/esm_version_checker",
    license="MIT",
    author="Paul Gierz",
    author_email="pgierz@awi.de",
    description="Mini package to check versions of diverse esm_tools software",
    long_description=read("README.rst"),
    packages=find_packages(exclude=("tests",)),
    install_requires=[
        "Click>=6.0",
        "gitpython",
        "PyGithub",
        "tabulate",
        "esm_rcfile @ git+https://github.com/esm-tools/esm_rcfile.git",
    ],
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    entry_points={"console_scripts": ["esm_versions=esm_version_checker.cli:main"]},
)
