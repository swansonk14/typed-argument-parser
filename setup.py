from setuptools import find_packages, setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='typed-argument-parsing',
    version='0.0.1',
    author='Jesse Michel and Kyle Swanson',
    author_email='kswanson@asapp.com',
    description='Typed Argument Parsing',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/swansonk14/typed-argument-parsing',
    license='MIT',
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=[
        'argument parsing',
        'typing'
    ]
)
