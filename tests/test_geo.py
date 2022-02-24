"""Test geographic functions"""

from dearpygui_map.geo import (
    get_tile_xyz_bbox,
    get_tile_xyz_center,
    point_to_xy,
)


def test_point_to_xy():
    """Test point to x,y coordinate conversion"""
    latitude, longitude = (60.1641, 24.9402)
    zoom_level = 12

    expected = (2331.7640533333333, 1185.7334442480528)
    received = point_to_xy(latitude, longitude, zoom_level)

    assert received == expected


def test_get_tile_xyz_center():
    """Correct tile x, y, z values when querying by center and size"""
    center = (60.1641, 24.9402)
    zoom_level = 12
    window_size = (300, 300)
    tile_size = (256, 256)

    expected = [(2331, 1185, 12), (2331, 1186, 12), (2332, 1185, 12), (2332, 1186, 12)]
    received = list(get_tile_xyz_center(center, zoom_level, window_size, tile_size))

    assert received == expected


def test_get_tile_xyz_bbox():
    """Correct tile x, y, z values around defined area"""
    bbox = (60.15198, 24.90550, 60.17582, 24.96273)
    zoom_level = 12

    expected = [(2331, 1185, 12), (2331, 1186, 12), (2332, 1185, 12), (2332, 1186, 12)]
    received = list(get_tile_xyz_bbox(bbox, zoom_level))

    assert received == expected
