from setuptools import setup

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="resumecli",
    version="1.0.0",
    package_dir={"": "src"},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "resumecli=cli:app",
        ],
    },
)
