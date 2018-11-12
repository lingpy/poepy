#import distribute_setup
#distribute_setup.use_setuptools()

from setuptools import setup, find_packages,Extension
import codecs
# setup package name etc as a default
pkgname = 'poepy'


setup(
        name=pkgname,
        description="A Python library for handling annotated rhymes.",
        version='0.1.0',
        packages=find_packages(where='src'),
        package_dir={'': 'src'},
        zip_safe=False,
        license="GPL",
        include_package_data=True,
        install_requires=['lingpy'],
        url='https://github.com/lingpy/poepy',
        long_description=codecs.open('README.md', 'r', 'utf-8').read(),
        long_description_content_type='text/markdown',
        #entry_points={
        #    'console_scripts': ['sinopy=sinopy.cli:main'],
        #},
        author='Johann-Mattis List',
        author_email='list@shh.mpg.de',
        keywords='Chinese linguistics, historical linguistics, computer-assisted language comparison'
        )