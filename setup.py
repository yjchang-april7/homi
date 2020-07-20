import re

from setuptools import setup

with open("src/homi/__init__.py", encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

with open("requirements.txt", encoding="utf8") as f:
    requirements = [line for line in f.readlines()]

setup(
    name='homi',
    version=version,
    install_requires=requirements,

)
