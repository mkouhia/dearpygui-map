"""Map widget"""

from contextlib import contextmanager

import dearpygui.dearpygui as dpg


@contextmanager
def map_widget(width: int, height: int) -> int | str:
    """Map widget for Dear PyGui

    Args:
        width (int): widget width
        height (int): widget height

    Yields:
        int | str: Dear PyGui drawlist, with map content
    """
    try:
        with dpg.drawlist(width=width, height=height) as widget:
            dpg.draw_rectangle((0,0), (width, height))
        dpg.push_container_stack(widget)
        yield widget
    finally:
        dpg.pop_container_stack()

def add_tile_source() -> int | str:
    """Add tile source"""
    with dpg.draw_layer(label="tiles"):
        for x in [0,1]:
            for y in [0,1]:
                im = _add_image(f'examples/sample_tiles/{x}-{y}.png')
                dpg.draw_image(im, (256*x, 256*y), (256*(x+1), 256*(y+1)))

def _add_image(file: str, tag: int | str = 0) -> int | str:
    width, height, _, data = dpg.load_image(file)
    with dpg.texture_registry():
        texture_tag = dpg.add_static_texture(width, height, data, tag=tag)
    return texture_tag
