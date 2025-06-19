#!python3

from setuptools import setup, find_packages
from py_iracing import __version__

setup(
    name='py_iracing',
    version=__version__,
    description='Python 3 implementation of iRacing SDK',
    author='voyagen',
    url='https://github.com/voyagen/py_iracing',
    packages=find_packages(),
    license='MIT',
    platforms=['win64'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
    ],
    entry_points={
        'console_scripts': ['py_iracing = py_iracing.cli:main'],
    },
    install_requires=[
        'PyYAML >= 5.3',
        'aiohttp >= 3.8.1',
    ],
    tests_require=[
        'pytest',
        'pytest-asyncio',
    ],
)
