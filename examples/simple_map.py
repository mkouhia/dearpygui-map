import dearpygui.dearpygui as dpg

import dearpygui_map.widget as dpg_map

dpg.create_context()

with dpg.window(label="Map demo"):

    with dpg.group(horizontal=True):
        with dpg_map.map_widget(500, 500):
            dpg_map.configure_tile_layer()
    
dpg.create_viewport(title='Dear PyGui map widget demo', width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()