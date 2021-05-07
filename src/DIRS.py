from qgis.core import *


ROOT = QgsProject.instance().readPath("./")
DATA = ROOT+'/data'
ORIGINAL_DATA = DATA+'/original'
MODIFIED_DATA = DATA+'/modified'

PATHS = { 'ROOT':ROOT, 'DATA':DATA, 'ORIGINAL_DATA':ORIGINAL_DATA, 'MODIFIED_DATA':MODIFIED_DATA }


