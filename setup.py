"""
Cocopot
---------

Cocopot is a microframework for Python. Foucus on mobile service and cloud service, no default template system.

Cocopot is Fun
```````````````````````

.. code:: python

    from cocopot import Cocopot
    app = Cocopot()

    @app.route("/")
    def hello():
        return "Hello World!"

    if __name__ == "__main__":
        app.run()

And Easy to Setup
```````````````````````

.. code:: bash

    $ pip install Cocopot
    $ python hello.py
     * Running on http://localhost:3000/

"""
from __future__ import print_function
import sys
from setuptools.command.test import test as TestCommand
from setuptools import setup

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

setup(
    name='Cocopot',
    version='0.2',
    url='http://github.com/zeaphoo/cocopot/',
    download_url='http://github.com/zeaphoo/cocopot/tarball/0.2',
    license='BSD',
    author='zeaphoo',
    author_email='zeaphoo@gmail.com',
    description='A microframework for python web development, more suitable for mobile service.',
    long_description=__doc__,
    packages=['cocopot'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[],
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
)
