"""Geography calculation"""

import itertools
import math
from typing import Iterator


class Coordinate:

    """Internal coordinate representation

    Attributes:
        x (float): x dimension, display units
        y (float): y dimension, display units
    """

    MAX_LATITUDE = 85.0511287798

    def __init__(self, x: float, y: float) -> None:  # pylint: disable=invalid-name
        # pylint: disable=invalid-name
        self.x = x
        self.y = y

    def __repr__(self) -> str:
        return f"Coordinate(x={self.x!r}, y={self.y!r})"

    def __eq__(self, other: "Coordinate") -> bool:
        return self.x == other.x and self.y == other.y

    @staticmethod
    def _lon_to_x(lon: float) -> float:
        if lon > 180 or lon < -180:
            raise ValueError(f"Longitude must be -180...180, {lon=}")
        return (lon + 180) / 360

    @classmethod
    def _lat_to_y(cls, lat: float) -> float:
        if lat > cls.MAX_LATITUDE or lat < -cls.MAX_LATITUDE:
            val_ = cls.MAX_LATITUDE
            raise ValueError(f"Latitude must be -{val_}...{val_}: {lat=}")

        lat_rad = math.radians(lat)
        return (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0

    def tile_xy(self, zoom: int) -> tuple[int, int]:
        """Calculate tile max x, y coordinates

        Args:
            zoom (int): Zoom level

        Returns:
            tuple[int, int]: Tile x, y coordinates
        """
        zoom_scale = math.pow(2, zoom)
        tile_x = math.floor(self.x * zoom_scale)
        tile_y = math.floor(self.y * zoom_scale)
        return (tile_x, tile_y)

    def latlon(self) -> tuple[float, float]:
        """Convert internal coordinates to lat, lon

        Returns:
            tuple[float, float]: latitude, longitude
        """
        lon_deg = self.x * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * self.y)))
        lat_deg = math.degrees(lat_rad)
        return (lat_deg, lon_deg)

    @classmethod
    def from_latlon(cls, latitude: float, longitude: float) -> "Coordinate":
        """Construct internal coordinate representation from lat /lon

        Args:
            latitude (float): Latitude, degrees
            longitude (float): Longitude, degrees

        Raises:
            ValueError: Latitude or longitude is out of bounds: latitude
              must be within -85.0511287798 ... 85.0511287798 (map tile)
              restriction and longitude within -180 ... 180.

        Returns:
            Coordinate: Internal coordinate instance
        """
        coord_x = cls._lon_to_x(longitude)
        coord_y = cls._lat_to_y(latitude)
        return cls(coord_x, coord_y)

    def with_screen_offset(
        self,
        delta_x: float,
        delta_y: float,
        *,
        zoom: int,
        resolution: tuple[int, int] = (256, 256),
    ) -> "Coordinate":
        """Return new coordinate with offset location

        Args:
            delta_x (float): Difference in x coordinate, screen pixels
            delta_y (float): Difference in y coordinate, screen pixels
            zoom (int): Zoom level
            resolution (tuple[int, int]): Pixel resolution per zoom unit

        Returns:
            Coordinate: New coordinate with offset
        """
        dim_tiles = math.pow(2, zoom)
        new_x = self.x + delta_x / (dim_tiles * resolution[0])
        new_y = self.y + delta_y / (dim_tiles * resolution[1])
        return Coordinate(new_x, new_y)


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
    """Convert geographical point to xy tile coordinates

    Args:
        latitude (float): Latitude
        longitude (float): Longitude
        zoom_level (int): Zoom level

    Returns:
        tuple[float, float]: x, y coordinates in tile units, not rounded
    """
    x_pixels = _lon_to_x_px(longitude, zoom_level)
    y_pixels = _lat_to_y_px(latitude, zoom_level)
    return (x_pixels, y_pixels)


def _lon_to_x(longitude: float, zoom_level: int) -> int:
    """Convert longitude to tile x coordinate"""
    return math.floor(_lon_to_x_px(longitude, zoom_level))


def _lon_to_x_px(longitude: float, zoom_level: int) -> int:
    # pylint: disable=protected-access
    return Coordinate._lon_to_x(longitude) * math.pow(2, zoom_level)


def _lat_to_y(latitude: float, zoom_level: int) -> int:
    """Convert latitude to tile y coordinate"""
    return math.floor(_lat_to_y_px(latitude, zoom_level))


def _lat_to_y_px(latitude: float, zoom_level: int) -> int:
    # pylint: disable=protected-access
    return Coordinate._lat_to_y(latitude) * math.pow(2, zoom_level)
