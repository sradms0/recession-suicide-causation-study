from qgis.core import *
from PyQt5.QtCore import *
from qgis.utils import *

from os import walk

from DIRS import PATHS

def clear_layers():
    print('removing all layers')
    project_instance = QgsProject.instance()
    for layer in project_instance.mapLayers().values():
        project_instance.removeMapLayer(layer)


def get_geo_layers(mapLayers):
    from re import search

    return [
        l for l in mapLayers.values() 
        if search('\w+_geo_\d+', l.name())
    ]

def import_geo_layers():
    print('importing geo layers')

    iface.mainWindow().blockSignals(True)

    ROOT = PATHS['MODIFIED_DATA']
    DB_PATH = f'{ROOT}/db'
    FINAL_SHP_PATH = f'{ROOT}/shp/final'

    iface.addVectorLayer(f'{DB_PATH}/state_suicides_unemployment_geometry.db', '', 'ogr')
    iface.addVectorLayer(f'{DB_PATH}/oregon_counties_suicides_unemployment_geometry.db', '', 'ogr')
    states_and_counties_unemp_sui_db_geo_layers = get_geo_layers(QgsProject.instance().mapLayers())
    
    for db_layer in states_and_counties_unemp_sui_db_geo_layers:
        final_shp_name = f'{FINAL_SHP_PATH}/{db_layer.name()}.shp'
        QgsVectorFileWriter.writeAsVectorFormat(db_layer,final_shp_name,"utf-8", driverName="ESRI Shapefile")
        QgsProject.instance().removeMapLayer(db_layer)

        final_shp_layer = iface.addVectorLayer(final_shp_name, '', 'ogr')
        curr_final_shp_layer_name = final_shp_layer.name()
        final_shp_layer.setName(curr_final_shp_layer_name.split(' ')[1])
        crs = final_shp_layer.crs()
        crs.createFromId(4326)
        final_shp_layer.setCrs(crs)
        
    iface.mainWindow().blockSignals(False)


def style_geo_layers():
    print('styling geo layers')

    COLORS = {
        '1.1': '#fffdf0',
        '1.2': '#e6f1e0',
        '1.3': '#d4e5f7',
        '2.1': '#fdf3ab',
        '2.2': '#bfdebe',
        '2.3': '#a1c7eb',
        '3.1': '#e6d201',
        '3.2': '#7ec6b0',
        '3.3': '#007fc4'
    }

    states_and_counties_unemp_sui_geo_layers = get_geo_layers(QgsProject.instance().mapLayers())
    for layer in states_and_counties_unemp_sui_geo_layers:
        print(layer)
        categories = []

        for bimode, color in COLORS.items():
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            layer_style = {'color': color }
            symbol_layer = QgsSimpleFillSymbolLayer.create(layer_style)
            
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)
            
            category = QgsRendererCategory(bimode, symbol, str(bimode))
            categories.append(category)

        renderer = QgsCategorizedSymbolRenderer('bimode', categories)
        if renderer is not None:
            layer.setRenderer(renderer)
            
        layer.triggerRepaint()


def import_and_style():
    import_geo_layers()
    style_geo_layers()


if __name__ != '__main__': pass
