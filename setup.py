from setuptools import setup, find_packages

setup(
    name="smart_parking_system",
    version="0.1.0",
    # if you leave your modules in the root, this will pick up *any*
    # directories with an __init__.py—but you have flat .py files,
    # so we’ll add a tiny package wrapper below.
    packages=find_packages(),

    # all your pip dependencies here
    install_requires=[
        "opencv-python",
        "fastapi",
        "uvicorn",
    ],
)
