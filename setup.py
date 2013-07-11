import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

requires = [
  'colormath',
  'requests',
  'simplejson']

setup(
    name='Lightbox',
    version='1.0',
    description=('Python library and JSON HTTP interface for controlling multi-'
                 'output RGB devices with color transitions in LAB space.'),
    long_description=README,
    classifiers=[
      'Development Status :: 4 - Beta',
      'Intended Audience :: Developers',
      'License :: OSI Approved :: BSD License',
      'Programming Language :: Python',
      'Topic :: Home Automation',
      ],
    author='Elmer de Looff',
    author_email='elmer.delooff@gmail.com',
    url='https://github.com/Frack/Lightbox',
    keywords='lightbox light led colormath',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    )
