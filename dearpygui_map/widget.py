"""Map widget"""

import itertools
import sys
from typing import Iterator

import dearpygui.dearpygui as dpg
from dearpygui_map.geo import Coordinate
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
            width (int): Widget width
            height (int): Widget height
            center (tuple[float, float]): Center point coordinates:
              latitude, longitude
            zoom_level (int): Tile map zoom level
            tile_server (TileServer): Tile supplier, from
              dearpygui_map.tile_source
        """
        self.width = width
        self.height = height

        self.origin = Coordinate.from_latlon(*center).with_screen_offset(
            -width / 2, -height / 2, zoom=zoom_level, resolution=tile_server.tile_size
        )
        self.zoom_level = zoom_level

        self.tile_manager = TileManager(
            origin=self.origin,
            width=width,
            height=height,
            zoom_level=zoom_level,
            tile_server=tile_server,
        )

        self.widget: int | str = None
        self.global_handler: int | str = None

        self._left_mouse_pressed: bool = False
        self.last_drag: tuple[float, float] = (0.0, 0.0)

    def insert_widget(self) -> int | str:
        """Draw widget, insert Dear PyGui code

        Returns:
            int | str: Dear PyGui drawlist, with map content
        """
        with dpg.handler_registry() as self.global_handler:
            dpg.add_mouse_click_handler(callback=self._mouse_click_cb)
            dpg.add_mouse_drag_handler(callback=self._mouse_drag_cb)
            dpg.add_mouse_release_handler(callback=self._mouse_release_cb)
            dpg.add_mouse_wheel_handler(callback=self._mouse_wheel_cb)

        with dpg.drawlist(width=self.width, height=self.height) as self.widget:
            dpg.draw_rectangle((0, 0), (self.width, self.height))
            self.tile_manager.add_tile_layer()
            self.tile_manager.add_tile_license()

        self.tile_manager.draw_layer()
        return self.widget

    def draw_layers(self):
        """Redraw tile layer, for example after dragging operation"""
        self.tile_manager.draw_layer()

    def zoom_on_point(self, canvas_position: tuple[float, float], zoom_level: int):
        """Zoom in/out, while keeping focus on given point

        NOTE: it is necessary to call `self.refresh_layers` after this.

        Args:
            canvas_position (tuple[float, float]): X, y point on canvas,
              which retains its screen position on zoom change.
            zoom_level (int): New zoom level. If zoom level is less than
              zero or greater than tile_server.max_zoom_level,
              do nothing.
        """
        if zoom_level < 0 or zoom_level > self.tile_manager.tile_server.max_zoom_level:
            return

        focus_position = self.origin.with_screen_offset(
            *canvas_position,
            zoom=self.zoom_level,  # old zoom level
            resolution=self.tile_manager.tile_server.tile_size,
        )

        self.origin = focus_position.with_screen_offset(
            *[-i for i in canvas_position],
            zoom=zoom_level,  # new zoom level
            resolution=self.tile_manager.tile_server.tile_size,
        )

        self.zoom_level = zoom_level

        self.tile_manager.set_origin(self.origin, zoom_level)

    def get_coordinate(
        self,
        canvas_x: float,
        canvas_y: float,
    ) -> Coordinate:
        """Get lat, lon coordinates for a x, y point on canvas

        Args:
            canvas_x (float): Point x coordinate on canvas
            canvas_y (float): Point y coordinate on canvas

        Returns:
            Coordinate: Location for the point on canvas
        """
        return self.origin.with_screen_offset(
            canvas_x,
            canvas_y,
            zoom=self.zoom_level,
            resolution=self.tile_manager.tile_server.tile_size,
        )

    def _drag_canvas(self, delta_x: float, delta_y: float):
        """Move canvas by dragging

        NOTE: it is necessary to call `self.refresh_layers` after this,
        and `self._finish_drag`, when dragging is released.

        Args:
            delta_x (float): Change in x position
            delta_y (float): Change in y position
        """
        self.last_drag = (delta_x, delta_y)
        self.tile_manager.drag_layer(delta_x, delta_y)

    def _finish_drag(self):
        """Finish dragging; update tile positions"""
        if self.last_drag == (0.0, 0.0):
            return

        self.origin = self.origin.with_screen_offset(
            *[-i for i in self.last_drag],
            zoom=self.zoom_level,
        )
        self.last_drag = (0.0, 0.0)

        self.tile_manager.finish_drag()

    def _mouse_click_cb(self, sender: int | str, app_data: int) -> None:
        """Callback on mouse click"""
        if dpg.is_item_left_clicked(self.widget):
            self._left_mouse_pressed = True

    def _mouse_release_cb(self, sender: int | str, app_data: int) -> None:
        """Callback on mouse release"""
        self._left_mouse_pressed = False
        self._finish_drag()

    def _mouse_drag_cb(self, sender: int | str, app_data: list[int | float]) -> None:
        """Callback on mouse drag"""
        _, delta_x, delta_y = app_data
        if self._left_mouse_pressed:
            self._drag_canvas(delta_x, delta_y)
            self.draw_layers()

    def _mouse_wheel_cb(self, sender: int | str, app_data: int) -> None:
        """Callback on mouse wheel"""
        del sender  # unused
        delta_zoom = app_data
        canvas_pos = dpg.get_drawing_mouse_pos()
        self.zoom_on_point(canvas_pos, self.zoom_level + delta_zoom)
        self.draw_layers()


class TileManager:

    """Tile manager for MapWidget"""

    def __init__(
        self,
        origin: Coordinate,
        width: int,
        height: int,
        zoom_level: int,
        tile_server: TileServer,
    ) -> None:
        self.viewport_size = width, height
        self.origin = origin
        self.zoom_level = zoom_level
        self.tile_server = tile_server

        self.tile_draw_node_id: int | str = None
        self.tiles: list[TileSpec] = []

        self.last_drag: tuple[float, float] = (0.0, 0.0)
        self.origin_offset = (0, 0)

        self.set_origin(origin, zoom_level)

    def set_origin(self, origin: Coordinate, zoom_level: int):
        """Set widget map origin position

        Set self.zoom_level and self.origin_offset

        Args:
            origin (Coordinate): Origin point
            zoom_level (int): Zoom level
        """
        self.origin = origin
        origin_xy = origin.tile_xy(zoom_level, floor_=False)

        self.zoom_level = zoom_level
        self.origin_offset: tuple[float, float] = tuple(
            -origin_xy[i] * self.tile_server.tile_size[i] + self.last_drag[i]
            for i in range(2)
        )

    def add_tile_layer(self):
        """Add Dear PyGui draw layer for map tiles"""
        tile_layer = dpg.add_draw_layer(label="tiles")
        self.tile_draw_node_id = dpg.add_draw_node(parent=tile_layer)

    def add_tile_license(self):
        """Add tile lisence as a new layer"""
        width_guess = len(self.tile_server.license_text) * 7 + 4

        x_text = max(0, self.viewport_size[0] - width_guess)
        y_text = max(0, self.viewport_size[1] - 13)

        with dpg.draw_layer(label="license"):
            dpg.draw_rectangle(
                (max(0, x_text - 4), y_text),
                self.viewport_size,
                fill=(255, 255, 255, 100),
                color=(255, 255, 255, 100),
            )
            dpg.draw_text(
                (x_text, y_text),
                color=(0, 0, 0, 255),
                text=self.tile_server.license_text,
                size=13,
            )

    def draw_layer(self):
        """Update tile layer, if there are too few tiles displayed"""
        dpg.apply_transform(
            self.tile_draw_node_id,
            dpg.create_translation_matrix(
                [sum(i) for i in zip(self.origin_offset, self.last_drag)]
            ),
        )

        missing_tiles = list(self._required_tiles_for_view())

        if len(missing_tiles) == 0:
            return

        # TODO purge those tiles from draw layer that are too far away to display

        # FIXME make tile handler persistent (do not spawn new handlers whenever scrolling)
        downloader = TileHandler(
            missing_tiles, self.draw_tile, thread_count=self.tile_server.thread_limit
        )
        downloader.start()

    def _required_tiles_for_view(self) -> Iterator[TileSpec]:
        """Get tiles that need to be downloaded for a view

        Check that which tiles are already in `self.tiles`, return specs for
        the others that are not.

        Yields:
            TileSpec: Tile specification
        """
        # TODO add some margin - download more tiles than should be absolutely required
        tile_xyz_tuples = self._get_visible_tiles()

        tile_specs = itertools.starmap(self.tile_server.to_tile_spec, tile_xyz_tuples)
        tile_specs = filter(lambda ts: ts not in self.tiles, tile_specs)

        yield from tile_specs

    def _get_visible_tiles(self) -> Iterator[tuple[int, int, int]]:
        """Calculate which tiles should be visible

        Compute given current origin offset, drag and zoom level

        Yields:
            tuple[int, int, int]: tile (x, y, z) values
        """
        origin_offset = tuple(-i for i in self.last_drag)
        min_point = self.origin.with_screen_offset(
            *origin_offset,
            zoom=self.zoom_level,
        )
        max_point = min_point.with_screen_offset(
            *self.viewport_size, zoom=self.zoom_level
        )

        min_xy = min_point.tile_xy(self.zoom_level)
        max_xy = max_point.tile_xy(self.zoom_level)

        yield from itertools.product(
            range(min_xy[0], max_xy[0] + 1),
            range(min_xy[1], max_xy[1] + 1),
            (self.zoom_level,),
        )

        return tuple(p.tile_xy(zoom=self.zoom_level) for p in [min_point, max_point])

    def draw_tile(self, tile_spec: TileSpec):
        """Draw tile on canvas

        If image loading fails, draw gray area. Otherwise, add tile
        spec to self.tiles
        """
        if tile_spec in self.tiles:
            return

        tile = MapTile(tile_spec)
        if tile.draw_image(parent=self.tile_draw_node_id):
            self.tiles.append(tile_spec)

    def drag_layer(self, delta_x: float, delta_y: float):
        """Move layer to new position

        NOTE: after calling this, one must redraw contents with
        `TileManager.draw_layer`. Dragging action is finished with
        `TileManager.finish_drag`, after mouse button is released.

        Args:
            delta_x (float): Change in x position
            delta_y (float): Change in y position
        """
        self.last_drag = (delta_x, delta_y)

    def finish_drag(self):
        """Finish dragging; update tile positions"""
        if self.last_drag == (0.0, 0.0):
            return

        self.origin_offset = tuple(
            sum(i) for i in zip(self.origin_offset, self.last_drag)
        )

        origin_offset = tuple(-i for i in self.last_drag)
        self.origin = self.origin.with_screen_offset(
            *origin_offset,
            zoom=self.zoom_level,
        )
        self.last_drag = (0.0, 0.0)


class MapTile:

    """Map tile"""

    def __init__(self, tile_spec: TileSpec):
        self.file = tile_spec.local_storage_path
        self.x_canvas, self.y_canvas = tile_spec.canvas_coordinates()
        self.width, self.height = tile_spec.tile_size
        self.tile_spec = tile_spec

        self.image_tag = None

    def draw_image(self, parent: int | str) -> bool:
        """Draw tile

        Place tile on canvas. If image loading fails, draw gray area.

        Returns:
            bool: True if image loading failed, False otherwise
        """
        pmin = (self.x_canvas, self.y_canvas)
        pmax = (self.x_canvas + self.width, self.y_canvas + self.height)

        dpg_image = dpg.load_image(str(self.file))
        if dpg_image is None:
            dpg.draw_rectangle(pmin, pmax, fill=(128, 128, 128, 255), parent=parent)
            return False

        width, height, _, data = dpg_image
        try:
            with dpg.texture_registry():
                texture = dpg.add_static_texture(width, height, data)
        except Exception as err:  # pylint: disable=broad-except
            sys.stderr.write("Could not add texture - ", err)

        self.image_tag = dpg.draw_image(
            texture,
            pmin,
            pmax,
            parent=parent,
        )
        return True


def add_map_widget(
    width: int,
    height: int,
    center: tuple[float, float],
    zoom_level: int,
    tile_server: TileServer,
) -> int | str:
    """Add map widget
    
    Args:
        width (int): Widget width
        height (int): Widget height
        center (tuple[float, float]): Center point coordinates:
            latitude, longitude
        zoom_level (int): Tile map zoom level
        tile_server (TileServer): Tile supplier, from
            dearpygui_map.tile_source
    """
    map_widget = MapWidget(
        width=width,
        height=height,
        center=center,
        zoom_level=zoom_level,
        tile_server=tile_server,
    )
    return map_widget.insert_widget()
