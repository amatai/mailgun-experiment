

from setuptools import setup, find_packages

setup(
    name='minimailgun',
    version='0.1',
    description='An experiment to create mini mailgun.',
    long_description=__doc__,
    packages=find_packages(exclude=['*.tests']),
    package_data={
        '': [
            '*.yaml',
        ],
    },
    install_requires=[
        'flask'
    ],
    extras_require={
    },
    test_suite='minimailgun.tests',
    tests_require=[
        'ddt',
        'mock',
        'mongomock',
    ],
    verbose=False,
    entry_points={
    },
)
