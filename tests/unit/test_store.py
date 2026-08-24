import unittest

from src.store import Store


class TestStore(unittest.IsolatedAsyncioTestCase):
    async def test_get_and_set(self) -> None:
        store = Store()
        self.assertIsNone(await store.get("k1"))
        await store.set("k1", "v1")
        self.assertEqual(await store.get("k1"), "v1")

    async def test_expiration_ex_and_px(self) -> None:
        current_time = 1000.0

        def mock_clock() -> float:
            return current_time

        store = Store(time_func=mock_clock)
        await store.set("k1", "v1", ex=10)
        await store.set("k2", "v2", px=5000)

        self.assertEqual(await store.get("k1"), "v1")
        self.assertEqual(await store.get("k2"), "v2")

        current_time = 1006.0
        self.assertEqual(await store.get("k1"), "v1")
        self.assertIsNone(await store.get("k2"))

        current_time = 1011.0
        self.assertIsNone(await store.get("k1"))

    async def test_set_nx_and_xx(self) -> None:
        store = Store()
        res1 = await store.set("k1", "v1", nx=True)
        self.assertTrue(res1)
        res2 = await store.set("k1", "v2", nx=True)
        self.assertFalse(res2)
        self.assertEqual(await store.get("k1"), "v1")

        res3 = await store.set("k2", "v2", xx=True)
        self.assertFalse(res3)
        self.assertIsNone(await store.get("k2"))

        res4 = await store.set("k1", "v3", xx=True)
        self.assertTrue(res4)
        self.assertEqual(await store.get("k1"), "v3")

    async def test_incr_decr_and_ttl_preservation(self) -> None:
        current_time = 1000.0

        def mock_clock() -> float:
            return current_time

        store = Store(time_func=mock_clock)
        await store.set("num", "10", ex=20)

        val, err = await store.incr_by("num", 1)
        self.assertIsNone(err)
        self.assertEqual(val, 11)

        val, err = await store.incr_by("num", -5)
        self.assertIsNone(err)
        self.assertEqual(val, 6)

        current_time = 1021.0
        self.assertIsNone(await store.get("num"))

        val, err = await store.incr_by("missing", 1)
        self.assertIsNone(err)
        self.assertEqual(val, 1)

        await store.set("str_key", "abc")
        val, err = await store.incr_by("str_key", 1)
        self.assertEqual(err, "ERR value is not an integer or out of range")
        self.assertIsNone(val)


if __name__ == "__main__":
    unittest.main()
