import pytest
from decimal import Decimal

from qval import InvalidQueryParamException, qval, qval_curry
from qval.framework_integration import HTTP_400_BAD_REQUEST, Request
from qval.utils import FrozenBox
from qval.validator import Validator


stats = []
factories = {
    "double": float,
    "num": int,
    "price": Decimal,
    "hashme": hash,
    "observable": stats.append,
}
validators = {"price": Validator(lambda x: x > 0)}


@qval(factories, validators)
def simple_view(request: Request, params: FrozenBox):
    return request, params


class ViewClass(object):
    @qval(factories, validators)
    def complex_view(
        self, request: Request, param1: int, param2: int, params: FrozenBox
    ):
        return request, param1, param2, params


def test_params_provided():
    request = {
        "double": "3.14",
        "num": "10",
        "price": "2.79",
        "hashme": "s$cret_t0k3n",
        "observable": "important metric",
    }
    # Test simple view
    r, params = simple_view(request)
    assert stats[-1] == request["observable"]
    assert set(r.query_params.keys()) == set(params.__dct__.keys())

    # Test complex view
    r, p1, p2, params = ViewClass().complex_view(request, 1, 2)
    assert (p1, p2) == (1, 2)
    assert stats[-1] == request["observable"]
    assert set(r.query_params.keys()) == set(params.__dct__.keys())


def test_params_validated():
    request = {
        "double": "3.14",
        "num": "10",
        "price": "0",
        "hashme": "s$cret_t0k3n",
        "observable": "important metric",
    }
    with pytest.raises(InvalidQueryParamException) as e:
        simple_view(request)
    assert stats[-1] == request["observable"]
    assert e.value.status_code == HTTP_400_BAD_REQUEST

    with pytest.raises(InvalidQueryParamException) as e:
        ViewClass().complex_view(request, 1, 2)
    assert stats[-1] == request["observable"]
    assert e.value.status_code == HTTP_400_BAD_REQUEST


# Curries qval with a static request (in this case)
# Useful in frameworks with global request classes (e.g. Flask)
def get_curried_qval():
    request = {
        "double": "3.14",
        "num": "10",
        "price": "2.79",
        "hashme": "s$cret_t0k3n",
        "observable": "important metric",
    }
    return qval_curry(request)

curried_qval = get_curried_qval()


@curried_qval(factories, validators)
def view(request, some_param, params):
    return request, some_param, params


def test_curried_qval():
    # Test simple view
    r, test, params = view("test")
    assert test == "test"
    assert stats[-1] == r.query_params["observable"]
    assert set(r.query_params.keys()) == set(params.__dct__.keys())
