from setuptools import setup, find_packages

def get_version():
    with open('pandas_nhanes/VERSION') as f:
        return f.read().strip()

setup(
    name="pandas_nhanes",
    version=get_version(),
    packages=find_packages(),
    install_requires=[
        "pandas>=2.2.3",
        "requests>=2.32.3",
        "tqdm>=4.66.4",
        "itables>=2.3.0"
    ],
    author="Jerome",
    author_email="",
    description="A Python API for accessing NHANES data",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/jeromevde/pandas_nhanes",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    include_package_data=True,
) 