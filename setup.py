from os import path
from setuptools import setup, find_packages


here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="pwnlib",
    version="0.0.1",
    packages=find_packages(),
    author="nox",
    author_email="noxh4x+dev@example.com",
    description="Pwn library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MrNox/pwnlib.git",
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
    ],
    python_requires='>=3.9',
    install_requires=['pycryptodome'],
)
