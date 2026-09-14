import unittest
from src.store import Store

class StoreTests(unittest.IsolatedAsyncioTestCase):
    async def test_expiration(self) -> None:
        now = [10.0]; store = Store(lambda: now[0])
        self.assertTrue(await store.set('k', 'v', 15.0)); self.assertEqual(await store.ttl('k'), 5)
        now[0] = 16; self.assertIsNone(await store.get('k')); self.assertEqual(await store.ttl('k'), -2)
    async def test_increment(self) -> None:
        store = Store(); value, ok = await store.increment('n', 1); self.assertTrue(ok); self.assertEqual(value, 1)
