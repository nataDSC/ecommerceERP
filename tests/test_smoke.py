import sys

from ecommerce_erp.main import main


def test_main_returns_zero(monkeypatch) -> None:
    # Isolate argparse from pytest's own argv, then run with the default SKU.
    monkeypatch.setattr(sys, "argv", ["ecommerce-erp", "--sku", "SKU-003"])
    assert main() == 0
