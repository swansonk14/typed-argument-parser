from setuptools import find_packages, setup

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='typed-argument-parser',
    version='1.4.3',
    author='Jesse Michel and Kyle Swanson',
    author_email='jessem.michel@gmail.com, swansonk.14@gmail.com',
    description='Typed Argument Parser',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/swansonk14/typed-argument-parser',
    download_url='https://github.com/swansonk14/typed-argument-parser/v_1.4.3.tar.gz',
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
