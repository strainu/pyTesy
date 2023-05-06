import setuptools
import re
import os

here = os.path.abspath(os.path.dirname(__file__))

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyTesyCloud",
    version="0.0.4",
    author="Strainu",
    author_email="pypi@strainu.ro",
    description="Library for Tesy smart home devices. Based on StyraHem/pyTesy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/strainu/pyTesyCloud",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
