from qgis.core import *

import sys
sys.path.append(QgsProject.instance().readPath("./")+'/src')

from data_operations import *
from layer_operations import *


clear_layers()
clean_and_create()
