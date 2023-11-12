from pathlib import Path
from setuptools import find_packages, setup

# Load version number
__version__ = ""
version_file = Path(__file__).parent.absolute() / "tap" / "_version.py"

with open(version_file) as fd:
    exec(fd.read())

# Load README
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="typed-argument-parser",
    version=__version__,
    author="Jesse Michel and Kyle Swanson",
    author_email="jessem.michel@gmail.com, swansonk.14@gmail.com",
    description="Typed Argument Parser",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/swansonk14/typed-argument-parser",
    download_url=f"https://github.com/swansonk14/typed-argument-parser/archive/refs/tags/v_{__version__}.tar.gz",
    license="MIT",
    packages=find_packages(),
    package_data={"tap": ["py.typed"]},
    install_requires=["typing-inspect >= 0.7.1", "docstring-parser >= 0.15"],
    tests_require=["pytest"],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Typing :: Typed",
    ],
    keywords=["typing", "argument parser", "python"],
)
