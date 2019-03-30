import pytest
from decimal import Decimal

from qval import InvalidQueryParamException, qval, qval_curry
from qval.framework_integration import HTTP_400_BAD_REQUEST, Request
from qval.utils import FrozenBox, dummyfy
from qval.validator import Validator

from tests.crossframework import builder


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
    return dummyfy(request), params


class ViewClass(object):
    @qval(factories, validators)
    def complex_view(
        self, request: Request, param1: int, param2: int, params: FrozenBox
    ):
        return dummyfy(request), param1, param2, params


def test_params_provided():
    params = {
        "double": "3.14",
        "num": "10",
        "price": "2.79",
        "hashme": "s$cret_t0k3n",
        "observable": "important metric",
    }
    for request in builder.iterbuild(params):
        # Test simple view
        r, box = simple_view(request)
        assert stats[-1] == params["observable"]
        assert set(r.query_params.keys()) == set(box.__dct__.keys())

        # Test complex view
        r, p1, p2, box = ViewClass().complex_view(request, 1, 2)
        assert (p1, p2) == (1, 2)
        assert stats[-1] == params["observable"]
        assert set(r.query_params.keys()) == set(box.__dct__.keys())


def test_params_validated():
    params = {
        "double": "3.14",
        "num": "10",
        "price": "0",
        "hashme": "s$cret_t0k3n",
        "observable": "important metric",
    }
    for request in builder.iterbuild(params):
        with pytest.raises(InvalidQueryParamException) as e:
            simple_view(request)
        assert stats[-1] == params["observable"]
        assert e.value.status_code == HTTP_400_BAD_REQUEST

        with pytest.raises(InvalidQueryParamException) as e:
            ViewClass().complex_view(request, 1, 2)
        assert stats[-1] == params["observable"]
        assert e.value.status_code == HTTP_400_BAD_REQUEST


def test_qval_requires_params():
    with pytest.raises(TypeError) as e:

        @qval
        def sample():
            pass

    assert e.type is TypeError


def test_qval_requires_request_argument():
    @qval({})
    def sample(request):
        pass

    with pytest.raises(ValueError) as e:
        sample(object())
    assert e.type is ValueError

    @qval({})
    def multi_param(first, second, request):
        pass

    with pytest.raises(ValueError) as e:
        multi_param(object(), list(), {})
    assert e.type is ValueError


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
    return dummyfy(request), some_param, params


def test_curried_qval():
    # Test simple view
    r, test, box = view("test")
    assert test == "test"
    assert stats[-1] == r.query_params["observable"]
    assert set(r.query_params.keys()) == set(box.__dct__.keys())
