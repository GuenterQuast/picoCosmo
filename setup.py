"""
Setup script for picoCosmo 
"""

import sys
from setuptools import setup

pkg_name = "picocosmo"
# import _version_info from package
sys.path[0] = pkg_name
import _version_info

_version = _version_info._get_version_string()

setup(
    name=pkg_name,
    version=_version,
    author='Guenter Quast',
    author_email='Guenter.Quast@online.de',
    packages=[pkg_name],
    inlcude_package_data=True,
    package_data={pkg_name: ['images/*', 'doc/*']},
    install_requires = [],
    scripts=['CosmoGui.py', 'runCosmo.py'],
    classifiers=[
    'Development Status :: 5 - Production/Stable',
    #'Development Status :: 4 - Beta',
    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
    'Programming Language :: Python :: 3.10',
    'Programming Language :: Python :: 3.11',
    'Programming Language :: Python :: 3.12',
    ],
    url='https://www.etp.kit.edu/~quast/',
    license='GNU Public Licence',
    description=' Analysis of waveforms from cosmic ray detectors',
    long_description=open('README').read(),
    setup_requires=[\
        "picodaqa",
        "NumPy >= 1.17.0",
        "SciPy >= 1.1.0",
        "matplotlib >= 3.4.0",]
)
