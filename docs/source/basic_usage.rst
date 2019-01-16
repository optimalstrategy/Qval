.. _basic_usage:

===========
Basic usage
===========
Qval provides two ways of validation:

1. A function called :func:`validate() <qval.qval.validate>`:

    .. code-block:: python

        def validate(
            # Request instance. Must be a dictionary or implement request interface.
            request: Union[Request, Dict[str, str]],
            # Dictionary of (param_name -> `Validator()` object).
            validators: Dict[str, Validator] = None,
            # Provide true if you want to access all parameters of the request in the context.
            box_all: bool = True,
            # Factories that will be used to convert parameters to python objects (param -> [callable[str] => object]).
            **factories,
        ) -> QueryParamValidator:


2. A decorator called :func:`@qval() <qval.qval.qval>`:

    .. code-block:: python

        # Wrapped view must accept `request` as either first or second argument
        def qval(
            # Dictionary of (parameter -> factory or None)
            factories: Dict[str, Optional[Callable[[str], Any]]],
            # Dictionary of (parameter -> Validator)
            validators: Dict[str, Validator] = None,
            # Boxing flag. Provide True to access all provided parameters in the context manager
            box_all: bool = True,
            # Optional request instance that will be used to obtain query parameters
            request_: Request = None,
        ):


Let's jump to a quick example.
Imagine you have a RESTful calculator with an endpoint called :code:`/api/divide`. You can use :func:`validate() <qval.qval.validate>`
to automatically convert query parameters to python objects and then validate them:

    .. code-block:: python

        from qval import validate
        ...

        def division_view(request):
            """
            GET /api/divide?
            param a     : int
            param b     : int, nonzero
            param token : string, length = 12

            Example: GET /api/divide?a=10&b=2&token=abcdefghijkl -> 200, {"answer": 5}
            """
            # Parameter validation occurs in the context manager.
            # If validation fails or user code throws an error, context manager
            # will raise InvalidQueryParamException or APIException respectively.
            # In Django Rest Framework, these exceptions will be processed and result
            # in error codes (400 and 500) on the client side.
            params = (
                # `a` and `b` must be integers
                # Note: in order to get a nice error message on the client side,
                # you factory should raise either ValueError or TypeError
                validate(request, a=int, b=int)
                # `b` must be anything but zero
                .nonzero("b")
                # The `transform` callable will be applied to parameter before the check.
                # In this case we'll get `token`'s length and check if it is equal to 12.
                .eq("token", 12, transform=len)
            )
            # validation starts here
            with params as p:
                return Response({"answer": p.a // p.b})

    .. code-block:: javascript

        // GET /api/divide?a=10&b=2&token=abcdefghijkl
        // Browser:
        {
          "answer": 5
        }


    Sending :code:`b = 0` to this endpoint will result in the following message on the client side:

    .. code-block:: javascript

        // GET /api/divide?a=10&b=0&token=abcdefghijkl
        {
          "error": "Invalid `b` value: 0."
        }


If you have many parameters and custom validators, it's better to use the :func:`@qval() <qval.qval.qval>` decorator:

    .. code-block:: python

        # validators.py
        from decimal import Decimal
        from qval import Validator
        ...

        def price_validator(price: int) -> bool:
            """
            A predicate to validate `price` query parameter.
            Provides custom error message.
            """
            if price <= 0:
                # If price does not match our requirements, we raise QvalValidationError() with a custom message.
                # This exception will be handled in the context manager and will be reraised
                # as InvalidQueryParamException() [HTTP 400].
                raise QvalValidationError(f"Price must be greater than zero, got \'{price}\'.")
            return True


        purchase_factories = {"price": Decimal, "item_id": int, "token": None}
        purchase_validators = {
            "token": Validator(lambda x: len(x) == 12),
            # Validator(p) can be omitted if there is only one predicate:
            "item_id": lambda x: x >= 0,
            "price": price_validator,
        }

        # views.py
        from qval import qval
        from validators import *
        ...

        # Any function or method wrapped with `qval()` must accept request as
        # either first or second argument, and parameters as last.
        @qval(purchase_factories, purchase_validators)
        def purchase_view(request, params):
            """
            GET /api/purchase?
            param item_id : int, positive
            param price   : float, greater than zero
            param token   : string, len == 12

            Example: GET /api/purchase?item_id=1&price=5.8&token=abcdefghijkl
            """
            # do something with p.item_id and p.price
            print(f"{params.item_id} costs {params.price}$.")
            ...
