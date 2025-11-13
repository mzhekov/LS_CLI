"""
LeadSauce CLI - Professional Network Management Tool
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="leadsauce-cli",
    version="1.0.0",
    author="LeadSauce Development Team",
    author_email="dev@leadsauce.com",
    description="Command-line interface for professional network management",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mzhekov/LS_CLI",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "types-python-dateutil>=2.8.0",
            "types-PyYAML>=6.0.0",
            "types-requests>=2.31.0",
            "types-tabulate>=0.9.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "leadsauce=leadsauce.cli:cli",
        ],
    },
    include_package_data=True,
    package_data={
        "leadsauce": ["templates/*.html", "templates/email_templates/*.html"],
    },
)
