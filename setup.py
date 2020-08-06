"""Python Nightscout api client

See:
https://github.com/marciogranzotto/py-nightscout
https://github.com/nightscout/cgm-remote-monitor
"""

import pathlib
from setuptools import setup, find_packages

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

setup(
    name="py_nightscout",
    version="1.1.1",
    description="A library that provides a Python interface to Nightscout",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/marciogranzotto/py-nightscout",
    author="Marcio Granzotto",
    author_email="marciogranzotto@gmail.com",
    license="MIT",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
    keywords="nightscout api client development",
    packages=find_packages(exclude=["tests"]),
    install_requires=["requests", "python-dateutil", "pytz"],
    extras_require={"dev": ["check-manifest"], "test": ["coverage", "httmock"]},
)
