"""Map widget"""

import itertools
import math
from pathlib import Path

import dearpygui.dearpygui as dpg
from dearpygui_map.geo import point_to_xy
from dearpygui_map.io import TileHandler
from dearpygui_map.tile_source import TileServer, TileSpec


class MapWidget:
    """Map widget for Dear PyGui"""

    def __init__(
        self,
        width: int,
        height: int,
        center: tuple[float, float],
        zoom_level: int,
        tile_server: TileServer,
    ):
        """Initialize map widget

        Args:
            width (int): widget width
            height (int): widget height
        """
        self.width = width
        self.height = height

        self.tile_manager = TileManager(
            width=width,
            height=height,
            center=center,
            zoom_level=zoom_level,
            tile_server=tile_server,
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
            self.tile_manager.add_tile_layer()

        dpg.push_container_stack(self.widget)

        self.tile_manager.update_tile_layer()
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
        self,
        width: int,
        height: int,
        center: tuple[float, float],
        zoom_level: int,
        tile_server: TileServer,
    ) -> None:
        self.viewport_size = width, height
        self.zoom_level = zoom_level
        self.tile_server = tile_server

        self.layer_extent_pixels: tuple[tuple[int, int], tuple[int, int]] = None
        self.tile_draw_node_id: int | str = None
        self.tiles: list[TileSpec] = []

        self.last_drag: tuple[float, float] = (0.0, 0.0)
        self.origin_offset = (0, 0)

        self.center_point(center, zoom_level)

    def center_point(self, center: tuple[float, float], zoom_level: int):
        """Center point on widget

        Set self.zoom_level and self.origin_offset

        Args:
            center (tuple[float, float]): Center point: latitude, longitude
            zoom_level (int): Zoom level
        """
        center_xy = point_to_xy(center[0], center[1], zoom_level)

        self.zoom_level = zoom_level
        self.origin_offset: tuple[float, float] = tuple(
            -center_xy[i] * self.tile_server.tile_size[i]
            + self.viewport_size[i] / 2
            + self.last_drag[i]
            for i in range(2)
        )

    def add_tile_layer(self):
        """Add Dear PyGui draw layer for map tiles"""
        tile_layer = dpg.add_draw_layer(label="tiles")
        self.tile_draw_node_id = dpg.add_draw_node(parent=tile_layer)

    def update_tile_layer(self):
        """Update tile layer, if there are too few tiles displayed"""

        dpg.apply_transform(
            self.tile_draw_node_id,
            dpg.create_translation_matrix(
                [sum(i) for i in zip(self.origin_offset, self.last_drag)]
            ),
        )

        if (
            self.layer_extent_pixels is not None
            and self.layer_extent_pixels[0][0] + self.last_drag[0] < 0
            and self.layer_extent_pixels[0][1] + self.last_drag[1] < 0
            and self.layer_extent_pixels[1][0] + self.last_drag[0]
            > self.viewport_size[0]
            and self.layer_extent_pixels[1][1] + self.last_drag[1]
            > self.viewport_size[1]
        ):
            # TODO add some margin
            return

        # TODO add some margin - download more tiles than should be absolutely required
        min_xy, max_xy = self.visible_tile_range
        self.layer_extent_pixels = (
            self._to_canvas_pixels(*min_xy),
            self._to_canvas_pixels(max_xy[0] + 1, max_xy[1] + 1),
        )

        tile_xyz_tuples = itertools.product(
            range(min_xy[0], max_xy[0] + 1),
            range(min_xy[1], max_xy[1] + 1),
            (self.zoom_level,),
        )
        tile_specs = itertools.starmap(self.tile_server.to_tile_spec, tile_xyz_tuples)
        tile_specs = filter(lambda ts: ts not in self.tiles, tile_specs)

        # TODO purge those tiles from draw layer that are too far away to display

        # FIXME make tile handler persistent (do not spawn new handlers whenever scrolling)
        downloader = TileHandler(
            tile_specs, self.draw_tile, thread_count=self.tile_server.thread_limit
        )
        downloader.start()

    @property
    def visible_tile_range(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """Calculate which tiles should be visible

        Compute given current origin offset, drag and zoom level

        Returns:
            tuple[tuple[int, int], tuple[int, int]]: tile (x_min, y_min), (x_max, y_max)
        """
        return tuple(
            tuple(
                math.floor(
                    (
                        -(self.origin_offset[i] + self.last_drag[i])
                        + self.viewport_size[i] * is_max
                    )
                    / self.tile_server.tile_size[i]
                )
                for i in range(2)
            )
            for is_max in [0, 1]
        )

    def _to_canvas_pixels(self, tile_x: int, tile_y: int) -> tuple[int, int]:
        """Convert x, y coordinates to canvas pixel coordinates

        Args:
            tile_x (int): Tile x coordinate
            tile_y (int): Tile y coordinate

        Returns:
            tuple[int, int]: x, y in canvas pixels
        """
        return (
            tile_x * self.tile_server.tile_size[0] + self.origin_offset[0],
            tile_y * self.tile_server.tile_size[1] + self.origin_offset[1],
        )

    def draw_tile(self, tile_spec: TileSpec):
        """Draw tile on canvas"""
        if tile_spec in self.tiles:
            return
        tile = MapTile(tile_spec.local_storage_path, *tile_spec.canvas_coordinates())

        tile.draw_image(parent=self.tile_draw_node_id)
        self.tiles.append(tile_spec)

    def drag_layer(self, delta_x: float, delta_y: float):
        """Move layer to new position

        Args:
            delta_x (float): Change in x position
            delta_y (float): Change in y position
        """
        self.last_drag = (delta_x, delta_y)
        self.update_tile_layer()

    def finish_drag(self):
        """Finish dragging; update tile positions"""
        if self.last_drag == (0.0, 0.0):
            return

        self.layer_extent_pixels = tuple(
            tuple(min_or_max[i] + self.last_drag[i] for i in range(2))
            for min_or_max in self.layer_extent_pixels
        )

        self.origin_offset = tuple(
            sum(i) for i in zip(self.origin_offset, self.last_drag)
        )
        self.last_drag = (0.0, 0.0)


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


map_widget = MapWidget  # pylint: disable=invalid-name


def add_map_widget(
    width: int,
    height: int,
    center: tuple[float, float],
    zoom_level: int,
    tile_server: TileServer,
) -> int | str:
    """Add map widget"""
    with MapWidget(
        width=width,
        height=height,
        center=center,
        zoom_level=zoom_level,
        tile_server=tile_server,
    ) as _widget:
        pass
    return _widget


def configure_tile_layer() -> int | str:
    """Configure tile layer"""
    ...
