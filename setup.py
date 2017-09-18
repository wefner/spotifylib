#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

readme = open('README.rst').read()
history = open('HISTORY.rst').read().replace('.. :changelog:', '')
version = open('.VERSION').read()

# get the requirements from the requirements.txt
requirements_file = [line.strip() 
                     for line in open('requirements.txt').readlines()
                     if line.strip() and not line.startswith('#')]
requirements = requirements_file

# get the test requirements from the test_requirements.txt
test_requirements = [line.strip() 
                     for line in open('requirements/testing.txt').readlines()
                     if line.strip() and not line.startswith('#')]

setup(
    name='''spotifylib''',
    version=version,
    description='''Spotify API Client''',
    long_description=readme + '\n\n' + history,
    author='''Oriol Fabregas''',
    author_email='''fabregas.oriol@gmail.com''',
    url='''https://github.com/wefner/spotifylib''',
    packages=find_packages(where='.', exclude=('tests', 'hooks')),
    package_dir={'''spotifylib''':
                 '''spotifylib'''},
    include_package_data=True,
    install_requires=requirements,
    license='''MIT''',
    zip_safe=False,
    keywords='''spotifylib''',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        '''License :: OSI Approved :: MIT License''',
        'Natural Language :: English',
        'Programming Language :: Python',
    ],
    test_suite='tests',
    tests_require=test_requirements,
    data_files=[
        ('', [
            '.VERSION',
            'LICENSE',
            'AUTHORS.rst',
            'CONTRIBUTING.rst',
            'HISTORY.rst',
            'README.rst',
            'USAGE.rst',
        ]),
    ]
)
