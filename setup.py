

from setuptools import setup, find_packages

setup(
    name='minimailgun',
    version='0.1',
    description='An experiment to create mini mailgun.',
    long_description=__doc__,
    packages=find_packages(exclude=['*.tests']),
    package_data={
    },
    install_requires=[
        'flask',
        'pyyaml',
        'pymongo',
    ],
    extras_require={
    },
    verbose=False,
    entry_points={
    },
)
