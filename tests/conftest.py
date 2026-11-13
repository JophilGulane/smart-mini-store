import pytest
from core.database import initialize
from core.demo_data import seed_demo
from core.inventory import add_product


@pytest.fixture
def store(tmp_path):
    path = tmp_path/"store.db"
    initialize(path)
    pid = add_product(path, "Water", "Drinks", "10.00", "15.00", 20, 5)
    return path, pid


@pytest.fixture
def demo(tmp_path):
    path = tmp_path/"demo.db"
    initialize(path)
    seed_demo(path)
    return path
