"""52-bit geohash encoding used by Redis sorted-set geospatial commands."""

from __future__ import annotations

import math

BITS = 26
MAX_HASH = (1 << (BITS * 2)) - 1
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0
MIN_LATITUDE = -85.05112878
MAX_LATITUDE = 85.05112878


def validate_coordinates(longitude: float, latitude: float) -> bool:
    return (
        math.isfinite(longitude)
        and math.isfinite(latitude)
        and MIN_LONGITUDE <= longitude <= MAX_LONGITUDE
        and MIN_LATITUDE <= latitude <= MAX_LATITUDE
    )


def encode(longitude: float, latitude: float) -> int:
    """Encode longitude/latitude into the Redis 52-bit interleaved integer."""
    if not validate_coordinates(longitude, latitude):
        raise ValueError("invalid longitude,latitude pair")
    lon_unit = (longitude - MIN_LONGITUDE) / (MAX_LONGITUDE - MIN_LONGITUDE)
    lat_unit = (latitude - MIN_LATITUDE) / (MAX_LATITUDE - MIN_LATITUDE)
    lon_bits = min((1 << BITS) - 1, int(lon_unit * (1 << BITS)))
    lat_bits = min((1 << BITS) - 1, int(lat_unit * (1 << BITS)))
    value = 0
    for bit in range(BITS):
        value = (value << 1) | ((lon_bits >> (BITS - bit - 1)) & 1)
        value = (value << 1) | ((lat_bits >> (BITS - bit - 1)) & 1)
    return value


def decode(value: int) -> tuple[float, float]:
    """Decode a 52-bit integer into the centre longitude/latitude."""
    if not isinstance(value, int) or value < 0 or value > MAX_HASH:
        raise ValueError("geohash must be a 52-bit unsigned integer")
    lon_bits = lat_bits = 0
    for bit in range(BITS):
        lon_bits = (lon_bits << 1) | ((value >> (2 * (BITS - bit - 1) + 1)) & 1)
        lat_bits = (lat_bits << 1) | ((value >> (2 * (BITS - bit - 1))) & 1)
    longitude = MIN_LONGITUDE + (lon_bits + 0.5) * (MAX_LONGITUDE - MIN_LONGITUDE) / (1 << BITS)
    latitude = MIN_LATITUDE + (lat_bits + 0.5) * (MAX_LATITUDE - MIN_LATITUDE) / (1 << BITS)
    return longitude, latitude


encode_geohash = encode
decode_geohash = decode
