"""Geography calculation"""

import itertools
import math
from typing import Iterator


def get_tile_xyz(
    bbox: tuple[float, float, float, float], zoom_level: int
) -> Iterator[tuple[int, int, int]]:
    """Get tile x,y,z descriptors inside bounding box

    Args:
        bbox (tuple[float, float, float, float]): Bounding box limits
            lat_min, lon_min, lat_max, lon_max
        zoom_level (int): Zoom level

    Yields:
        Iterator[tuple[int, int, int]]: tile tuples in bounding box, (x, y, z)
    """
    x_lims = tuple(_lon_to_x(bbox[i], zoom_level) for i in [1, 3])
    y_lims = tuple(_lat_to_y(bbox[i], zoom_level) for i in [0, 2])
    yield from itertools.product(
        range(min(x_lims), max(x_lims) + 1),
        range(min(y_lims), max(y_lims) + 1),
        (zoom_level,),
    )


def _lon_to_x(longitude: float, zoom_level: int) -> int:
    """Convert longitude to tile x coordinate"""
    return math.floor((longitude + 180) / 360 * math.pow(2, zoom_level))


def _lat_to_y(latitude: float, zoom_level: int) -> int:
    """Convert latitude to tile y coordinate"""
    return math.floor(
        (
            1
            - math.log(
                math.tan(latitude * math.pi / 180)
                + 1 / math.cos(latitude * math.pi / 180)
            )
            / math.pi
        )
        / 2
        * math.pow(2, zoom_level)
    )
