"""Map tile sources"""

from dataclasses import dataclass
import itertools
from typing import Iterator
from urllib.parse import urlparse, unquote
from pathlib import Path

from dearpygui_map.util import user_cache_dir

from .geo import get_tile_xyz_bbox


@dataclass
class TileServer:

    """Map tile source"""

    name: str
    base_url: str
    subdomains: list[str]
    thread_limit: int = 1
    tile_size: tuple[int, int] = (256, 256)

    def to_tile_spec(self, tile_x: int, tile_y: int, zoom_level: int) -> "TileSpec":
        """Get tile specification for x, y, z coordinate tuple

        Args:
            tile_x (int): Tile x coordinate
            tile_y (int): Tile y coordinate
            zoom_level (int): Zoom level

        Returns:
            TileSpec: Tile specification
        """
        return TileSpec(
            tile_x=tile_x,
            tile_y=tile_y,
            zoom_level=zoom_level,
            tile_size=self.tile_size,
            base_url=self.base_url,
            subdomains=self.subdomains,
        )

    def get_tile_specs(
        self,
        bbox: tuple[float, float, float, float],
        zoom_level: int,
    ) -> Iterator["TileSpec"]:
        """Get tile specifications for bounding box area

        Args:
            bbox (tuple[float, float, float, float]):
                Bounding box lat_min, lon_min, lat_max, lon_max
            zoom_level (int): Zoom level
            tile_source (TileServer): Tile source

        Yields:
            Iterator[TileSpec]: tile specifications
        """
        yield from itertools.starmap(
            self.to_tile_spec, get_tile_xyz_bbox(bbox=bbox, zoom_level=zoom_level)
        )


@dataclass
class TileSpec:

    """Specification of a tile on server"""

    tile_x: int
    tile_y: int
    zoom_level: int
    base_url: str
    subdomains: list[str]
    tile_size: tuple[int, int] = (256, 256)

    @property
    def download_url(self):
        """Get download url for tile"""
        return self.base_url.format(
            subdomain=self.subdomains[0],
            x=self.tile_x,
            y=self.tile_y,
            z=self.zoom_level,
        )

    @property
    def local_storage_path(self) -> Path:
        """Get file location on local device"""
        cache_root = user_cache_dir()
        local_url = self.base_url.replace("{subdomain}.", "").format(
            x=self.tile_x,
            y=self.tile_y,
            z=self.zoom_level,
        )
        components = urlparse(local_url)
        Path(unquote(components.path))
        return Path(
            cache_root, components.netloc, *Path(unquote(components.path)).parts[1:]
        )

    def canvas_coordinates(self, x_offset: int, y_offset: int) -> tuple[int, int]:
        """Calculate canvas coordinates for tile

        Args:
            x_offset (int): Offset for tile x position, pixels
            y_offset (int): Offset for tile y position, pixels

        Returns:
            tuple[int, int]: position (x, y)
        """
        return (
            self.tile_x * self.tile_size[0] + x_offset,
            self.tile_y * self.tile_size[1] + y_offset,
        )


OpenStreetMap = TileServer(
    name="OpenStreetMap",
    base_url="http://{subdomain}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    subdomains=["a", "b", "c"],
    thread_limit=2,
)
