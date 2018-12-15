import pytest

from qval import InvalidQueryParamException
from qval.utils import make_request
from qval.qval import QueryParamValidator
from tests.crossframework import builder


def test_chain_validators():
    request = {
        "num": "42",
        "num2": "-10",
        "num3": "3.14",
        "power": "16",
        "power2": "25",
        "new_param": "2.79",
    }
    # fmt: off
    factories = {
        "num": int,
        "num2": int,
        "num3": float,
        "power": int,
        "power2": lambda x: float(x) ** 0.5
    }
    # fmt: on

    qval = (
        QueryParamValidator(make_request(request), factories)
        .check("power", lambda x: (x ** 0.5).is_integer())
        .check("power2", float.is_integer)
        .eq("num", 42)
        .gt("num", 41)
        .lt("num2", 0)
        .nonzero("num3")
        .positive("power")
    )
    qval.add_predicate(
        "new_param", lambda x: float(x) not in (float("inf"), float("-inf"))
    )
    for r in builder.iterbuild(request):
        params = qval.apply_to_request(r)
        with params as p:
            assert p.num == 42
            assert p.num2 == -10
            assert p.num3 == 3.14
            assert p.power == 16
            assert p.power2 == 5
            assert p.new_param == "2.79"

    bad_examples = {
        "num": "0",  # is not equal to 42
        "num2": "1",  # is greater than zero
        "num3": "0",  # is equal to zero
        "power": "-64",  # is not positive
        "power2": "24",  # is not a perfect square
        "new_param": "inf",  # is an infinity
    }

    for r in builder.iterbuild(bad_examples):
        params = qval.apply_to_request(r)
        with pytest.raises(InvalidQueryParamException) as e, params:
            pass
        assert e.type is InvalidQueryParamException
