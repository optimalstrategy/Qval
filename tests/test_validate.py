import pytest

from qval import validate, APIException, InvalidQueryParamException, QvalValidationError
from qval.framework_integration import (
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_400_BAD_REQUEST,
)
from tests.crossframework import builder


def test_params_processed():
    dct = {"num": "42", "double": "2.79", "string": "some string"}
    for request in builder.iterbuild(dct):
        with validate(request, num=int, double=float) as p:
            assert p.num == 42
            assert p.double == 2.79
            assert p.string == "some string"


def test_params_omitted():
    dct = {"num": "42", "string": "some string"}
    for request in builder.iterbuild(dct):
        # Disable auto-detection of parameters (box_all)
        params = validate(request, num=int, box_all=False)
        with pytest.raises(APIException) as e, params as p:
            assert p.num == 42
            assert p.string == "some string"
        assert e.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR


def test_missing_param_throws_error():
    dct = {"param1": "whatever", "param2": "6.66"}
    for request in builder.iterbuild(dct):
        params = validate(request, param1=None, param2=float, param3=int)
        with pytest.raises(InvalidQueryParamException) as e, params:
            pass
        assert e.value.status_code == HTTP_400_BAD_REQUEST


def test_validator_factory():
    currency2f = lambda x: float(x[:-1])
    qparams = {
        "price": "43.5$",
        "n_items": "1",
        "meta": "info",
        "num": "10",
        "num2": "5",
        "token": "0123456789",
    }
    for r in builder.iterbuild(qparams):
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
            assert {43.5, 1, "info", 10, 5, "0123456789"} == set(p.__dct__.values())


def test_validation_fails():
    currency2f = lambda x: float(x[:-1])
    qparams = {
        "price": "43.5$",
        "n_items": "0",
        "meta": "info",
        "num": "-10",
        "num2": "20",
        "token": "012345678",
    }
    for r in builder.iterbuild(qparams):
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

    params = {"param": "value"}
    for r in builder.iterbuild(params):
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

    params = {"param": "value"}
    for r in builder.iterbuild(params):
        for exc in (TypeError, ValueError, KeyError):
            with pytest.raises(InvalidQueryParamException) as e, validate(
                r, param=exc_factory(exc)
            ):
                pass
            assert e.value.status_code == HTTP_400_BAD_REQUEST


def test_unsupported_errors_handled():
    supported_exceptions = (TypeError, ValueError, KeyError)
    random_exceptions = (IOError, BrokenPipeError, ConnectionError, BufferError)
    params = {"param": "value"}
    for r in builder.iterbuild(params):
        for exc in supported_exceptions + random_exceptions:
            with pytest.raises(APIException) as e, validate(r):
                raise exc
            assert e.value.status_code == HTTP_500_INTERNAL_SERVER_ERROR


def test_custom_validation_errors():
    def num_predicate(value: int) -> bool:
        if not 0 < value < 10:
            raise QvalValidationError(
                f"`num` must belong to the interval (0; 10), got '{value}'."
            )
        return True

    params = validate({"num": "5"}, {"num": num_predicate}, num=int)
    with params as p:
        assert p.num == 5

    try:
        with params.apply_to_request({"num": "20"}):
            pass
    except InvalidQueryParamException as e:
        assert "`num` must belong to the interval (0; 10), got '20'." in str(e.detail)
