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
    assert r.json()['error'] == "Invalid `b` value: 0."


def test_divide_success(server):
    url = f"{base}/divide"
    r = requests.get(f"{url}?a=10&b=5")
    assert r.status_code == 200
    assert r.json()['answer'] == 2


def test_pow_parameters_required(server):
    url = f"{base}/pow"
    assert requests.get(url).status_code == 400
    assert requests.get(f"{url}?a=10").status_code == 400
    assert requests.get(f"{url}?b=10").status_code == 400


def test_pow_parameters_validated(server):
    url = f"{base}/divide"
    assert requests.get(f"{url}?a=string&b=str").status_code == 400


def test_pow_overflow_error(server):
    url = f"{base}/divide"
    r = requests.get(f"{url}?a=2.2324&b=30000000")
    assert r.status_code == 500
    # assert r.json()["error"] == ''
