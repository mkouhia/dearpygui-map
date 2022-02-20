"""Map widget"""


import dearpygui.dearpygui as dpg


class MapWidget:
    """Map widget for Dear PyGui"""

    def __init__(self, width: int, height: int):
        """Initialize map widget

        Args:
            width (int): widget width
            height (int): widget height
        """
        self.width = width
        self.height = height

        self.tile_manager = TileManager(width=width, height=height)

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
        self.tile_manager.tile_layer_id = self._get_tile_layer()
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

    def _get_tile_layer(self) -> int | str:
        layer_ids = list(
            filter(
                lambda i: dpg.get_item_type(i) == "mvAppItemType::mvDrawLayer"
                and dpg.get_item_label(i) == "tiles",
                dpg.get_item_children(self.widget, slot=2),
            )
        )
        if len(layer_ids) != 1:
            raise UserWarning(
                "No tile source found! Use `add_tile_source` within MapWidget."
            )

        return layer_ids[0]


class TileManager:

    """Tile manager for MapWidget"""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

        self.tile_layer_id: int | str = None
        self.tiles: list["MapTile"] = []

        self.last_drag: tuple[float, float] = None

    def draw_layer(self):
        """Draw tiles"""
        with dpg.draw_layer(label="tiles"):
            for x_index in [0, 1]:
                for y_index in [0, 1]:
                    tile = MapTile(
                        f"examples/sample_tiles/{x_index}-{y_index}.png",
                        256 * x_index,
                        256 * y_index,
                    )
                    tile.draw_image()
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

    def __init__(self, file: str, x_canvas, y_canvas) -> None:
        self.file = file
        self.width = 256
        self.height = 256
        self.x_canvas = x_canvas
        self.y_canvas = y_canvas

        self.image_tag: int | str = None

    def draw_image(self):
        """Draw tile"""
        width, height, _, data = dpg.load_image(self.file)
        with dpg.texture_registry():
            texture = dpg.add_static_texture(width, height, data)
        self.image_tag = dpg.draw_image(
            texture,
            (self.x_canvas, self.y_canvas),
            (self.x_canvas + self.width, self.y_canvas + self.height),
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


def add_map_widget(width: int, height: int) -> int | str:
    """Add map widget"""
    with MapWidget(width=width, height=height) as _widget:
        pass
    return _widget


def configure_tile_layer() -> int | str:
    """Configure tile layer"""
    ...
