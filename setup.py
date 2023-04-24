from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

version = "0.0.2"
requirements = ["pika", "multiprocess", "rich", "watchdog"]

setup(
    name="rabbie",
    version=version,
    author="Archie Ferguson",
    author_email="iamarchieferguson@gmail.com",
    url="https://github.com/scuffi/rabbie",
    description="A simple, decorator interface for AMQP based message brokers",
    long_description_content_type="text/markdown",
    long_description=long_description,
    license="MIT license",
    packages=find_packages(exclude=["test"]),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
