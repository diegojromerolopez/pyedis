"""Unit and dispatcher integration tests for GEOADD and geohash encoding."""

import unittest

from src.commands import CommandDispatcher
from src.handlers.geospatial.geohash_codec import (
    MAX_HASH,
    decode_geohash,
    encode_geohash,
    validate_coordinates,
)
from src.store import Store
from tests.doubles import MutableClock


class RecordingAOF:
    """In-memory persistence double recording mutation and truncate calls."""

    def __init__(self) -> None:
        self.records: list[dict[str, object]] = []
        self.truncated = False

    def log_mutation(self, record: dict[str, object]) -> None:
        self.records.append(record)

    def truncate(self) -> None:
        self.records.clear()
        self.truncated = True


class TestGeoHashCodec(unittest.TestCase):
    def test_encoding_is_52_bit_and_decodes_to_same_cell(self) -> None:
        value = encode_geohash(12.5, 48.1)
        self.assertGreaterEqual(value, 0)
        self.assertLessEqual(value, MAX_HASH)
        longitude, latitude = decode_geohash(value)
        self.assertLess(abs(longitude - 12.5), 180 / (1 << 25))
        self.assertLess(abs(latitude - 48.1), (85.05112878 * 2) / (1 << 25))

    def test_different_coordinates_produce_different_hashes(self) -> None:
        berlin = encode_geohash(13.4, 52.5)
        paris = encode_geohash(2.35, 48.85)
        self.assertNotEqual(berlin, paris)
        self.assertGreaterEqual(berlin, 0)
        self.assertLessEqual(berlin, MAX_HASH)

    def test_coordinate_validation_rejects_nonfinite_and_out_of_bounds_values(self) -> None:
        self.assertTrue(validate_coordinates(-180.0, -85.05112878))
        self.assertTrue(validate_coordinates(180.0, 85.05112878))
        for longitude, latitude in ((180.0001, 0), (-180.0001, 0), (0, 85.1), (0, -85.1)):
            with self.subTest(longitude=longitude, latitude=latitude):
                self.assertFalse(validate_coordinates(longitude, latitude))
        self.assertFalse(validate_coordinates(float("nan"), 0))
        self.assertFalse(validate_coordinates(0, float("inf")))

    def test_decode_rejects_values_outside_unsigned_52_bit_range(self) -> None:
        for value in (-1, MAX_HASH + 1, 1.0):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    decode_geohash(value)  # type: ignore[arg-type]

    def test_encode_raises_for_invalid_coordinates(self) -> None:
        with self.assertRaises(ValueError):
            encode_geohash(200.0, 0.0)


class TestGeoAdd(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = MutableClock(100.0)
        self.store = Store(clock=self.clock)
        self.aof = RecordingAOF()
        self.dispatcher = CommandDispatcher(self.store, self.aof)  # type: ignore[arg-type]

    async def dispatch(self, *args: str) -> bytes:
        reply, close = await self.dispatcher.dispatch([arg.encode() for arg in args])
        self.assertFalse(close)
        return reply

    async def test_geoadd_registers_with_dispatcher_and_stores_members(self) -> None:
        reply = await self.dispatch(
            "GEOADD", "cities", "13.4", "52.5", "berlin", "2.35", "48.85", "paris"
        )
        self.assertEqual(reply, b":2\r\n")
        self.assertEqual(set(self.store._zsets["cities"]), {"berlin", "paris"})
        self.assertEqual(
            self.aof.records,
            [
                {
                    "op": "GEOADD",
                    "args": ["cities", "13.4", "52.5", "berlin", "2.35", "48.85", "paris"],
                }
            ],
        )

    async def test_nx_xx_and_ch_return_redis_style_counts(self) -> None:
        self.assertEqual(await self.dispatch("GEOADD", "places", "0", "0", "one"), b":1\r\n")
        self.assertEqual(await self.dispatch("GEOADD", "places", "1", "1", "one"), b":0\r\n")
        self.assertEqual(await self.dispatch("GEOADD", "places", "2", "2", "one", "NX"), b":0\r\n")
        self.assertEqual(
            await self.dispatch("GEOADD", "places", "2", "2", "missing", "XX"), b":0\r\n"
        )
        self.assertEqual(await self.dispatch("GEOADD", "places", "2", "2", "one", "CH"), b":1\r\n")
        self.assertEqual(await self.dispatch("GEOADD", "places", "2", "2", "one", "CH"), b":0\r\n")
        self.assertAlmostEqual(self.store._zsets["places"]["one"], float(encode_geohash(2, 2)))

    async def test_invalid_coordinates_and_syntax_do_not_mutate_or_log(self) -> None:
        for args, expected in (
            (("GEOADD", "x", "181", "0", "m"), b"-ERR invalid longitude,latitude pair\r\n"),
            (("GEOADD", "x", "0", "nan", "m"), b"-ERR invalid longitude,latitude pair\r\n"),
            (("GEOADD", "x", "NX", "XX", "0", "0", "m"), b"-ERR syntax error\r\n"),
            (
                ("GEOADD", "x", "0", "0"),
                b"-ERR wrong number of arguments for 'geoadd' command\r\n",
            ),
        ):
            with self.subTest(args=args):
                self.assertEqual(await self.dispatch(*args), expected)
        self.assertNotIn("x", self.store._zsets)
        self.assertEqual(self.aof.records, [])

    async def test_duplicate_members_are_updated_once_and_aof_only_records_changes(self) -> None:
        reply = await self.dispatch("GEOADD", "x", "0", "0", "m", "1", "1", "m")
        self.assertEqual(reply, b":2\r\n")
        self.assertEqual(len(self.store._zsets["x"]), 1)
        self.assertEqual(len(self.aof.records), 1)
        before = len(self.aof.records)
        self.assertEqual(await self.dispatch("GEOADD", "x", "1", "1", "m", "NX"), b":0\r\n")
        self.assertEqual(len(self.aof.records), before)

    async def test_unknown_command_still_rejected_after_geoadd_registration(self) -> None:
        reply = await self.dispatch("NOTACOMMAND")
        self.assertEqual(reply, b"-ERR unknown command 'NOTACOMMAND'\r\n")

    async def test_wrongtype_error_when_key_holds_string(self) -> None:
        await self.dispatch("SET", "strkey", "value")
        reply = await self.dispatch("GEOADD", "strkey", "0", "0", "m")
        self.assertEqual(
            reply,
            b"-ERR WRONGTYPE Operation against a key holding the wrong kind of value\r\n",
        )
