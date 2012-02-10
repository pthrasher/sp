import os
from setuptools import setup

kwds = {}

# Read the long description from the README.txt
thisdir = os.path.abspath(os.path.dirname(__file__))
f = open(os.path.join(thisdir, 'README.rst'))
kwds['long_description'] = f.read()
f.close()


setup(
    name='sp',
    version='1.1.0',
    author='Philip Thrasher',
    author_email='philipthrasher@gmail.com',
    url="http://github.com/pthrasher/sp",
    description="Quickly find out which directories / files are hogging your disk space.",
    license="Unlicense",
    classifiers=[
        "License :: Public Domain",
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Utilities",
    ],
    py_modules=["sp"],
    entry_points=dict(
        console_scripts=[
            "sp = sp:sp_main",
        ],
    ),
    **kwds
)
