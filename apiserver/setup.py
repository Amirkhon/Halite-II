from setuptools import setup


setup(
    name="apiserver",
    packages=["apiserver"],
    include_package_data=True,
    install_requires=[
        "flask",
        "sqlalchemy",
        "alembic",
    ],
)
