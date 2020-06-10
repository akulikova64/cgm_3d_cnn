from setuptools import setup


INSTALL_REQUIRES=[
        "keras>=2.3", 
        "tensorflow>=2.0",
        "matplotlib>=3.1"
        ]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="cgm_3d_cnn", 
    version="0.0.1",
    author="Anastasiya V Kulikova",
    author_email="akulikova82@yahoo.com",
    description="A 3D Convolutional Neural Network that predicts protein secondary structure.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=INSTALL_REQUIRES,
    url="https://github.com/akulikova64/cgm_3d_cnn",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Intended Audience :: Science/Research",
    ],
    python_requires='>=3.6',
)