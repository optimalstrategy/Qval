import requests

base = "http://localhost:8000/api"


def test_divide_parameters_required(server):
    url = f"{base}/divide"
    assert requests.get(url).status_code == 400
    assert requests.get(f"{url}?a=10").status_code == 400
    assert requests.get(f"{url}?b=10").status_code == 400


def test_divide_parameters_types_validated(server):
    url = f"{base}/divide"
    assert requests.get(f"{url}?a=10&b=2.2").status_code == 400
    assert requests.get(f"{url}?a=str&b=string").status_code == 400


def test_divide_parameters_validated(server):
    url = f"{base}/divide"
    r = requests.get(f"{url}?a=10&b=0")
    assert r.status_code == 400
    assert r.json()["error"] == "Invalid `b` value: 0."


def test_divide_success(server):
    url = f"{base}/divide"
    r = requests.get(f"{url}?a=10&b=5")
    assert r.status_code == 200
    assert r.json()["answer"] == 2


def test_pow_parameters_required(server):
    url = f"{base}/pow"
    assert requests.get(url).status_code == 400
    assert requests.get(f"{url}?a=10").status_code == 400
    assert requests.get(f"{url}?b=10").status_code == 400


def test_pow_parameters_validated(server):
    url = f"{base}/pow"
    assert requests.get(f"{url}?a=string&b=str").status_code == 400


def test_pow_overflow_error(server):
    url = f"{base}/pow"
    r = requests.get(f"{url}?a=2.2324&b=30000000")
    assert r.status_code == 500
    assert (
        r.json()["error"]
        == "An error occurred while processing you request. Please contact the website administrator."
    )


def test_pow_success(server):
    url = f"{base}/pow"
    r = requests.get(f"{url}?a=2&b=10")
    assert r.status_code == 200
    assert r.json()["answer"] == 1024


def test_purchase_parameters_required(server):
    url = f"{base}/purchase"
    params = {"item_id=1", "price=4.2", "token=123456789012"}
    for p1 in params:
        for p2 in params - {p1}:
            assert requests.get(f"{url}?{p1}&{p2}").status_code == 400


def test_purchase_parameters_validated(server):
    url = f"{base}/purchase"
    params = [
        ("-10", "123456789012", "13"),
        ("7723", "12345678901", "71"),
        ("3921", "123456789012", "0"),
    ]
    for p0, p1, p2 in params:
        assert (
            requests.get(f"{url}?itemd_id={p0}&token={p1}&price={p2}").status_code
            == 400
        )


def test_purchase_success(server):
    url = f"{base}/purchase"
    r = requests.get(f"{url}?item_id=10&token=123456789012&price=4.04")
    assert r.status_code == 200
    assert r.json()["success"] == "Item '10' has been purchased. Check: 4.12$."
