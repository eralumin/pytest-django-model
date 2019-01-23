===================
pytest-django-model
===================

.. image:: https://img.shields.io/pypi/v/pytest-django-model.svg
    :target: https://pypi.org/project/pytest-django-model
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/pytest-django-model.svg
    :target: https://pypi.org/project/pytest-django-model
    :alt: Python versions

.. image:: https://travis-ci.org/kmarilleau/pytest-django-model.svg?branch=master
    :target: https://travis-ci.org/kmarilleau/pytest-django-model
    :alt: See Build Status on Travis CI

A Simple Way to Test your Django Models

----

Description
-----------

This plugin allows you to simply test your Django models, by writing your tests
as you would write your models. On the other hand, pytest-django-model tests
only fields, constants, and the Meta inner class. You will have to write tests
of methods and properties.

The principle here is not really to test the behavior of your models but rather
to make sure that the settings are the right ones.

Installation
------------

You can install "pytest-django-model" via `pip`_ from `PyPI`_::

    $ pip install pytest-django-model


Usage
-----

The plugin is very easy to use, there are only three things to remember\:

- The ``PytestDjangoModel`` metaclass.
- The ``model`` attribute.
- The ``parent`` attribute (optional).


Let's take this model:

.. code-block:: python

    class Foo(Bar, Baz):
        class Meta:
            unique_together = ("name", "email")

        FAVORITE_COLOR_CHOICES = (
            ("BL", "blue"),
            ("YE", "yellow"),
            ("GR", "green"),
            ("RE", "red")
        )

        name = models.CharField(max_length=256)
        email = models.EmailField(blank=True)

        favorite_color = models.CharField(
            max_length=2, choices=FAVORITE_COLOR_CHOICES, default="BL"
        )
        is_awesome = models.BooleanField(default=True)


To test it, we just have to write this:

.. code-block:: python

    from pytest_django_model import PytestDjangoModel

    # Name of the test class doesn't matter.
    class TestFoo(metaclass=PytestDjangoModel):
        class Meta:
            model = Foo
            # Parents can be a model or a list/tuple of models.
            parents = (Bar, Baz)

            unique_together = ("name", "email")

        FAVORITE_COLOR_CHOICES = (
            ("BL", "blue"),
            ("YE", "yellow"),
            ("GR", "green"),
            ("RE", "red")
        )

        name = models.CharField(max_length=256)
        email = models.EmailField(blank=True)

        favorite_color = models.CharField(
            max_length=2, choices=FAVORITE_COLOR_CHOICES, default="BL"
        )
        is_awesome = models.BooleanField(default=True)

And voila! We can now launch tests with the command ``pytest``.

From there, the class ``PytestDjangoModel`` will generate a fake Django model
from constants, fields and options of the Meta class. This model will inherit
all the models of the ``parents`` attribute.

The data of ``Foo`` model and the model created from the ``TestFoo`` class will
be extracted and compared. If any constant differs or isn't found, pytest will
raise a error, same for fields and Meta options.


Contributing
------------
Contributions are very welcome. Development Environment can be setup with
``make setup``. Tests can be run with ``make test``, please ensure the coverage
at least stays the same before you submit a pull request.

License
-------

Distributed under the terms of the `GNU GPL v3.0`_ license,
"pytest-django-model" is free and open source software.


Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed
description.

.. _`Cookiecutter`: https://github.com/audreyr/cookiecutter
.. _`@hackebrot`: https://github.com/hackebrot
.. _`MIT`: http://opensource.org/licenses/MIT
.. _`BSD-3`: http://opensource.org/licenses/BSD-3-Clause
.. _`GNU GPL v3.0`: http://www.gnu.org/licenses/gpl-3.0.txt
.. _`Apache Software License 2.0`: http://www.apache.org/licenses/LICENSE-2.0
.. _`file an issue`: https://github.com/kmarilleau/pytest-django-model/issues
.. _`pytest`: https://github.com/pytest-dev/pytest
.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project
