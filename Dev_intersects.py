# http://gis.stackexchange.com/questions/26257/how-can-i-iterate-over-map-layers-in-qgis-python


from qgis.core import *
import shutil
import os, sys

#shutil.copy("C:\WorkSpace\QGIS\TestData\SC52_5M_Polygon_Master", "C:\WorkSpace\QGIS\TestData\SC52_5M_Polygon")
#os.system("cp C:\WorkSpace\QGIS\TestData\SC52_5M_Polygon_Master.*  C:\WorkSpace\QGIS\TestData\SC52_5M_Polygon.*")

#iface.addVectorLayer("C:\WorkSpace\QGIS\TestData\SC52_5M_Polygon.shp", "SC52_5M_Polygon", "ogr")


# both work
layers = iface.legendInterface().layers()
#layers = iface.mapCanvas().layers()

# set layers
for layer in layers:
    layerType = layer.type()
    layerName = layer.name()
    if layerName == "":
        cutter_layer = layer
    
    if layerName == "Coastal_2006_complete":
        cutter_layer = layer
        print "Cutter layer FeatureCount: ", cutter_layer.featureCount()
        
    if layerName == "SC52_5M_Polygon":
        cutted_layer = layer
        print "Cutted layer FeatureCount: ", cutted_layer.featureCount()


selected_cutted_feature_count = cutted_layer.selectedFeatureCount()
print "selected to be cut: ", selected_cutted_feature_count 
selected_cutted_features = cutted_layer.selectedFeatures()

cutted_layer.startEditing()

for each_polygon_feature in selected_cutted_features:
    
    # search for cutter features which intersect with each_polygon_feature
    print "Processing: ", each_polygon_feature.id()
    
    myGeometry = each_polygon_feature.geometry()
    areaOfInterest = myGeometry.boundingBox()
    
    request = QgsFeatureRequest()
    request .setFilterRect(areaOfInterest)
    
    cutter_features = cutter_layer.getFeatures(request)
    
    merged_cutter_geom = QgsGeometry().asPolyline()
    first_cutter_geom_defined = False
    for each_cutter_feature in cutter_features:
        print each_polygon_feature.id(), "intersects with ", each_cutter_feature.id()
        current_geom = each_cutter_feature.geometryAndOwnership()
        
        print repr(current_geom)
        print current_geom.length()
        
        if first_cutter_geom_defined == False:
            print "start new geom"
            merged_cutter_geom = current_geom 
            first_cutter_geom_defined = True
        else:
            print "add geom to collecton"
            merged_cutter_geom = merged_cutter_geom.combine(current_geom)
   
        if merged_cutter_geom is None:
            print "merged_cutter_geom is None !"
        else:
            print  "merged_cutter_geom is OK"
        
    myGeometry = each_polygon_feature.geometry()
    
    if merged_cutter_geom:
    
        if myGeometry.intersects(merged_cutter_geom):
            
            #split geometry 
            result, newGeometries, topoTestPoints = myGeometry.splitGeometry(merged_cutter_geom.asPolyline(), True) 
            
            print "result, new geoms", result, len(newGeometries)

            if result ==0:
                #update the original feature 
                each_polygon_feature.setGeometry(myGeometry) 
                cutted_layer.updateFeature(each_polygon_feature) 
                
                for aGeom in newGeometries: 
                    #print aGeom.exportToWkt()
                    newFeature = QgsFeature() 
                    newFeature.setGeometry(aGeom)
                    newFeature.setAttributes(each_polygon_feature.attributes()) 
                    print "Add new feature"
                                
                    cutted_layer.addFeatures([newFeature])
        else:
                print "??? not intersects  ", each_polygon_feature.id()
            
cutted_layer.commitChanges()
