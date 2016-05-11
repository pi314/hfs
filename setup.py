import sys
import os

from setuptools import find_packages, setup

def get_hfs_version():
    constants_file_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'hfs/constants.py'
    )
    with open(constants_file_path) as constants:
        for line in constants:
            if line.startswith('__version__'):
                code = compile(line, '<string>', 'single')
                version = code.co_consts[0]

        return version


setup(
    name='hfs',
    version=get_hfs_version(),
    description='Tiny HTTP File Server',
    url='https://github.com/pi314/hfs',
    author='Cychih',
    author_email='michael66230@gmail.com',
    maintainer='Cychih',
    maintainer_email='michael66230@gmail.com',
    license='WTFPL',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Natural Language :: Chinese (Traditional)',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Utilities',
    ],
    install_requires=[],
    packages=find_packages(exclude=['scripts']),
    package_data={
            '': ['*.py', 'static/*', '*.html'],
        },
    scripts=['scripts/hfs'],
)
