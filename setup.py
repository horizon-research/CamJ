
from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["numpy==1.21.6", "pillow==9.4.0"]

setup(
    name="camj",
    version="0.0.1",
    author="Yu Feng",
    author_email="yfeng28@ur.rochester.edu",
    description="A package for in-sensor processing simulation",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/horizon-research/CamJ",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.8",
    ],
)