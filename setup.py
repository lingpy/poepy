from setuptools import setup, find_packages
import codecs


setup(
    name='poepy',
    description="A Python library for handling annotated rhymes.",
    version='0.2.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    zip_safe=False,
    license="GPL",
    include_package_data=True,
    install_requires=[
        'clldutils',
        'lingpy',
    ],
    extras_require={
        "test": ['pytest', 'pytest-coverage']
    },
    url='https://github.com/lingpy/poepy',
    long_description=codecs.open('README.md', 'r', 'utf-8').read(),
    long_description_content_type='text/markdown',
    author='Johann-Mattis List',
    author_email='list@shh.mpg.de',
    keywords='Chinese linguistics, historical linguistics, computer-assisted language comparison'
)
