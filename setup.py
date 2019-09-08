from setuptools import find_packages, setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='typed-argument-parser',
    version='1.3',
    author='Jesse Michel and Kyle Swanson',
    author_email='swansonk.14@gmail.com',
    description='Typed Argument Parser',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/swansonk14/typed-argument-parser',
    download_url='https://github.com/swansonk14/typed-argument-parser/v_1.3.tar.gz',
    license='MIT',
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    keywords=[
        'typing',
        'argument parser',
        'python'
    ]
)
