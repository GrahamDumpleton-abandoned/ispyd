from setuptools import setup

setup(
    name = 'ispyd',
    packages = [ 'ispyd', 'ispyd.plugins' ],
    version = '0.9.0',
    license = 'Apache 2.0 Licence',
    description = 'WSGI Process Shell',
    author = 'Graham Dumpleton',
    author_email = 'Graham.Dumpleton@gmail.com',
    maintainer = 'Graham Dumpleton',
    maintainer_email = 'Graham.Dumpleton@gmail.com',
    url = 'https://github.com/GrahamDumpleton/wsgi-shell',
    entry_points = { 'console_scripts': ['ispy = ispyd.client:main'] },
)
