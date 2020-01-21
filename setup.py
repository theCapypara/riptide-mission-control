from setuptools import setup, find_packages

# README read-in
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()
# END README read-in

setup(
    name='riptide-mission-control',
    version='0.5.0rc1',
    packages=find_packages(),
    package_data={
        'tornadoql': ['static/graphiql.html'],
        'riptide_mission_control': ['schema.graphqls'],
    },
    description='Tool to manage development environments for web applications using containers - GraphQL API Server',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/Parakoopa/riptide-proxy/',
    install_requires=[
        'riptide-lib >= 0.5, < 0.6',
        'tornado >= 6.0',
        'Click >= 7.0',
        'graphene >= 2.0, < 3.0',
        'python-prctl >= 1.7; sys_platform == "linux"',
        'docutils >= 0.15'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    entry_points='''
        [console_scripts]
        riptide_mc=riptide_mission_control.main:main
    ''',
)
