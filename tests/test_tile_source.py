"""Test tile sources"""

from dearpygui_map.tile_source import TileServer, TileSpec


def test_to_tile_spec():
    """Test tile specification generation"""
    tile_x, tile_y, zoom_level = (2331, 1185, 12)
    tile_size = (256, 256)
    base_url = "test_url"
    subdomains = ["foo"]

    test_provider = TileServer("test_name", base_url, subdomains, 1, tile_size)

    expected = TileSpec(tile_x, tile_y, zoom_level, base_url, subdomains, tile_size)
    received = test_provider.to_tile_spec(tile_x, tile_y, zoom_level)

    assert received == expected
