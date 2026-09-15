import unittest
from src.store import Store

class StoreTest(unittest.TestCase):
    def test_values_and_expiry(self) -> None:
        now = [10.0]; store = Store(lambda: now[0])
        store.set(b'a', b'v', 11); self.assertEqual(store.get(b'a'), b'v')
        now[0] = 12; self.assertIsNone(store.get(b'a'))

    def test_keys(self) -> None:
        store = Store(); store.set(b'ab', b'1'); store.set(b'ac', b'2')
        self.assertEqual(store.keys(b'a?'), [b'ab', b'ac'])
