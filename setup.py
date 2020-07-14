import os
from setuptools import find_packages, setup

# Load version number
__version__ = None

src_dir = os.path.abspath(os.path.dirname(__file__))
version_file = os.path.join(src_dir, 'tap', '_version.py')

with open(version_file) as fd:
    exec(fd.read())

# Load README
with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='typed-argument-parser',
    version=__version__,
    author='Jesse Michel and Kyle Swanson',
    author_email='jessem.michel@gmail.com, swansonk.14@gmail.com',
    description='Typed Argument Parser',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/swansonk14/typed-argument-parser',
    download_url=f'https://github.com/swansonk14/typed-argument-parser/v_{__version__}.tar.gz',
    license='MIT',
    packages=find_packages(),
    package_data={'tap': ['py.typed']},
    install_requires=[
        'typing_extensions >= 3.7.4',
        'typing-inspect >= 0.5'
    ],
    tests_require=['pytest'],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        "Typing :: Typed"
    ],
    keywords=[
        'typing',
        'argument parser',
        'python'
    ]
)
