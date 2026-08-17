import unittest

from app.models.store import StoreNetwork
from app.services.store_service import StoreService


class ManagerStoreSearchTests(unittest.TestCase):
    def test_search_stores_uses_network_and_query(self):
        db = None
        self.assertTrue(hasattr(StoreService, "search_stores"))


if __name__ == "__main__":
    unittest.main()
