"""A setuptools based setup module.
See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
#with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
#    long_description = f.read()

setup(
    name='slack_soundbot',
    version='0.1.0',
    description='Plays sounds in reaction to a Slack channel.',
    author='Sander Evers',
    classifiers=[
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Programming Language :: Python :: 3.7',
    ],

    keywords='slack jukebox soundboard bot',
    packages=find_packages(),
    install_requires=['websocket-client==0.35.0','slacksocket','janus','pyyaml','requests'],
    # package_data={  # Optional
    #     'sample': ['package_data.dat'],
    # },

    entry_points={
        'console_scripts': [
            'slack-soundbot=slack_soundbot.__main__:main',
        ],
    },
)