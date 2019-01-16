=============
Configuration
=============

--------
Settings
--------

Qval supports configuration via config files and environmental variables.
If :code:`DJANGO_SETTINGS_MODULE` or :code:`SETTINGS_MODULE` are defined, the specified config module will be used. Otherwise,
all lookups would be done in :obj:`os.environ`.

Supported variables:

* | :code:`QVAL_MAKE_REQUEST_WRAPPER = myapp.myfile.my_func`. Customizes behaviour of the
    :func:`make_request() <qval.utils.make_request>` function, which is applied to all incoming requests,
    then the result is passed to :class:`qval.qval.QueryParamValidator`. The provided function must accept :code:`request`
    and return object that supports request interface (see :class:`DummyRequest <qval.framework_integration.DummyRequest>`).

  | For example, the following code adds print to each :func:`make_request() <qval.utils.make_request>` call:

    .. code-block:: python

        # app/utils.py
        def my_wrapper(f):
            @functools.wraps(f)
            def wrapper(request):
                print(f"Received new request: {request}")
                return f(request)
            return wrapper

  | Also you need to execute :code:`export QVAL_MAKE_REQUEST_WRAPPER=app.utils.my_wrapper` in your console
    or to add it to the config file.

* | :code:`QVAL_REQUEST_CLASS = path.to.CustomRequestClass`. :func:`@qval() <qval.qval.qval>` will use it to
    determine which argument is a request. If you have a custom request class that implements
    :class:`DummyRequest() <qval.framework_integration.DummyRequest>` interface, provide it with this variable.

* | :code:`QVAL_LOGGERS = [mylogger.factory, ...] | mylogger.factory`. List of paths or path to a factory callable.
    Specified callable must return object with :class:`Logger` interface. See section `Logging`_) for more info.

-------
Logging
-------

Qval uses a global :obj:`log <qval.utils.log>` object acting as singleton when reporting errors. By default,
:func:`logging.getLogger` function is used as a factory on each call. You can provide your own factory
(see `Settings`_) or disable the logging. Example error message:

.. code-block:: bash

    An error occurred during the validation or inside of the context: exc `<class 'OverflowError'>` ((34, 'Numerical result out of range')).
    | Parameters: <QueryDict: {'a': ['2.2324'], 'b': ['30000000']}>
    | Body      : b''
    | Exception:
    Traceback (most recent call last):
      File "<path>/qval/qval.py", line 338, in inner
        return f(*args, params, **kwargs)
      File "<path>/examples/django-example/app/views.py", line 46, in pow_view
        return JsonResponse({"answer": params.a ** params.b})
    OverflowError: (34, 'Numerical result out of range')
    Internal Server Error: /api/pow
    [19/Nov/2018 07:03:15] "GET /api/pow?a=2.2324&b=30000000 HTTP/1.1" 500 102

Import the :obj:`log <qval.utils.log>` object from :mod:`qval.utils` and configure as you need:

.. code-block:: python

    from qval import log
    # For instance, disable logging:
    log.disable()
