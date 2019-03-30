import pytest
from qval.utils import FrozenBox


@pytest.fixture()
def dct():
    return {"string": "string", "number": 0x420000, "double": 3.141_592}


def test_box_is_immutable(dct):
    box = FrozenBox(dct)

    with pytest.raises(TypeError) as e:
        box["string"] = "new string"
    assert box.string == "string"
    assert e.type is TypeError

    with pytest.raises(TypeError) as e:
        box.number = 0
    assert box.number == 0x420000
    assert e.type is TypeError

    with pytest.raises(TypeError) as e:
        box["new_key"] = 10
    assert e.type is TypeError

    with pytest.raises(TypeError) as e:
        box.new_key = 10
    assert e.type is TypeError


def test_box_contains_is_valid(dct):
    box = FrozenBox(dct)

    assert "string" in box
    assert "number" in box
    assert "double" in box
    assert "random" not in box


def test_box_iter_works(dct):
    box = FrozenBox(dct)

    assert dict(iter(box)) == dct


def test_error_on_unknown_keys(dct):
    box = FrozenBox(dct)

    with pytest.raises(KeyError) as e:
        box.random
    assert e.type is KeyError

    with pytest.raises(KeyError) as e:
        box["key"]
    assert e.type is KeyError


def test_repr_is_valid(dct):
    box = FrozenBox(dct)
    assert list(eval(repr(box))) == list(FrozenBox(dct))


def test_str_representation(dct):
    box = FrozenBox(dct)
    assert str(box) == f"FrozenBox<{dct}>"
