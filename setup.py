#!/usr/bin/env python

import importlib
from setuptools import setup, find_packages
module = importlib.import_module('sf-rfc-validate')

pkg = "sf-rfc-validate"
version = module.__version__

setup(
    name=pkg,
    version=version,
    description="Validate HTTP Structured Fields in XML2RFC documents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Mark Nottingham",
    author_email="mnot@mnot.net",
    license="MIT",
    url=f"https://github.com/mnot/{pkg}/",
    download_url=f"https://github.com/mnot/{pkg}/tarball/{pkg}-{version}",
    packages=find_packages(),
    scripts=["sf-rfc-validate.py"],
    requires=["http_sfv"],
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Operating System :: POSIX",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
