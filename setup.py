from setuptools import setup, find_packages

setup(
    name="osm_rate_check",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A package to calculate OSM user editing rates based on changesets.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/osm_rate_check",  # Replace with your repository URL
    packages=find_packages(),
    install_requires=[
        "requests",
        "PyYAML",
    ],
    entry_points={
        "console_scripts": [
            "osm_rate_check=osm_rate_check.group_osm_rate_check:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Choose your license
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
