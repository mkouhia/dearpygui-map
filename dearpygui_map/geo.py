"""Geography calculation"""

import itertools
import math
from typing import Iterator


def get_tile_xyz_center(
    center: tuple[float, float],
    zoom_level: int,
    window_size: tuple[int, int],
    tile_size: tuple[int, int],
) -> Iterator[tuple[int, int, int]]:
    """Get tile x,y,z descriptors by center and output image size

    Args:
        center (tuple[float, float]): Image center coordinate: lat, lon
        zoom_level (int): Zoom level
        window_size (tuple[int, int]): Window size in pixels: x, y
        tile_size (tuple[int, int]): Tile size in pixels: x, y

    Yields:
        Iterator[tuple[int, int, int]]: tile tuples in area: x, y, z
    """
    center_x, center_y = point_to_xy(center[0], center[1], zoom_level)
    delta_x, delta_y = [window_size[i] / tile_size[i] / 2 for i in range(2)]

    yield from itertools.product(
        range(math.floor(center_x - delta_x), math.floor(center_x + delta_x) + 1),
        range(math.floor(center_y - delta_y), math.floor(center_y + delta_y) + 1),
        (zoom_level,),
    )


def get_tile_xyz_bbox(
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


def point_to_xy(
    latitude: float, longitude: float, zoom_level: int
) -> tuple[float, float]:
    """Convert geographical point to xy pixel coordinates

    Args:
        latitude (float): Latitude
        longitude (float): Longitude
        zoom_level (int): Zoom level

    Returns:
        tuple[float, float]: x, y coordinates, not rounded
    """
    x_pixels = _lon_to_x_px(longitude, zoom_level)
    y_pixels = _lat_to_y_px(latitude, zoom_level)
    return (x_pixels, y_pixels)


def _lon_to_x(longitude: float, zoom_level: int) -> int:
    """Convert longitude to tile x coordinate"""
    return math.floor(_lon_to_x_px(longitude, zoom_level))


def _lon_to_x_px(longitude: float, zoom_level: int) -> int:
    return (longitude + 180) / 360 * math.pow(2, zoom_level)


def _lat_to_y(latitude: float, zoom_level: int) -> int:
    """Convert latitude to tile y coordinate"""
    return math.floor(_lat_to_y_px(latitude, zoom_level))


def _lat_to_y_px(latitude: float, zoom_level: int) -> int:
    return (
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
