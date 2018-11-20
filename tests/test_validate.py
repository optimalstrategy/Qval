import pytest
from hypothesis import given, example
from hypothesis import strategies as st

from qval import validate, APIException, InvalidQueryParamException
from qval.framework_integration import (
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_400_BAD_REQUEST,
)


@given(st.integers(), st.floats(allow_nan=False), st.text())
@example(42, 2.79, "string")
def test_params_processed(num, double, string):
    dct = {"num": str(num), "double": str(double), "string": string}
    with validate(dct, num=int, double=float) as p:
        assert p.num == num
        assert p.double == double
        assert p.string == string


def test_params_omitted():
    dct = {"num": "42", "string": "some string"}
    # Disable auto-detection of parameters (box_all)
    params = validate(dct, num=int, box_all=False)
    with pytest.raises(APIException) as e, params as p:
        assert p.num == 42
        assert p.string == "some string"
    assert e.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR


def test_missing_param_throws_error():
    dct = {"param1": "whatever", "param2": "6.66"}
    params = validate(dct, param1=None, param2=float, param3=int)
    with pytest.raises(InvalidQueryParamException) as e, params:
        pass
    assert e.value.status_code == HTTP_400_BAD_REQUEST


@given(
    st.floats(allow_nan=False),
    st.integers(min_value=0),
    st.text(),
    st.integers(max_value=9.9),
    st.text(min_size=10, max_size=10),
)
def test_validator_factory(price, n_items, meta, num2, token):
    currency2f = lambda x: float(x[:-1])
    r = {
        "price": f"{price}$",
        "n_items": str(n_items),
        "meta": meta,
        "num": "10",
        "num2": str(num2),
        "token": token,
    }
    params = (
        validate(
            r, price=currency2f, n_items=int, num=int, num2=int
        ).positive(  # `n_items` must be greater than zero
            "n_items"
        )
        # `num` must be equal to 10
        .eq("num", 10)
        # `num2` must be less than 10
        .lt("num2", 10)
        # Len of `token` must be equal to 10
        .check("token", lambda x: len(x) == 10)
        # The same check as above, but using `transform`
        .eq("token", 10, transform=len)
    )
    with params as p:
        assert {price, n_items, meta, 10, num2, token} == set(p.__dct__.values())


@given(
    st.floats(allow_nan=False),
    st.integers(max_value=0),
    st.text(),
    st.integers(min_value=10),
    st.text(),
)
def test_validation_fails(price, n_items, meta, num2, token):
    currency2f = lambda x: float(x[:-1])
    r = {
        "price": f"{price}$",
        "n_items": str(n_items),
        "meta": meta,
        "num": "42",
        "num2": str(num2),
        "token": token,
    }
    params = (
        validate(
            r, price=currency2f, n_items=int, num=int, num2=int
        ).positive(  # `n_items` must be greater than zero
            "n_items"
        )
        # `num` must be equal to 10
        .eq("num", 10)
        # `num2` must be less than 10
        .lt("num2", 10)
        # Len of `token` must be equal to 10
        .check("token", lambda x: len(x) == 10)
        # The same check as above, but using `transform`
        .eq("token", 10, transform=len)
    )
    with pytest.raises(InvalidQueryParamException) as e, params:
        pass
    assert e.value.status_code == HTTP_400_BAD_REQUEST


def test_exception_handled_in_outside_context():
    """
    See `QueryParamValidator._validate()` and `test_supported_errors_handled()` for more info.
    """
    # Random exception.
    def f(_):
        raise IOError

    r = {"param": "value"}
    with pytest.raises(APIException) as e, validate(r, param=f):
        pass
    assert e.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR


def test_supported_errors_handled():
    """
    Only TypeError, ValueError and KeyError occurred during the validation
    are handled as expected. Any error thrown inside of the context will raise APIError.
    See `test_unsupported_errors_handled()`.
    """

    def exc_factory(exc):
        def f(_):
            raise exc

        return f

    r = {"param": "value"}
    for exc in (TypeError, ValueError, KeyError):
        with pytest.raises(InvalidQueryParamException) as e, validate(
            r, param=exc_factory(exc)
        ):
            pass
        assert e.value.status_code == HTTP_400_BAD_REQUEST


def test_unsupported_errors_handled():
    supported_exceptions = (TypeError, ValueError, KeyError)
    random_exceptions = (IOError, BrokenPipeError, ConnectionError, BufferError)
    r = {"param": "value"}
    for exc in supported_exceptions + random_exceptions:
        with pytest.raises(APIException) as e, validate(r):
            raise exc
        assert e.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR
