"""Example: display map"""

import dearpygui.dearpygui as dpg
import dearpygui_map as dpg_map

dpg.create_context()

with dpg.window(label="Map demo"):
    dpg_map.add_map_widget(
        width=700, height=500, center=(60.1641, 24.9402), zoom_level=12
    )

dpg.create_viewport(title="Dear PyGui map widget demo", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
