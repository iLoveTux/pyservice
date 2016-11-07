import sys
import platform
from setuptools import setup

tests_require = ["nose>=1.0"]
if sys.version_info < (3,0):
    tests_require = ["nose>=1.0", "mock"]


install_requires = []
if "Windows" in platform.system():
    install_requires.append("pywin32==220")

setup(
    name="pyservice",
    version="0.1.0",
    author="Photonios",
    description="Cross platform service library",
    license="GPLv2",
    keywords="utility tools service daemon",
    url="https://github.com/Photonios/pyservice",
    packages=['pyservice'],
    install_requires=install_requires,
    test_suite="nose.collector",
    tests_require=tests_require,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
    ],
)

