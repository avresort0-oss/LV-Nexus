from setuptools import setup, find_packages

setup(
    name="LV-Nexus",
    version="2.1.0",
    description="Next-Gen Windows Performance Architecture",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "psutil>=5.9.0",
        "pywebview>=4.4.1",
        "wmi>=1.5.1",
        "comtypes>=1.3.1"
    ],
    entry_points={
        "console_scripts": [
            "lvnexus=main:bootstrap",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
    ],
    python_requires=">=3.8",
)
