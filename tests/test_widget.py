"""Map widget tests"""

import pytest

from dearpygui_map.tile_source import OpenStreetMap
from dearpygui_map.widget import TileManager


@pytest.fixture(name="tile_manager")
def fx_tile_manager() -> TileManager:
    """Fixture: tile manager initially centered in Helsinki"""
    return TileManager(700, 500, (60.1641, 24.9402), 12, OpenStreetMap)


def test_center_point_init(tile_manager: TileManager):
    """Check that zoom level and offset are properly set"""
    assert tile_manager.zoom_level == 12
    assert tile_manager.origin_offset == (-596581.5976533333, -303297.7617275015)


def test_center_point_move(tile_manager: TileManager):
    """Check that zoom level and offset are properly set"""
    center, zoom_level = (59.3315, 18.0560), 13

    tile_manager.center_point(center, zoom_level)

    assert tile_manager.zoom_level == zoom_level
    assert tile_manager.origin_offset == (-1153409.8236444446, -616473.2951275909)


def test_visible_tile_range(tile_manager: TileManager):
    """Check that correct min/max tiles are found"""
    expected = ((2330, 1184), (2333, 1186))
    received = tile_manager.visible_tile_range
    print(received)

    assert received == expected
