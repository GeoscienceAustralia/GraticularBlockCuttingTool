
from qgis.core import *

layer = iface.activeLayer()
layer.id()
layer.featureCount()

# select features with blank 'Vertices' field
request = QgsFeatureRequest().setFilterExpression( u'"Vertices" == \'\'' )
new_features = layer.getFeatures( request )

for each_new_feature in new_features:
    msg = "This feature need to be atrributed: layer=%s ID=%d" % (layer.name(),  each_new_feature.id())
    print msg
