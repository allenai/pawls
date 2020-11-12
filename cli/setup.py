from setuptools import setup, find_packages

with open("readme.md", "r") as readme_file:
    readme = readme_file.read()


setup(
    name="pawls",
    version="0.0.1",
    description="PAWLS (PDF Annotation with Labels and Structure)",
    packages=find_packages(),
    long_description=readme,
    url="http://github.com/allenai/pawls",
    author="Mark Neumann",
    author_email="markn@allenai.org",
    keywords="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    license="Apache 2.0",
    install_requires=[
        "click>=6.7",
        "requests",
        "boto3",
        "tqdm",
    ],
    python_requires=">=3.6",
    entry_points={"console_scripts": ["pawls=pawls.__main__:pawls_cli"]},
    zip_safe=False,
)
