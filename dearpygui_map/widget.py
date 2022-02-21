"""Map widget"""

import itertools
from pathlib import Path

import dearpygui.dearpygui as dpg
from dearpygui_map.geo import get_tile_xyz_center, point_to_xy
from dearpygui_map.io import TileHandler
from dearpygui_map.tile_source import OpenStreetMap, TileSpec


class MapWidget:
    """Map widget for Dear PyGui"""

    def __init__(
        self, width: int, height: int, center: tuple[float, float], zoom_level: int
    ):
        """Initialize map widget

        Args:
            width (int): widget width
            height (int): widget height
        """
        self.width = width
        self.height = height

        self.tile_manager = TileManager(
            width=width, height=height, center=center, zoom_level=zoom_level
        )

        self.widget: int | str = None
        self.global_handler: int | str = None

        self._left_mouse_pressed: bool = False

    def __enter__(self) -> int | str:
        """Enter context manager

        Returns:
            int | str: Dear PyGui drawlist, with map content
        """
        with dpg.handler_registry() as self.global_handler:
            dpg.add_mouse_click_handler(callback=self._mouse_click_cb)
            dpg.add_mouse_drag_handler(callback=self._mouse_drag_cb)
            dpg.add_mouse_release_handler(callback=self._mouse_release_cb)

        with dpg.drawlist(width=self.width, height=self.height) as self.widget:
            dpg.draw_rectangle((0, 0), (self.width, self.height))
            self.tile_manager.draw_layer()

        dpg.push_container_stack(self.widget)
        return self.widget

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Exit context manager

        Args:
            exc_type (_type_): _description_
            exc_value (_type_): _description_
            exc_tb (_type_): _description_
        """
        del exc_type, exc_value, exc_tb  # unused
        dpg.pop_container_stack()

    def _mouse_click_cb(self, sender: int | str, app_data: int) -> None:
        """Callback on mouse click"""
        if dpg.is_item_left_clicked(self.widget):
            self._left_mouse_pressed = True

    def _mouse_release_cb(self, sender: int | str, app_data: int) -> None:
        """Callback on mouse release"""
        self._left_mouse_pressed = False
        self.tile_manager.finish_drag()

    def _mouse_drag_cb(self, sender: int | str, app_data: list[int | float]) -> None:
        """Callback on mouse drag"""
        _, delta_x, delta_y = app_data
        if self._left_mouse_pressed:
            self.tile_manager.drag_layer(delta_x, delta_y)


class TileManager:

    """Tile manager for MapWidget"""

    def __init__(
        self, width: int, height: int, center: tuple[float, float], zoom_level: int
    ) -> None:
        self.width = width
        self.height = height
        self.center = center
        self.zoom_level = zoom_level

        self.tile_layer_id: int | str = None
        self.tiles: list["MapTile"] = []

        self.last_drag: tuple[float, float] = None

    def draw_layer(self):
        """Draw tiles"""
        tile_xyz_tuples = get_tile_xyz_center(
            self.center,
            self.zoom_level,
            (self.width, self.height),
            OpenStreetMap.tile_size,
        )
        tile_specs = itertools.starmap(OpenStreetMap.to_tile_spec, tile_xyz_tuples)

        downloader = TileHandler(
            tile_specs, self.draw_tile, thread_count=OpenStreetMap.thread_limit
        )
        downloader.start()

        self.tile_layer_id = dpg.add_draw_layer(label="tiles")

    def draw_tile(self, tile_spec: TileSpec):
        """Draw tile on canvas"""
        # TODO what if scrolling happens while waiting for tile?
        # Suggestion: make a canvas object that is moved around, tile coordinates refer to canvas
        x_center, y_center = point_to_xy(
            self.center[0], self.center[1], self.zoom_level
        )
        x_canvas, y_canvas = tile_spec.canvas_coordinates(
            -x_center * tile_spec.tile_size[0] + self.width / 2,
            -y_center * tile_spec.tile_size[1] + self.height / 2,
        )
        tile = MapTile(tile_spec.local_storage_path, x_canvas, y_canvas)
        tile.draw_image(parent=self.tile_layer_id)
        self.tiles.append(tile)

    def drag_layer(self, delta_x: float, delta_y: float):
        """Move layer to new position

        Args:
            delta_x (float): Change in x position
            delta_y (float): Change in y position
        """
        for map_tile in self.tiles:
            map_tile.drag_image(delta_x, delta_y)
        self.last_drag = (delta_x, delta_y)

    def finish_drag(self):
        """Finish dragging; update tile positions"""
        if self.last_drag is None:
            return

        for map_tile in self.tiles:
            map_tile.finish_drag(*self.last_drag)
        self.last_drag = None


class MapTile:

    """Map tile"""

    def __init__(self, file: Path, x_canvas: int, y_canvas: int) -> None:
        self.file = file
        self.width = 256
        self.height = 256
        self.x_canvas = x_canvas
        self.y_canvas = y_canvas

        self.image_tag: int | str = None

    def draw_image(self, parent: int | str):
        """Draw tile"""
        width, height, _, data = dpg.load_image(str(self.file))
        with dpg.texture_registry():
            texture = dpg.add_static_texture(width, height, data)
        self.image_tag = dpg.draw_image(
            texture,
            (self.x_canvas, self.y_canvas),
            (self.x_canvas + self.width, self.y_canvas + self.height),
            parent=parent,
        )

    def drag_image(self, delta_x: float, delta_y: float):
        """Move tile"""
        dpg.configure_item(
            self.image_tag,
            pmin=(self.x_canvas + delta_x, self.y_canvas + delta_y),
            pmax=(
                self.x_canvas + self.width + delta_x,
                self.y_canvas + self.height + delta_y,
            ),
        )

    def finish_drag(self, delta_x, delta_y):
        """Finish dragging; reset tile X and Y position

        Args:
            delta_x (float): Final change in X position
            delta_y (float): Final change in Y position
        """
        self.x_canvas += delta_x
        self.y_canvas += delta_y


map_widget = MapWidget  # pylint: disable=invalid-name


def add_map_widget(
    width: int, height: int, center: tuple[float, float], zoom_level: int
) -> int | str:
    """Add map widget"""
    with MapWidget(
        width=width, height=height, center=center, zoom_level=zoom_level
    ) as _widget:
        pass
    return _widget


def configure_tile_layer() -> int | str:
    """Configure tile layer"""
    ...
