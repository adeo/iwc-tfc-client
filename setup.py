import setuptools

from tfc_client import __version__


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tfc_client",
    version=__version__,
    author="Alexandre Dath for ADEO",
    author_email="alex.dath@gmail.com",
    license="MIT",
    keywords="API Terraform TFC",
    description="A developer friendly Terraform Cloud API client",
    long_description_content_type="text/markdown",
    long_description=long_description,
    url="https://github.com/adeo/iwc-tfc-client",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    extras_require={
        "dev": ["black", "twine", "wheel"],
        "test": ["pytest", "coverage", "pytest-cov"],
    },
    tests_require=["pytest", "pytest-cov"],
    install_requires=[
        "requests",
        "pydantic>=0.32.2",
        "pydantic[email]",
        "email-validator>=1.0.3",
        "idna>=2.0.0",
        "dnspython>=1.15.0",
        "inflection",
    ],
)
