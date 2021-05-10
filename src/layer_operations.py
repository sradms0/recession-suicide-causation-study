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

    path = f"{PATHS['MODIFIED_DATA']}/db"
    layer = iface.addVectorLayer(f'{path}/state_suicides_unemployment_geometry.db', '', 'ogr')
    state_unemp_sui_geo_layers = get_geo_layers(QgsProject.instance().mapLayers())
    
    for layer in state_unemp_sui_geo_layers:
        crs = layer.crs()
        crs.createFromId(4326)
        layer.setCrs(crs)
        
    iface.mainWindow().blockSignals(False)


def style_geo_layers():
    print('styling geo layers')

    COLORS = {
        '1.1': '#f3f3f3',
        '1.2': '#eac5dd',
        '1.3': '#e6a3d0',
        '2.1': '#c2f1ce',
        '2.2': '#9ec6d3',
        '2.3': '#bc9fce',
        '3.1': '#8be2af',
        '3.2': '#7fc6b1',
        '3.3': '#7b8eaf'
    }

    state_unemp_sui_geo_layers = get_geo_layers(QgsProject.instance().mapLayers())
    for layer in state_unemp_sui_geo_layers:
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
