#!/usr/bin/env python
# coding: utf-8

import os
import codecs
from setuptools import setup


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="pytest-django-models",
    version="0.1.0",
    author="Kevin Marilleau",
    author_email="kevin.marilleau@gmail.com",
    maintainer="Kevin Marilleau",
    maintainer_email="kevin.marilleau@gmail.com",
    license="GNU GPL v3.0",
    url="https://github.com/kmarilleau/pytest-django-models",
    description="A Simple Way to Test your Django Models",
    long_description=read("README.rst"),
    py_modules=["pytest_django_models"],
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*",
    install_requires=["pytest>=3.5.0", "django"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points={"pytest11": ["django-models = pytest_django_models.plugin"]},
)
