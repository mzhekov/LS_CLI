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
    url="https://github.com/yourusername/leadsauce-cli",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
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
