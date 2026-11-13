import pytest
from core.database import connect, initialize
from core.inventory import record_sale, receive_stock, products, sales, ledger, edit_product, money_to_centavos


def test_sale_is_atomic_persistent_and_idempotent(store):
    path, pid = store
    sid, created = record_sale(path, pid, 3, "same-token")
    assert created
    assert record_sale(path, pid, 3, "same-token") == (sid, False)
    initialize(path)  # Reopening preserves the data.
    assert products(path).iloc[0].stock_qty == 17
    assert sales(path).revenue_php.sum() == 45
    assert ledger(path).quantity_delta.sum() == 17
    assert len(sales(path)) == 1


def test_overselling_rolls_back(store):
    path, pid = store
    with pytest.raises(ValueError, match="Insufficient"):
        record_sale(path, pid, 21, "oversell")
    assert products(path).iloc[0].stock_qty == 20
    assert sales(path).empty
    assert len(ledger(path)) == 1


@pytest.mark.parametrize("qty", [0, -1, 1.5, "NaN", "Infinity"])
def test_invalid_quantities_rejected(store, qty):
    path, pid = store
    with pytest.raises(ValueError):
        record_sale(path, pid, qty, "bad")
    assert products(path).iloc[0].stock_qty == 20


def test_database_failure_rolls_back_balance(store):
    path, pid = store
    with connect(path) as db:
        db.execute("CREATE TRIGGER prevent_sales BEFORE INSERT ON sales BEGIN SELECT RAISE(ABORT,'test failure'); END")
    with pytest.raises(Exception, match="test failure"):
        record_sale(path, pid, 2, "fail")
    assert products(path).iloc[0].stock_qty == 20


def test_price_snapshot_and_archive(store):
    path, pid = store
    record_sale(path, pid, 2, "first")
    edit_product(path, pid, "Water", "Drinks", 12, 20, 5, False)
    assert sales(path).iloc[0].unit_price_php == 15
    with pytest.raises(ValueError, match="active"):
        record_sale(path, pid, 1, "archived")


def test_receipt_idempotency_and_unknown_product(store):
    path, pid = store
    assert receive_stock(path, pid, 5, "receipt")
    assert not receive_stock(path, pid, 5, "receipt")
    assert products(path).iloc[0].stock_qty == 25
    with pytest.raises(ValueError):
        receive_stock(path, 999, 2)
    assert ledger(path).quantity_delta.sum() == 25


@pytest.mark.parametrize("value", ["-1", "1.001", "nan", "inf", "abc"])
def test_money_validation(value):
    with pytest.raises(ValueError):
        money_to_centavos(value)


def test_demo_seed_ledger_consistency(demo):
    from core.demo_data import seed_demo
    assert not seed_demo(demo)
    for row in products(demo).itertuples():
        assert ledger(demo, row.id).quantity_delta.sum() == row.stock_qty
