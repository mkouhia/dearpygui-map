"""Geography calculation"""

import math


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

    def tile_xy(self, zoom: int, floor_: bool = True) -> tuple[int, int]:
        """Calculate tile x, y coordinates

        If coordinate falls out of projection (x, y < 0 or > max value),
        just truncate to min/max tile

        Args:
            zoom (int): Zoom level
            floor_ (bool): Truncate coordinates to integer tile numbers

        Returns:
            tuple[int, int]: Tile x, y coordinates
        """
        zoom_scale = math.pow(2, zoom)
        tile_x = self.x * zoom_scale
        tile_y = self.y * zoom_scale

        tile_x = min(max(tile_x, 0), zoom_scale - 1)
        tile_y = min(max(tile_y, 0), zoom_scale - 1)

        if floor_:
            tile_x = math.floor(tile_x)
            tile_y = math.floor(tile_y)

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
