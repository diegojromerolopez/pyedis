import unittest


class ServerIntegrationTests(unittest.TestCase):
    def test_suite_loads(self) -> None:
        self.assertEqual(1 + 1, 2)
