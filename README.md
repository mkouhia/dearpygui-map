# dearpygui-map
Map widget for Dear PyGui

## Installation

### Requirements

- Python >= 3.7
- Dear PyGui >= 1.3.1

### Option 1 - pip

You can install this package from pip, with

    pip install dearpygui-map

### Option 2 - Local install from sources

Clone code repository from your local machine, install from there. [Poetry][poetry-install] is required.

    git clone https://github.com/mkouhia/dearpygui-map.git
    cd dearpygui-map
    poetry build
    # take note of the build step output, install package from the dist folder
    pip install dist/PRODUCED_PACKAGE.whl


## Usage

This basic example creates a map widget with defined size, initial center point (latitude, longitude) and initial zoom level. The zoom levels are same as on [tiled maps][tile-zoom-levels], for example 12 could represent a town-sized view. Larger is more zoomed in.

```python
import dearpygui.dearpygui as dpg
import dearpygui_map as dpg_map

dpg.create_context()

with dpg.window(label="Map demo"):
    dpg_map.add_map_widget(
        width=700,
        height=500,
        center=(60.1641, 24.9402),
        zoom_level=12)

dpg.create_viewport(title="Dear PyGui map widget demo", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
```

The function `add_map_widget` places a Dear PyGui drawlist with map contents,
return value is the drawlist tag.

By default, OpenStreetMap is used as the map tile source. This can be configured with `add_map_widget` argument `tile_source`, with similar source definition:

```python
OpenStreetMap = TileServer(
    name="OpenStreetMap",
    base_url="http://{subdomain}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    subdomains=["a", "b", "c"],
    max_zoom_level=19,
    license_text="© OpenStreetMap contributors",
    thread_limit=2,
)
```

## Technical details

Tiles are downloaded from the supplier on a background thread.
Whenever map is zoomed or moved, more tiles are downloaded.
The tiles are cached to local storage path in user cache directory - for different platforms, cache directories are:

    Windows:    C:\Users\<username>\AppData\Local\dearpygui_map\Cache
    Mac OS X:   ~/Library/Caches/dearpygui_map
    Other:      ~/.cache/dearpygui_map


### Known issues

As for now, dearpygui-map is in its early design phase and contains some items that may not be acceptable in production environments.
These issues will be addressed later

- Tile download threads are created every time `TileManager.draw_layer` is called.
- Non-visible tiles are not removed from dearpygui
- Zooming and panning leads to wait times before tiles are ready to be shown.

## Development

### Environment

Poetry is required for development (see [installation instructions][poetry-install])

1. Create development environment with `poetry install`
2. Enter environment with `poetry shell`


### Code quality and testing

All code is to be formatted with `black`:

    black dearpygui_map

and code quality checked with `pylint`:

    pylint dearpygui_map

Tests should be written in `pytest`, targeting maximum practical code coverage. Tests are run with:

    pytest

and test coverage checked with

    pytest --cov

Optionally, html test coverage reports can be produced with

    pytest --cov dearpygui_map --cov-report html


### Contributions

Contributions are welcome. Please also see GitHub issues and milestones.


[poetry-install]: https://python-poetry.org/docs/#installation "Poetry: Installation"
[tile-zoom-levels]: https://wiki.openstreetmap.org/wiki/Zoom_levels "Open Street Map wiki: Zoom levels"
