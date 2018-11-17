from decimal import Decimal
from qval import Validator

purchase_factories = {"price": Decimal, "item_id": int, "token": None}

purchase_validators = {
    "price": Validator(lambda x: x > 0),
    "token": Validator(lambda x: len(x) == 12),
    "item_id": Validator(lambda x: x >= 0),
}
