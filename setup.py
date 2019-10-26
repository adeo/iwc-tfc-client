import setuptools
from tfc_client import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tfc_client",
    version=__version__,
    author="Alexandre Dath",
    author_email="alex.dath@gmail.com",
    license="ADEO",
    keywords="API Terraform TFC",
    description="A developer friendly Terraform Cloud API client",
    long_description=long_description,
    url="https://github.com/adeo/iwc-tfc-client",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    setup_requires=["pytest-runner"],
    extras_require={
        "dev": ["black", "twine", "wheel"],
        "test": ["pytest", "coverage", "pytest-cov"],
    },
    tests_require=["pytest", "pytest-cov"],
    install_requires=["requests", "pydantic", "pydantic[email]"],
)
