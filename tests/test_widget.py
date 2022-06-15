"""Map widget tests"""

import itertools

import pytest
from pytest_mock import MockerFixture

from dearpygui_map.geo import Coordinate
from dearpygui_map.tile_source import OpenStreetMap, TileServer, TileSpec
from dearpygui_map.widget import MapWidget, TileManager


@pytest.fixture(name="map_widget")
def fx_map_widget() -> MapWidget:
    """Fixture map widget initially centered in Helsinki"""
    center = (60.1641, 24.9402)
    return MapWidget(700, 500, center, 12, OpenStreetMap)


@pytest.fixture(name="tile_manager")
def fx_tile_manager() -> TileManager:
    """Fixture: tile manager initially centered in Helsinki"""
    center = Coordinate.from_latlon(60.1641, 24.9402)
    origin = center.with_screen_offset(-350, -250, zoom=12)
    return TileManager(origin, 700, 500, 12, OpenStreetMap)


def test_widget_zoom_on_point_origin_changes(map_widget: MapWidget):
    """When zooming, origin changes if canvas_position is not 0,0"""
    origin_0 = map_widget.origin
    map_widget.zoom_on_point((200, 200), 13)

    assert map_widget.origin != origin_0


def test_widget_zoom_on_point_origins_equal(map_widget: MapWidget):
    """When zooming, new origin is same for widget and tile manager"""
    map_widget.zoom_on_point((200, 200), 13)

    assert map_widget.origin == map_widget.tile_manager.origin


def test_widget_get_screen_coordinates(map_widget: MapWidget):
    """Query point on canvas to get coordinate"""
    received = map_widget.get_coordinate(350, 250)
    expected = Coordinate.from_latlon(60.1641, 24.9402)

    assert received == expected


def test_widget_drag_canvas(map_widget: MapWidget, mocker: MockerFixture):
    """Last drag attribute is updated and tile layer is also dragged"""
    tilemgr_cls = mocker.patch("dearpygui_map.widget.TileManager")
    drag = (100, 100)
    # pylint: disable=protected-access
    map_widget._drag_canvas(*drag)

    assert map_widget.last_drag == drag
    assert tilemgr_cls.drag_layer.called_with(*drag)


def test_widget_finish_drag(map_widget: MapWidget, mocker: MockerFixture):
    """Last drag is reset, origin is moved and tile layer is called

    Drag so that previous center point should be found at origin
    """
    tilemgr_cls = mocker.patch("dearpygui_map.widget.TileManager")
    drag = (-350, -250)  # Drag so that
    # pylint: disable=protected-access
    map_widget._drag_canvas(*drag)
    map_widget._finish_drag()

    assert map_widget.last_drag == (0, 0)
    assert map_widget.origin == Coordinate.from_latlon(60.1641, 24.9402)
    assert tilemgr_cls.finish_drag.called_once


def test_center_point_init(tile_manager: TileManager):
    """Check that zoom level and offset are properly set"""
    assert tile_manager.zoom_level == 12
    assert tile_manager.origin_offset == (-596581.5976533333, -303297.7617275015)


def test_center_point_move(tile_manager: TileManager):
    """Check that zoom level and offset are properly set"""
    zoom_level = 13
    center = Coordinate.from_latlon(59.3315, 18.0560)
    origin = center.with_screen_offset(-350, -250, zoom=zoom_level)

    tile_manager.set_origin(origin, zoom_level)

    assert tile_manager.zoom_level == zoom_level
    assert tile_manager.origin_offset == (-1153409.8236444446, -616473.2951275909)


def test_manager_initial_tiles(tile_manager: TileManager):
    """Initial tiles are correct"""
    expected_coord_range = [(2328, 1182), (2335, 1188)]

    # pylint: disable=protected-access
    received = list(tile_manager._required_tiles_for_view())
    expected = _coords_to_specs(
        tile_manager.tile_server,
        expected_coord_range,
        tile_manager.zoom_level,
    )

    assert received == expected


def test_manager_tiles_after_dragging(tile_manager: TileManager):
    """Required tile range changes correctly

    Dragging towards origin (upper left) should reveal more tiles frow
    lower right corner.
    """
    expected_coord_range = [(2330, 1184), (2337, 1190)]

    # Drag to
    tile_manager.drag_layer(-512, -512)

    # pylint: disable=protected-access
    received = list(tile_manager._required_tiles_for_view())
    expected = _coords_to_specs(
        tile_manager.tile_server,
        expected_coord_range,
        tile_manager.zoom_level,
    )

    assert received == expected


def _coords_to_specs(
    tile_server: TileServer, expected_coord_range: list[tuple], zoom: int
) -> list[TileSpec]:
    min_x, min_y = expected_coord_range[0]
    max_x, max_y = expected_coord_range[1]
    tiles = itertools.product(
        range(min_x, max_x + 1),
        range(min_y, max_y + 1),
        (zoom,),
    )
    return list(itertools.starmap(tile_server.to_tile_spec, tiles))


def test_manager_origin_change_after_drag(tile_manager: TileManager):
    """Origin coordinate is correct after dragging"""

    origin_0 = tile_manager.origin
    tile_manager.drag_layer(-512, -512)
    tile_manager.finish_drag()

    received = tile_manager.origin
    expected = origin_0.with_screen_offset(512, 512, zoom=tile_manager.zoom_level)

    assert received == expected


def test_manager_origin_same_after_zoom(tile_manager: TileManager):
    """When zoom changes, origin stays"""
    origin_0 = tile_manager.origin
    tile_manager.set_origin(origin_0, tile_manager.zoom_level + 1)

    assert tile_manager.origin == origin_0
