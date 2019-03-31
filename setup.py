try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(
    name='sqlport',  
    license='BSD',
    version='0.1',
    packages=find_packages(),
    scripts=['bin/sqlport'] ,
    author='Andre Kuehne',
    author_email='andre.kuehne.77@gmail.com',
    maintainer='Andre Kuehne',
    maintainer_email='andre.kuehne.77@gmail.com',
    description='Aspires to port Informix SQL to PostgreSQL',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ak-1/sqlport',
    install_requires=[
        'sly @ git+https://github.com/ak-1/sly35.git@master#egg=sly-0.4',
        'termcolor',
      ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
)
