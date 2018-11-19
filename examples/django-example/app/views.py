from decimal import Decimal

from django.http import HttpRequest, JsonResponse
from qval import qval, validate

from app.validators import *


def division_view(request: HttpRequest):
    """
    GET /api/divide?
    param a : int
    param b : int, nonzero

    Example: GET /api/divide?a=10&b=2&token=abcdefghijkl -> 200, {"answer": 5}
    """
    # Parameter validation occurs in the context manager.
    # If validation fails or user code throws an error, context manager
    # will raise InvalidQueryParamException or APIException respectively.
    # In Django, these exception will be processed and result
    # in error codes (400 and 500) on the client side.
    params = (
        validate(request, a=int, b=int)
        # `b` must be anything but zero
        .nonzero("b")
    )
    with params as p:
        return JsonResponse({"answer": p.a // p.b})


@qval({"a": float, "b": float})
def pow_view(request, params):
    """
    GET /api/pow?
    param a : float
    param b : float

    Example: GET /api/pow?a=2&b=3 -> 200, {"answer": 8.0}
    Example: GET /api/pow?a=2&b=3000000000000 -> 500,
    {
        "error": "An error occurred while processing you request. Please contact the website administrator."
    }
   """
    # Here we don't catch the OverflowError if `b` is too big.
    # This will result in 500 error on the client side.
    return JsonResponse({"answer": params.a ** params.b})


@qval(purchase_factories, purchase_validators)
def purchase_view(request, params):
    """
    GET /api/purchase?
    param item_id : int, positive
    param price   : float, greater than zero
    param token   : string, length == 12

    Example: GET /api/purchase?item_id=1&price=5.8&token=abcdefghijkl
             -> {"success": "Item '1' has been purchased. Check: 5.92$."
    """
    tax = 0.02
    cost = params.price * Decimal(1 + tax)
    return JsonResponse({
        "success": f"Item '{params.item_id}' has been purchased. Check: {round(cost, 2)}$."
    })
