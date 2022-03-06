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


def test_tile_urls():
    """Tile urls are generated properly"""
    bbox = (60.15198, 24.90550, 60.17582, 24.96273)
    zoom_level = 12

    test_provider = TileServer(
        name="test provider",
        base_url="http://{subdomain}.tile.test_provider.org/{z}/{x}/{y}.png",
        subdomains=["a"],
        max_zoom_level=19,
        tile_size=(256, 256),
    )

    expected_locs = [
        (2331, 1185, 12),
        (2331, 1186, 12),
        (2332, 1185, 12),
        (2332, 1186, 12),
    ]
    expected = [
        TileSpec(
            tile_x=loc[0],
            tile_y=loc[1],
            zoom_level=12,
            tile_size=test_provider.tile_size,
            base_url=test_provider.base_url,
            subdomains=test_provider.subdomains,
        )
        for loc in expected_locs
    ]
    received = list(test_provider.get_tile_specs(bbox, zoom_level))

    assert received == expected
