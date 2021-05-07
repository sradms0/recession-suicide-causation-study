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


if __name__ != '__main__': pass
