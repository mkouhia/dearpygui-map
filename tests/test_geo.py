"""Test geographic functions"""

from dearpygui_map.geo import get_tile_xyz


def test_get_tile_xyz():
    """Correct tile x, y, z values around defined area"""
    bbox = (60.15198, 24.90550, 60.17582, 24.96273)
    zoom_level = 12

    expected = [(2331, 1185, 12), (2331, 1186, 12), (2332, 1185, 12), (2332, 1186, 12)]
    received = list(get_tile_xyz(bbox, zoom_level))

    assert received == expected
