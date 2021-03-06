#!/usr/bin/env python

from setuptools import setup

setup(name='cnxml-validator',
      version='1.1',
      description='''Tools for validating and transforming Siyavula\'s authoring
      formats''',
      author='Siyavula Education',
      author_email='info@siyavula.com',
      url='http://www.siyavula.com/',
      packages=['XmlValidator'],
      scripts=['cnxmlplus2html', 'cnxmlplus2html5', 'cnxmlplus2latex', 'cnxmlplus-validate'],
      package_data={'XmlValidator': ['spec*.xml']},
      include_package_data=True,
      install_requires=['lxml',
                        'argparse'],
      )
