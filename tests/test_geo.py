"""Test geographic functions"""

import pytest

from dearpygui_map.geo import Coordinate


def test_coordinate_repr():
    """Reproduction is as defined"""
    coord_x = 0.8
    coord_y = 0.4

    received = repr(Coordinate(coord_x, coord_y))
    expected = f"Coordinate(x={coord_x}, y={coord_y})"

    assert received == expected


def test_coordinate_equality():
    """Two coordinates with same x, y are equal"""
    first = Coordinate(0.4, 0.3)
    second = Coordinate(0.4, 0.3)

    assert first == second


def test_coordinate_inequality():
    """Two coordinates with different x, y are not equal"""
    first = Coordinate(0.4, 0.3)
    second = Coordinate(0.41, 0.3)

    assert first != second


def test_coordinate_tile_xy():
    """Tile x, y coordinates are expected for Helsinki"""
    coord = Coordinate(x=0.5692783333333333, y=0.28948570416212227)

    expected = (2331, 1185)
    received = coord.tile_xy(zoom=12)

    assert received == expected


def test_coordinate_tile_xy_not_floor():
    """Tile x, y coordinates are not floored"""
    coord = Coordinate(x=0.5692783333333333, y=0.28948570416212227)

    expected = (2331.7640533333333, 1185.7334442480528)
    received = coord.tile_xy(zoom=12, floor_=False)

    assert received == expected


def test_coordinate_latlon():
    """Coordinate to lat/lon conversion works as expected"""
    coord = Coordinate(x=0.5692783333333333, y=0.28948570416212227)

    expected = (60.1641, 24.9402)
    received = coord.latlon()

    assert received == pytest.approx(expected, 1e-8)


def test_coordinate_from_latlon():
    """Construction from latitude/longitude works"""
    received = Coordinate.from_latlon(60.1641, 24.9402)
    expected = Coordinate(x=0.5692783333333333, y=0.28948570416212227)

    assert received == expected


invalid_coords = [
    (60.0, -181.0),
    (60.0, 200.0),
    (88.0, 24.0),
    (-86.0, 24.0),
]


@pytest.mark.parametrize("lat, lon", invalid_coords)
def test_coordinate_from_latlon_out_of_bounds(lat, lon):
    """Out-of bounds latitude/longitude results in error"""
    with pytest.raises(ValueError):
        Coordinate.from_latlon(lat, lon)


def test_coordinate_with_screen_offset():
    """Offset calculation works"""
    coord = Coordinate.from_latlon(60.1641, 24.9402)

    received = coord.with_screen_offset(-350, -250, zoom=12)
    expected = Coordinate.from_latlon(60.20677453949039, 24.820037036132817)

    assert received == expected
