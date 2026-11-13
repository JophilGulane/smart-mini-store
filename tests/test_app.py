"""Exercise real Streamlit controls with isolated data; no presentation records change."""
from pathlib import Path
from streamlit.testing.v1 import AppTest
from core.inventory import products, sales


def button(app, label):
    return next(b for b in app.button if b.label == label)


def test_pages_and_learning_controls(tmp_path, monkeypatch):
    monkeypatch.setenv("MINISTORE_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"streamlit_app.py"), default_timeout=30).run()
    assert not app.exception
    for page, action in [("Products & Stock", None), ("Record Sales", None),
                         ("Demand Forecast", "Train & evaluate forecast"),
                         ("Product Groups", "Run product clustering"),
                         ("Restocking Simulator", "Train restocking agent")]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, f"Page failed: {page}"
        if action:
            button(app, action).click().run(timeout=30)
            assert not app.exception, f"Action failed: {action}"
            assert not app.error, f"Action error: {action}"
    app.sidebar.selectbox[0].set_value("My store").run()
    assert not app.exception
    assert products(tmp_path/"store.db").empty


def test_live_sale_updates_stock_and_receipt(tmp_path, monkeypatch):
    monkeypatch.setenv("MINISTORE_DATA_DIR", str(tmp_path))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1]/"streamlit_app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value("Record Sales").run()
    path = tmp_path/"demo.db"
    pid = next(s for s in app.selectbox if s.key == "sale_product_demo").value
    before = int(products(path).set_index("id").loc[pid, "stock_qty"])
    button(app, "Save sale").click().run()
    assert not app.exception
    assert products(path).set_index("id").loc[pid, "stock_qty"] == before-1
    assert any("saved" in s.value.lower() for s in app.success)
    assert "Start another sale" in [b.label for b in app.button]
