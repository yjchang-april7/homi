import re

from setuptools import setup

with open("src/homi/__init__.py", encoding="utf8") as f:
    version = re.search(r'__version__ = "(.*?)"', f.read()).group(1)

setup(
    name='homi',
    version=version,
    install_requires=[
        "grpcio>=1.30.0",
        "grpcio_testing>=1.30.0",
        "grpcio-reflection>=1.30.0",
        "google-api-core>=1.21.0",
        "click>=7.1.2"
    ],
)
