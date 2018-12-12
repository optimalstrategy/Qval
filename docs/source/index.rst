================================
Welcome to Qval's documentation!
================================
`Qval <https://github.com/OptimalStrategy/qval>`_ is a query parameters validation library.
It is built using context managers and designed to work with
`Django Rest Framework <https://www.django-rest-framework.org/>`_, but also supports
`Django <https://www.djangoproject.com/>`_, `Flask <http://flask.pocoo.org/>`_ and
`Falcon <https://falconframework.org/>`_.

Qval can validate incoming query parameters, convert them to python objects and
automatically report errors to the client.

===========
Get started
===========
In order to use Qval in your project, install it with pip:

.. code-block:: bash

    $ pip install qval

The usage is as simple as:

   >>> from qval import validate
   >>> with validate({"integer": "10"}, integer=int) as p:
   ...     print(type(p.integer) is int, p.integer)
   True 10

For more verbose and clear examples refer to :ref:`basic_usage` and
`examples <https://github.com/OptimalStrategy/Qval/tree/master/examples>`_ in the github `repository <https://github.com/OptimalStrategy/qval>`_.


.. toctree::
   :maxdepth: 2
   :caption: Contents

   basic_usage.rst
   frameworks.rst
   configuration.rst
   qval.rst
