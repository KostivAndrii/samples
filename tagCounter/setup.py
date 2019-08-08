import setuptools

setuptools.setup(
    name="tagCounter",
    version="0.0.1",
    author="Andrii Kostiv",
    author_email="andrii_kostiv@epam.com",
    description="package for counting HTML tags",
    packages=['tagCounter'],
    install_requires=['sqlalchemy','pyaml'],
    package_data={'': ['*.yaml']}
)