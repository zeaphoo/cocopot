"""
Flagon
-------

Flagon is a microframework for Python. Foucus on mobile service and cloud service, no default template system.

Flagon is Fun
````````````

.. code:: python

    from flagon import Flagon
    app = Flagon()

    @app.route("/")
    def hello():
        return "Hello World!"

    if __name__ == "__main__":
        app.run()

And Easy to Setup
`````````````````

.. code:: bash

    $ pip install Flagon
    $ python hello.py
     * Running on http://localhost:3000/

"""
from __future__ import print_function
from setuptools import setup

setup(
    name='Flagon',
    version='0.1',
    url='http://github.com/zeaphoo/flagon/',
    license='BSD',
    author='zeaphoo',
    author_email='zeaphoo@gmail.com',
    description='A microframework based on Flask, more suitable for mobile service.',
    long_description=__doc__,
    packages=['flagon'],
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=[],
    classifiers=[
        'Development Status :: 3 - Alpha',
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
