from datetime import timedelta
import pandas as pd
import pytest
from core.database import today, connect
from core.history import import_history, history, finalize_day
from core.inventory import products


def test_import_does_not_change_stock_or_allow_duplicates(store):
    path, pid = store
    frame = pd.DataFrame({"product_id": [pid], "date": [str(today()-timedelta(days=1))], "units_sold": [0]})
    assert import_history(path, frame) == 1
    assert products(path).iloc[0].stock_qty == 20
    with pytest.raises(ValueError, match="already"):
        import_history(path, frame)
    assert len(history(path)) == 1


@pytest.mark.parametrize("changes", [{"date": "wrong"}, {"date": str(today())}, {"product_id": 999}, {"units_sold": -1}, {"units_sold": 1.2}, {"stockout_flag": 2}])
def test_import_validation_is_all_or_nothing(store, changes):
    path, pid = store
    row = {"product_id": pid, "date": str(today()-timedelta(days=2)), "units_sold": 3, "stockout_flag": 0}
    row.update(changes)
    with pytest.raises(ValueError):
        import_history(path, pd.DataFrame([row]))
    assert history(path).empty


def test_finalize_zero_sales_and_stockout(store):
    path, pid = store
    yesterday = today()-timedelta(days=1)
    with connect(path) as db:
        db.execute("UPDATE products SET created_at=? WHERE id=?", (str(yesterday), pid))
    assert finalize_day(path, yesterday, [pid]) == 1
    assert finalize_day(path, yesterday) == 0
    row = history(path).iloc[0]
    assert row.units_sold == 0 and row.stockout_flag == 1
