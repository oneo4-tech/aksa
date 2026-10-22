"""PROTOTYPE demo: the kind of test an AI assistant happily writes. It passes. It tests nothing."""

from unittest.mock import patch

import discount


def test_apply_discount():
    with patch.object(discount, "apply_discount", return_value=90.0) as fake:
        result = discount.apply_discount(100, 10)
    assert result == 90.0
    fake.assert_called_once()


def test_apply_discount_runs():
    result = discount.apply_discount(100, 10)
    assert result is not None
