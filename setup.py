import re
from codecs import open

from setuptools import setup


def read_attributes(string, *names):
    regex_tpl = r'^__{}__\s*=\s*[\'"]([^\'"]*)[\'"]'

    def read(name):
        regex = regex_tpl.format(name)
        return re.search(regex, string, re.MULTILINE).group(1)

    return [read(n) for n in names]


with open('base16_theme_switcher/__init__.py', 'r') as fd:
    content = fd.read()
    name, version, author, email, _license = read_attributes(
        content,
        'title',
        'version',
        'author',
        'email',
        'license'
    )

with open('README.rst', 'r', 'utf-8') as f:
    readme = f.read()

install_requires = ['configobj', 'ruamel.yaml']

tests_require = ['parameterized']

setup(
    name=name,
    version=version,
    description=(
        'A base16 theme configuration tool using *.Xresources theme files.'
    ),
    long_description=readme,
    author=author,
    author_email=email,
    url='https://github.com/piotr-rusin/base16-theme-switcher',
    packages=['base16_theme_switcher', 'test'],
    install_requires=install_requires,
    license=_license,
    classifiers=(
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: X11 Applications',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3.6',
        'Operating System :: POSIX :: Linux',
        'Topic :: Desktop Environment'
    ),
    keywords='themes theming base16',
    tests_require=tests_require,
    extras_require={
        'test': tests_require
    },
)
