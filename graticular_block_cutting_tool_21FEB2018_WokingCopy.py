# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GraticularBlockCuttingTool_QGIS
                                 A QGIS plugin
 This plugin cuts graticular polygon blocks
                              -------------------
        begin                : 2016-04-29
        git sha              : $Format:%H$
        copyright            : (C) 2016 by Qing Zhong
        email                : Qing.Zhong@ga.gov.au
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.core import *

# qz added
import PyQt4
from PyQt4 import QtGui

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFile, QFileInfo
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import Resources_rc
# Import the code for the dialog
from graticular_block_cutting_tool_dialog import GraticularBlockCuttingTool_QGISDialog
import os.path

import xml.etree.ElementTree as ET

import datetime
import copy

DEBUG = False
def debug_print(msg):
    if DEBUG:
        print msg

Title = "GraticularBlockCuttingTool_QGIS 19 Feb 2018 17:18 PM"
BlockLetter_of_1M_BlockID  = "ABCDEFGHJKLMNOPQRSTUVWXYZ"

#USER_CONFIG_FILE_PATH = "c:/Workspace/QGIS/CodeDev/user.config"

# os.path.realpath(__file__):
# 'C:\\Users\\u43418\\.qgis2\\python\\plugins\\GraticularBlockCuttingTool_QGIS\\graticular_block_cutting_tool.py

USER_CONFIG_FILE_PATH = os.path.join( os.path.dirname(__file__),   "user.config")

# def GetActualFieldName(feature, field_name):
#     #
#     # To support both shape file and file geodatabase
#     # shape file's field name is limited to 10 characters
#     # so if input is a shape file, then limit the field_name to 10 characters long
#
#     field_index = feature.fields().indexFromName(field_name)
#
#     if field_index == -1:
#         field_name = field_name[:10]
#
#     return field_name

def GetActualFieldName(layer, field_name):
    #
    # To support both shape file and file geodatabase
    # shape file's field name is limited to 10 characters
    # so if input is a shape file, then limit the field_name to 10 characters long

    # 5M uses 'Nunmber_of_Vertices'
    # 1M and newer dataset: Nunmber_Of_Vertices
    if field_name == "Number_Of_Vertices":

        field_index = layer.fields().indexFromName(field_name)

        if field_index == -1:
            # try shapefile
            field_name = field_name[:10]
            field_index = layer.fields().indexFromName(field_name)
        
            # try 5M 
            if field_index == -1:
                field_name = "Number_of_Vertices"
                field_index = layer.fields().indexFromName(field_name)

                if field_index == -1:
                    field_name = field_name[:10]

        return field_name

    # for any other field

    field_index = layer.fields().indexFromName(field_name)

    if field_index == -1:
        field_name = field_name[:10]
        field_index = layer.fields().indexFromName(field_name)
        #print "shape file", field_name,field_index

    return field_name

def GetMapSheetName(layer):

    # get map sheet name from layer name
    # SC53_1M_Polygon --> SC53
    # SV58_58_59_60_1D_Polygon -->  SV58_58_59_60

    layer_name = layer.name()

    if "_1M_" in layer_name:
        sep = "_1M_"
    elif "_1D_" in layer_name:
        sep = "_1D_"
    elif "_5M_" in layer_name:
        sep = "_5M_"
    elif "_10M_" in layer_name:
        sep = "_10M_"
    elif "_10S_" in layer_name:
        sep = "_10S_"
    elif "_6S_" in layer_name:
        sep = "_6S_"

    layer_name =  layer_name.split(sep)[0]

    return layer_name

# class ProgressBar():
#     def __init__(self, max):
#         self.max = max
#         self.dlg.progressBar.setValue(0)
#
#     def update(self,count):
#         value = count*100/self.max
#         self.dlg.progressBar.setValue(value)

# class ProgressBar:
#     def __init__(self, progressBar_Widget, max):
#         self.max = max
#         self.progressBar_Widget = progressBar_Widget
#         self.progressBar_Widget.setValue(0)
#
#     def update(self,count):
#         value = count*100/self.max
#         self.progressBar_Widget.setValue(value)

class GraticularBlockCuttingTool_QGIS:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GraticularBlockCuttingTool_QGIS_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = GraticularBlockCuttingTool_QGISDialog()

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&GraticularBlockCuttingTool_QGIS')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GraticularBlockCuttingTool_QGIS')
        self.toolbar.setObjectName(u'GraticularBlockCuttingTool_QGIS')

        #
        self.dlg.setWindowTitle(Title)
        #
        self.dlg.comboScale.addItem("1M")
        self.dlg.comboScale.addItem("5M")
        self.dlg.comboScale.addItem("1D")
        self.dlg.comboScale.addItem("10M")
        self.dlg.comboScale.addItem("6S")
        self.dlg.comboScale.addItem("10S")
        #
        self.dlg.btn_EditUserSettings.clicked.connect(self.EditUserSettings)
        self.dlg.btn_SaveUserSettings.clicked.connect(self.SaveUserSettings)
        self.dlg.btn_CutPolygons.clicked.connect(self.CutPolygons)
        self.dlg.btn_ClearMessage.clicked.connect(self.ClearMessage)
        self.dlg.btn_CheckArea.clicked.connect(self.CheckArea)
        self.dlg.btn_PopulateFieldAttributes.clicked.connect(self.PopulateFieldAttributes)
        self.dlg.btn_Test.clicked.connect(self.download)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GraticularBlockCuttingTool_QGIS', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the InaSAFE toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/GraticularBlockCuttingTool_QGIS/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Cutt Graticular Blocks'),
            callback=self.run,
            parent=self.iface.mainWindow())


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GraticularBlockCuttingTool_QGIS'),
                action)
            self.iface.removeToolBarIcon(action)

    def progressBar_Init(self,max_count):
        self.max_count = max_count
        self.completed = 0
        self.dlg.progressBar.setValue(0)
        self.dlg.progressBar.repaint() # asynchronous
        self.dlg.repaint()
        QCoreApplication.processEvents()

    def progressBar_update(self):
            self.completed = self.completed + 1
            value = self.completed*100/self.max_count
            if value > 100: value = 100
            self.dlg.progressBar.setValue(value)
            self.dlg.progressBar.repaint() # asynchronous
            self.dlg.repaint()
            QCoreApplication.processEvents()

    def download(self):

        self.progressBar_Init(1000)
        while self.completed < 1000:
            #self.completed = self.completed + 1
            self.progressBar_update()

        # layer = self.iface.mapCanvas().layer(0)
        #
        # fc = layer.featureCount()
        # self.Add_Message("featureCount= %s" % fc)
        #
        # layer_name = layer.name()
        # layer_id = layer.id()
        #
        # mDataSource = layer.dataProvider().dataSourceUri()
        #
        # #output_file = "C:/WorkSpace/QGIS/LearnDevPlugin/TestData/SC53_5M_Polygon_cut_TodayCopy.shp"
        # shape_file = mDataSource.split('|')[0]
        # shape_file = shape_file.replace('\\','/')
        #
        # self.Add_Message("layer name= %s" % layer_name)
        # self.Add_Message("layer id= %s" % layer_id)
        # #self.Add_Message("baseName= %s" % baseName)
        # self.Add_Message("mDataSource= %s" % mDataSource)
        # self.Add_Message("shape_file= %s" % shape_file)

        #self.completed = 0

        # while self.completed < 100:
        #     self.completed += 0.0001
        #     self.dlg.progressBar.setValue(self.completed)



        # QgsVectorFileWriter.writeAsVectorFormat(layer, 'c:/temp/myjson.json', 'utf-8', layer.crs(), 'GeoJson') # ok
        #QgsVectorFileWriter.writeAsVectorFormat(layer, r"C:/temp/qz_test.shp","utf-8",None,"ESRI Shapefile") # ok

        # output_file_temp = "C:/WorkSpace/QGIS/LearnDevPlugin/TestData/temp.shp"
        # r = QgsVectorFileWriter.writeAsVectorFormat(layer, output_file_temp,"utf-8",None,"ESRI Shapefile")
        # print repr(r)
        #
        # # remove original layer
        # QgsMapLayerRegistry.instance().removeMapLayer( layer_id )
        #
        # # delete original shapefile
        # #if os.path.isfile(output_file):
        # #    os.remove(output_file)
        # QgsVectorFileWriter.deleteShapeFile(shape_file)

        # copy temp as original

        # add 'new' layer
        # layer = self.iface.addVectorLayer(output_file_temp, layer_name + "_copy", "ogr")
        # if not layer:
        #     print "Layer failed to load!"

        # delete temp


    def ClearMessage(self):
         # clear message display
        self.dlg.listWidget_Messages.clear()

    def PassInitialChecks(self):

        #  Make sure all feature classes are in right order

        number_of_layers = self.iface.mapCanvas().layerCount()

        if number_of_layers >= 2:
            # Need at least two feature classes: 'Cutter' and 'Cutted'

            # make sure the top layer is a line feature class
            top_layer = self.iface.mapCanvas().layer(0)
            if top_layer.wkbType() == QGis.WKBLineString or top_layer.wkbType() == QGis.WKBMultiLineString:
                # msg = 'Top layer is a linestring layer'
                # self.dlg.listWidget_Messages.addItem(msg)
                return True
            else:
                msg = 'Top layer is NOT a linestring layer'
                self.Add_Message(msg)
                return False
        else:
                msg = "Need at least two feature classes: 'Cutter' and 'Cutted'"
                self.Add_Message(msg)
                return False

    def CutPolygons_Debug_Ver_2_16(self):

        # clear message display
        self.dlg.listWidget_Messages.clear()

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        top_layer = self.iface.mapCanvas().layer(0)
        cutter_layer = top_layer

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            cutted_layer = self.iface.mapCanvas().layer(i)
            debug_print("cutted_layer: %s" % repr(cutted_layer))

            field_index_Vertices = cutted_layer.fields().indexFromName( GetActualFieldName(cutted_layer,'Vertices') )
            field_index_BLOCK_ID = cutted_layer.fields().indexFromName( GetActualFieldName(cutted_layer,'BLOCK_ID') )
            field_index_Total = cutted_layer.fields().indexFromName( GetActualFieldName(cutted_layer,'Total') )

            # make sure the layer to be cut is a polygon feature class
            if cutted_layer.wkbType() <> QGis.WKBPolygon and cutted_layer.wkbType() <> QGis.WKBMultiPolygon:
                continue

            Start_time = datetime.datetime.now()
            self.Add_Message("Start cutting polygons %s" % Start_time)

            # *************************************************************************************************************

            selected_cutted_features = cutted_layer.selectedFeatures()

            selected_feature_count = cutted_layer.selectedFeatureCount()
            self.Add_Message("Number of polygons to be cut: %d" % selected_feature_count)

            cutted_layer.startEditing()

            self.progressBar_Init(selected_feature_count)

            for each_polygon_feature in selected_cutted_features:

                self.progressBar_update()

                BLOCK_ID = each_polygon_feature[field_index_BLOCK_ID]

                # search for cutter features which intersect with each_polygon_feature

                myGeometry = each_polygon_feature.geometry()
                areaOfInterest = myGeometry.boundingBox()

                request = QgsFeatureRequest()
                request.setFilterRect(areaOfInterest)

                cutter_features = cutter_layer.getFeatures(request)

                merged_cutter_geom = QgsGeometry().asPolyline()

                first_cutter_geom_defined = False

                for each_cutter_feature in cutter_features:

                    current_geom = each_cutter_feature.geometryAndOwnership()

                    #
                    if first_cutter_geom_defined == False:
                        merged_cutter_geom = current_geom
                        first_cutter_geom_defined = True
                    else:
                        merged_cutter_geom = merged_cutter_geom.combine(current_geom)

                if not merged_cutter_geom: continue     # no intersect polylines found, move to next polygon

                geom_col = merged_cutter_geom.asGeometryCollection()

                # giving problem ?
                debug_print ("For BLOCK_ID=%s, may need to cut %d times" %  (BLOCK_ID,len(geom_col)) )

                for each_merged_cutter_geom in geom_col:

                    #debug_print "Each geom_col ->", each_merged_cutter_geom.asPolyline()
                    debug_print ("Each cutting geom_col  length-> %s" % each_merged_cutter_geom.length())

                    # get all polygon features with the same BLOCK_ID: one is the original, and the others are newly created after cutting
                    request_2 = QgsFeatureRequest().setFilterExpression( u'"BLOCK_ID" =\'' + BLOCK_ID + '\'' )
                    polygon_features_with_current_BLOCK_ID = cutted_layer.getFeatures( request_2 )

                    for each_polygon_feature_with_current_BLOCK_ID in polygon_features_with_current_BLOCK_ID:

                        debug_print ("Test to see if this polygon will be cut: id= %s" % each_polygon_feature_with_current_BLOCK_ID.id())

                        This_geometry = each_polygon_feature_with_current_BLOCK_ID.geometry()

                        if This_geometry.intersects(each_merged_cutter_geom):

                            # when commitChanges() is called, edit session is  stopped, so call startEditing() to make sure it is in editing mode
                            cutted_layer.startEditing()

                            debug_print( "Try to cut this polygon: id=%d" % each_polygon_feature_with_current_BLOCK_ID.id())
                            #split geometry
                            result, newGeometries, topoTestPoints = This_geometry.splitGeometry(each_merged_cutter_geom.asPolyline(), True)
                            This_geometry_cp = This_geometry

                            if result ==0:

                                debug_print("Cutting ok")
                                # update the original feature
                                # each_polygon_feature_with_current_BLOCK_ID.setGeometry(This_geometry_cp)
                                # each_polygon_feature_with_current_BLOCK_ID.setAttribute(field_index_Total, '-1') # set 'Total' field to -1 to indicate it has been cut
                                # each_polygon_feature_with_current_BLOCK_ID.setAttribute(field_index_Vertices, '') # if use GEO_NONE then it is a string 'NONE'
                                # 'Vertices' field need to be re-attributed, set to blank here so that at next proceesing phase will know which feature to be attributed
                                # updateFeature() function has problem witg shapefile for QGIS 2.14
                                #cutted_layer.updateFeature(each_polygon_feature_with_current_BLOCK_ID)
                                #cutted_layer.changeGeometry(each_polygon_feature_with_current_BLOCK_ID.id(), This_geometry) # This line will crash !!!!

                                # commit after each cut
                                # if commit here new feature is deleted !!!
                                #res_1 = cutted_layer.commitChanges()
                                #debug_print ("commit changes: res_1=%s" % res_1)

                                # create new feature from original
                                #cutted_layer.startEditing()

                                newFeature = QgsFeature()
                                newFeature.setGeometry(This_geometry_cp)
                                # copy all attributes. Must have this, otherwise the new feature will NOT be created, unlike ArcGIS's way of creating new features
                                newFeature.setAttributes(each_polygon_feature_with_current_BLOCK_ID.attributes())
                                # 'Vertices' field need to be re-attributed, set to blank here so that at next proceesing phase will know which feature to be attributed
                                newFeature.setAttribute(field_index_Vertices, '')
                                newFeature.setAttribute(field_index_Total, '-1')

                                #res = cutted_layer.addFeatures([newFeature],True)
                                res = cutted_layer.addFeature(newFeature,True)
                                debug_print ("Add 'new' feature: %s" % res)
                                debug_print ("new polygon: id=%s" % newFeature.id())

                                # for aGeom in newGeometries:
                                #
                                #     newFeature = QgsFeature()
                                #     newFeature.setGeometry(aGeom)
                                #     # copy all attributes. Must have this, otherwise the new feature will NOT be created, unlike ArcGIS's way of creating new features
                                #     newFeature.setAttributes(each_polygon_feature_with_current_BLOCK_ID.attributes())
                                #     # 'Vertices' field need to be re-attributed, set to blank here so that at next proceesing phase will know which feature to be attributed
                                #     newFeature.setAttribute(field_index_Vertices, '')
                                #     newFeature.setAttribute(field_index_Total, '-1')
                                #
                                #     res = cutted_layer.addFeatures([newFeature],True)
                                #     debug_print ("Add new feature: %s" % res)
                                #     debug_print ("new polygon: id=%s" % newFeature.id())

                                # delete the original
                                cutted_layer.deleteFeature(each_polygon_feature_with_current_BLOCK_ID.id())

                                # must commit changes to ensure changes (updated original and newly created features) are written back to disk so that when these features are
                                # read back, they have been actually updated.
                                res_2 = cutted_layer.commitChanges()

                                debug_print ("commit changes: res_2=%s" % res_2)

                                break   # try to cut only once per segment

            End_time = datetime.datetime.now()
            self.Add_Message("Finished cutting polygons %s (%s)" % (End_time,End_time - Start_time))

            self.PopPolygon_Area_Fields(cutted_layer)



    def CutPolygons(self):

        # clear message display
        self.dlg.listWidget_Messages.clear()

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        top_layer = self.iface.mapCanvas().layer(0)
        cutter_layer = top_layer

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            cutted_layer = self.iface.mapCanvas().layer(i)
            debug_print("cutted_layer: %s" % repr(cutted_layer))
            #field_index_Vertices = each_polygon_feature.fields().indexFromName( GetActualFieldName(each_polygon_feature,'Vertices') )
            #field_index_BLOCK_ID = each_polygon_feature.fields().indexFromName( GetActualFieldName(each_polygon_feature,'BLOCK_ID') )
            field_index_Vertices = cutted_layer.fields().indexFromName( GetActualFieldName(cutted_layer,'Vertices') )
            field_index_BLOCK_ID = cutted_layer.fields().indexFromName( GetActualFieldName(cutted_layer,'BLOCK_ID') )
            field_index_Total = cutted_layer.fields().indexFromName( GetActualFieldName(cutted_layer,'Total') )

            # make sure the layer to be cut is a polygon feature class
            if cutted_layer.wkbType() <> QGis.WKBPolygon and cutted_layer.wkbType() <> QGis.WKBMultiPolygon:
                continue

            Start_time = datetime.datetime.now()
            self.Add_Message("Start cutting polygons %s" % Start_time)

            # *************************************************************************************************************

            selected_cutted_features = cutted_layer.selectedFeatures()

            selected_feature_count = cutted_layer.selectedFeatureCount()
            self.progressBar_Init(selected_feature_count)
            self.Add_Message("Number of polygons to be cut: %d" % selected_feature_count)

            cutted_layer.startEditing()

            for each_polygon_feature in selected_cutted_features:

                self.progressBar_update()

                BLOCK_ID = each_polygon_feature[field_index_BLOCK_ID]

                # search for cutter features which intersect with each_polygon_feature

                myGeometry = each_polygon_feature.geometry()
                areaOfInterest = myGeometry.boundingBox()

                request = QgsFeatureRequest()
                request.setFilterRect(areaOfInterest)

                cutter_features = cutter_layer.getFeatures(request)

                merged_cutter_geom = QgsGeometry().asPolyline()

                first_cutter_geom_defined = False

                for each_cutter_feature in cutter_features:

                    current_geom = each_cutter_feature.geometryAndOwnership()

                    #
                    if first_cutter_geom_defined == False:
                        merged_cutter_geom = current_geom
                        first_cutter_geom_defined = True
                    else:
                        merged_cutter_geom = merged_cutter_geom.combine(current_geom)

                if not merged_cutter_geom: continue     # no intersect polylines found, move to next polygon

                geom_col = merged_cutter_geom.asGeometryCollection()

                # giving problem ?
                debug_print ("For BLOCK_ID=%s, may need to cut %d times" %  (BLOCK_ID,len(geom_col)) )
                #print "For BLOCK_ID=%s, may need to cut %d times" %  (BLOCK_ID,len(geom_col))

                for each_merged_cutter_geom in geom_col:

                    #debug_print "Each geom_col ->", each_merged_cutter_geom.asPolyline()
                    debug_print ("Each cutting geom_col  length-> %s" % each_merged_cutter_geom.length())

                    # get all polygon features with the same BLOCK_ID: one is the original, and the others are newly created after cutting
                    request_2 = QgsFeatureRequest().setFilterExpression( u'"BLOCK_ID" =\'' + BLOCK_ID + '\'' )
                    polygon_features_with_current_BLOCK_ID = cutted_layer.getFeatures( request_2 )

                    for each_polygon_feature_with_current_BLOCK_ID in polygon_features_with_current_BLOCK_ID:

                        debug_print ("Test to see if this polygon will be cut: id= %s" % each_polygon_feature_with_current_BLOCK_ID.id())

                        This_geometry = each_polygon_feature_with_current_BLOCK_ID.geometry()

                        if This_geometry.intersects(each_merged_cutter_geom):

                            # when commitChanges() is called, edit session is  stopped, so call startEditing() to make sure it is in editing mode
                            cutted_layer.startEditing()

                            debug_print( "Try to cut this polygon: id=%d" % each_polygon_feature_with_current_BLOCK_ID.id())
                            #split geometry
                            result, newGeometries, topoTestPoints = This_geometry.splitGeometry(each_merged_cutter_geom.asPolyline(), True)
                            This_geometry_cp = This_geometry

                            if result ==0:

                                debug_print("Cutting ok")
                                # update the original feature
                                # each_polygon_feature_with_current_BLOCK_ID.setGeometry(This_geometry_cp)
                                # each_polygon_feature_with_current_BLOCK_ID.setAttribute(field_index_Total, '-1') # set 'Total' field to -1 to indicate it has been cut
                                # each_polygon_feature_with_current_BLOCK_ID.setAttribute(field_index_Vertices, '') # if use GEO_NONE then it is a string 'NONE'
                                # 'Vertices' field need to be re-attributed, set to blank here so that at next proceesing phase will know which feature to be attributed
                                # updateFeature() function has problem witg shapefile for QGIS 2.14
                                #cutted_layer.updateFeature(each_polygon_feature_with_current_BLOCK_ID)
                                #cutted_layer.changeGeometry(each_polygon_feature_with_current_BLOCK_ID.id(), This_geometry) # This line will crash !!!!

                                # commit after each cut
                                # if commit here new feature is deleted !!!
                                #cutted_layer.commitChanges()

                                # create new feature from original

                                newFeature = QgsFeature()
                                newFeature.setGeometry(This_geometry_cp)
                                # copy all attributes. Must have this, otherwise the new feature will NOT be created, unlike ArcGIS's way of creating new features
                                newFeature.setAttributes(each_polygon_feature_with_current_BLOCK_ID.attributes())
                                # 'Vertices' field need to be re-attributed, set to blank here so that at next proceesing phase will know which feature to be attributed
                                newFeature.setAttribute(field_index_Vertices, '')
                                newFeature.setAttribute(field_index_Total, '-1')

                                res = cutted_layer.addFeatures([newFeature],True)
                                debug_print ("Add 'new' feature: %s" % res)
                                debug_print ("new polygon: id=%s" % newFeature.id())

                                for aGeom in newGeometries:

                                    newFeature = QgsFeature()
                                    newFeature.setGeometry(aGeom)
                                    # copy all attributes. Must have this, otherwise the new feature will NOT be created, unlike ArcGIS's way of creating new features
                                    newFeature.setAttributes(each_polygon_feature_with_current_BLOCK_ID.attributes())
                                    # 'Vertices' field need to be re-attributed, set to blank here so that at next proceesing phase will know which feature to be attributed
                                    newFeature.setAttribute(field_index_Vertices, '')
                                    newFeature.setAttribute(field_index_Total, '-1')

                                    res = cutted_layer.addFeatures([newFeature],True)
                                    debug_print ("Add new feature: %s" % res)
                                    debug_print ("new polygon: id=%s" % newFeature.id())

                                # delete the original
                                cutted_layer.deleteFeature(each_polygon_feature_with_current_BLOCK_ID.id())

                                # must commit changes to ensure changes (updated original and newly created features) are written back to disk so that when these features are
                                # read back, they have been actually updated.
                                res_2 = cutted_layer.commitChanges()

                                debug_print ("commit changes: res_2=%s" % res_2)

                                break   # try to cut only once per segment

            End_time = datetime.datetime.now()
            self.Add_Message("Finished cutting polygons %s (%s)" % (End_time,End_time - Start_time))

            self.PopPolygon_Area_Fields(cutted_layer)

        #End_time = datetime.datetime.now()
        #self.Add_Message("Finished cutting polygons %s (%s)" % (End_time,End_time - Start_time))

        #  *************************************************************************************************************

    def PopPolygon_Area_Fields(self,layer):


        Start_time = datetime.datetime.now()
        self.Add_Message("Start populate area fields %s" % Start_time)
        feature_count = layer.featureCount()
        self.progressBar_Init(feature_count)

        # http://gis.stackexchange.com/questions/114735/qgis-python-convert-the-crs-of-an-in-memory-vector-layer
        # http://www.digital-geography.com/creating-arcs-qgis-python-way/?subscribe=success#518

        # http://gis.stackexchange.com/questions/102119/how-to-change-the-value-of-an-attribute-using-qgsfeature-in-pyqgis

        #field_index_Area_Hecta = feature.fields().indexFromName(GetActualFieldName(feature,'Area_Hectares'))
        #field_index_Area_Acres = feature.fields().indexFromName(GetActualFieldName(feature,'Area_Acres'))
        field_index_Area_Hecta = layer.fields().indexFromName(GetActualFieldName(layer,'Area_Hectares'))
        field_index_Area_Acres = layer.fields().indexFromName(GetActualFieldName(layer,'Area_Acres'))

        layer.startEditing()

        #sourceCrs = QgsCoordinateReferenceSystem(4283)
        sourceCrs = layer.crs()
        destCrs = QgsCoordinateReferenceSystem(3577)
        xform = QgsCoordinateTransform(sourceCrs, destCrs)

        # populate only these polygons which have been cut
        request = QgsFeatureRequest().setFilterExpression(u'"Total"=\'-1\'')    # "Total"='-1'

        iter = layer.getFeatures(request)

        # ? why no fields() attribute
        #field_index = layer.fields().indexFromName('Area_Hecta')

        for feature in iter:

            geom = feature.geometryAndOwnership()
            geom.transform(xform)

            # DO NOT USE THIS, GEOMETRY WILL BE CHANGED AS WELL
            #feature['Area_Hecta'] = geom.area()*0.0001
            #layer.updateFeature(feature)

            layer.changeAttributeValue(feature.id(), field_index_Area_Acres, geom.area()*0.0002471054)
            layer.changeAttributeValue(feature.id(), field_index_Area_Hecta, geom.area()*0.0001)

            self.progressBar_update()

        layer.commitChanges()

        End_time = datetime.datetime.now()
        self.Add_Message("Finished populate area fields %s (%s)" % (End_time,End_time - Start_time))

    def CheckArea(self):

        # clear message display
        self.dlg.listWidget_Messages.clear()

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        # get minimum area
        tree = ET.parse(USER_CONFIG_FILE_PATH)
        root = tree.getroot()

        setting = root.find("./userSettings/GraticularBlockCuttingTool.My.MySettings/setting[@name='Minimum_Polygon_Area_Hectares_App']")

        Minimum_Polygon_Area_Hectares_App  = setting.find('value').text

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)

            # get area field name
            Area_Hectares_Field_Name = GetActualFieldName(layer, "Area_Hectares")

            # if area of a feature is smaller than specified value, list the feature
            #request = QgsFeatureRequest().setFilterExpression( u'"Area_Hectares" < ' + Minimum_Polygon_Area_Hectares_App )
            request = QgsFeatureRequest().setFilterExpression( u'"' + Area_Hectares_Field_Name +'" < ' + Minimum_Polygon_Area_Hectares_App )
            small_features = layer.getFeatures( request )

            for each_small_feature in small_features:
                msg = "Found small feature: layer=%s ID=%d where %s < %f" % (layer.name(),  each_small_feature.id(),  'Area_Hectares', float(Minimum_Polygon_Area_Hectares_App))
                self.Add_Message(msg)

    def PopulateFieldAttributes(self):

        if self.dlg.chk_UserDefinedFields.isChecked():
            self.Populate_User_Defined_Field_Attributes()
        if self.dlg.chk_BlockNumberField.isChecked():
            self.Populate_Block_Number_Field()
        if self.dlg.chk_MapSheet.isChecked():
            self.Populate_Map_Sheet_Field()
        if self.dlg.chk_PolygonPartAndTotalField.isChecked():
            self.Populate_Polygon_Part_and_Total_Fields()
        if self.dlg.chk_VerticesField.isChecked():
            self.Populate_Vertices_Field()

    def Populate_User_Defined_Field_Attributes(self):

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        Start_time = datetime.datetime.now()
        self.Add_Message("Start populate user defined fields %s" % Start_time)

        tree = ET.parse(USER_CONFIG_FILE_PATH)
        root = tree.getroot()

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)

            self.Add_Message("Populating %s's user defined field attributes" % (layer.name()) )

            layer.startEditing()

            features = layer.getFeatures()

            for feature in features:

                # ToDo: change path to constant
                for setting in root.findall("./userSettings/GraticularBlockCuttingTool.My.MySettings/setting"):

                    attribute_value = setting.find('value').text
                    attribute_name = setting.get('name')

                    #field_index = feature.fields().indexFromName(GetActualFieldName(feature,attribute_name))
                    field_index = feature.fields().indexFromName(GetActualFieldName(layer,attribute_name))

                    if field_index <> -1:
                        layer.changeAttributeValue(feature.id(), field_index, attribute_value)

            layer.commitChanges()

            End_time = datetime.datetime.now()
            self.Add_Message("Finished populating %s's user defined field attributes %s (%s)" % (layer.name(),End_time, (End_time - Start_time) ) )

    def Populate_Block_Number_Field(self):

        # BLOCK_ID = SC54_1234 --> Block_Number = 1234

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        # for 1M and 5M, Block_Number is 2nd item in BLOCK_ID (SA01_1234 or SA01_1234_Z), while it is the 3rd item for 1D (SA01_1D_12)
        # This block needs to be moved out later !!!!
        if self.dlg.comboScale.currentText() == "1D":
            Block_Number_Index = 2
        else:
            Block_Number_Index = 1

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)

            field_index_BLCOK_ID = layer.fields().indexFromName(GetActualFieldName(layer,'BLOCK_ID'))
            field_index_Block_Number = layer.fields().indexFromName(GetActualFieldName(layer,'Block_Number'))

            Start_time = datetime.datetime.now()
            self.Add_Message("Populating %s's 'BLOCK_Number' field" % (layer.name()) )

            layer.startEditing()

            features = layer.getFeatures()

            for feature in features:

                if field_index_BLCOK_ID <> -1 and field_index_Block_Number <> -1:
                    #layer.changeAttributeValue(feature.id(), field_index_Block_Number, feature[field_index_BLCOK_ID].split('_')[-1] )
                    layer.changeAttributeValue(feature.id(), field_index_Block_Number, feature[field_index_BLCOK_ID].split('_')[Block_Number_Index] )

            layer.commitChanges()

            End_time = datetime.datetime.now()
            self.Add_Message("Finished populating %s's 'BLOCK_Number' %s (%s)" % (layer.name(),End_time, (End_time - Start_time) ) )


    def Populate_Map_Sheet_Field(self):
        # BLOCK_ID = SC54_1234 --> Map_Sheet = SC54

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)

            #field_index_BLCOK_ID = feature.fields().indexFromName(GetActualFieldName(feature,'BLOCK_ID'))
            #field_index_Block_Number = feature.fields().indexFromName(GetActualFieldName(feature,'Map_Sheet'))
            field_index_BLCOK_ID = layer.fields().indexFromName(GetActualFieldName(layer,'BLOCK_ID'))
            field_index_Block_Number = layer.fields().indexFromName(GetActualFieldName(layer,'Map_Sheet'))

            Start_time = datetime.datetime.now()
            self.Add_Message("Populating %s's 'Map_Sheet' field %s" % (layer.name(),Start_time) )

            layer.startEditing()

            features = layer.getFeatures()

            for feature in features:

                if field_index_BLCOK_ID <> -1 and field_index_Block_Number <> -1:
                   layer.changeAttributeValue(feature.id(), field_index_Block_Number, feature[field_index_BLCOK_ID].split('_')[0] )

            layer.commitChanges()

            End_time = datetime.datetime.now()
            self.Add_Message("Finished populating %s's 'Map_Sheet' %s (%s)" % (layer.name(),End_time, (End_time - Start_time) ) )

    def Populate_Polygon_Part_and_Total_Fields(self):

        # V2: SC52_1M: 20 min
        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        # for 1M and 5M, 48 5M rows and 72 5M columns
        # for 1D, 4 1D rows and 6 1D columns
        # This block needs to be moved out later !!!!
        if self.dlg.comboScale.currentText() == "1D":
            LAT_END_INDEX = 5
            LONG_END_INDEX = 7
            Block_EndIndex_1M = 0
        elif self.dlg.comboScale.currentText() == "5M":
            LAT_END_INDEX = 49   #49
            LONG_END_INDEX = 73 #73
            Block_EndIndex_1M = 0
        elif self.dlg.comboScale.currentText() == "1M":
            LAT_END_INDEX = 49       #49
            LONG_END_INDEX = 73      #73
            Block_EndIndex_1M = 24

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)

            #field_index_Part = each_feature.fields().indexFromName(GetActualFieldName(each_feature,'Part'))
            #field_index_Total = each_feature.fields().indexFromName(GetActualFieldName(each_feature,'Total'))
            field_index_Part = layer.fields().indexFromName(GetActualFieldName(layer,'Part'))
            field_index_Total = layer.fields().indexFromName(GetActualFieldName(layer,'Total'))
            field_index_BLOCK_ID = layer.fields().indexFromName(GetActualFieldName(layer,'BLOCK_ID'))

            Block_Number_Field_Name = GetActualFieldName(layer, "Block_Number")


            Start_time = datetime.datetime.now()
            self.Add_Message("Populating %s's 'Part' and 'Total' fields %s" % (layer.name(),Start_time) )

            layer.startEditing()

            # ==========
            # build a dictionary of these features have been cut

            Start_time_2 = datetime.datetime.now()
            #self.Add_Message("Start to request to get all cut polygons %s" % Start_time_2)

            # select features with  'Total' field is '-1'
            request = QgsFeatureRequest().setFilterExpression( u'"Total"=\'-1\'')
            new_features = layer.getFeatures( request )

            End_time_2 = datetime.datetime.now()
            #self.Add_Message("Finished get all cut polygons %s (%s)" % (End_time_2,End_time_2 - Start_time_2))

            dict = {}

            for each_new_feature in new_features:

                BLOCK_ID = each_new_feature[field_index_BLOCK_ID]

                if BLOCK_ID in dict:
                    dict[BLOCK_ID]['Total'] = dict[BLOCK_ID]['Total'] + 1
                else:
                    dict[BLOCK_ID] = {}
                    dict[BLOCK_ID]['Total'] = 1

                dict[BLOCK_ID]['Part'] = 0

            self.progressBar_Init(len(dict))
            self.Add_Message("Need to prcess %d blocks %s" % ( len(dict), datetime.datetime.now()))
            i = 0

            # process each block
            # select features with  'Total' field is '-1'
            request = QgsFeatureRequest().setFilterExpression( u'"Total"=\'-1\'')
            new_features = layer.getFeatures( request )
            
            for each_new_feature in new_features:

                self.progressBar_update()

                each_BLOCK_ID = each_new_feature[field_index_BLOCK_ID]

                dict[each_BLOCK_ID]['Part'] = dict[each_BLOCK_ID]['Part'] + 1

                if field_index_Part <> -1:
                    layer.changeAttributeValue(each_new_feature.id(), field_index_Part, str(dict[each_BLOCK_ID]['Part']) )

                if field_index_Total <> -1:
                    layer.changeAttributeValue(each_new_feature.id(), field_index_Total, str(dict[each_BLOCK_ID]['Total']) )

                i = i + 1

                #self.Add_Message("finish %d  %s" % (i, datetime.datetime.now()))

            # ==========


            layer.commitChanges()

            End_time = datetime.datetime.now()
            self.Add_Message("Finished populating %s's ''Part' and 'Total' fields %s (%s)" % (layer.name(),End_time, (End_time - Start_time) ) )


    def Populate_Vertices_Field(self):

        # clear message display
        self.dlg.listWidget_Messages.clear()
        self.Add_Message("Populating 'Vertices' field")

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)
            #field_index_Vertices = each_new_feature.fields().indexFromName(GetActualFieldName(each_new_feature,'Vertices'))
            #field_index_Number_of_Vertices = each_new_feature.fields().indexFromName(GetActualFieldName(each_new_feature,'Number_of_Vertices'))
            field_index_Vertices = layer.fields().indexFromName(GetActualFieldName(layer,'Vertices'))
            field_index_Number_Of_Vertices = layer.fields().indexFromName(GetActualFieldName(layer,'Number_Of_Vertices'))

            Start_time = datetime.datetime.now()
            self.progressBar_Init(100)  # dummy
            self.Add_Message("Populating %s's 'Vertices' field %s" % (layer.name(),Start_time) )

            layer.startEditing()

            # select features with blank 'Vertices' field
            request = QgsFeatureRequest().setFilterExpression( u'"Vertices" is null or "Vertices"=\'\'')
            new_features = layer.getFeatures( request )

            # get feature count
            feature_count = 0
            for each_new_feature in new_features:   feature_count = feature_count + 1
            self.progressBar_Init(feature_count)

            # query again
            new_features = layer.getFeatures( request )

            for each_new_feature in new_features:

                self.progressBar_update()

                msg = "This feature's vertices field needs to be atrributed: layer=%s ID=%d" % (layer.name(),  each_new_feature.id())
                self.Add_Message(msg)

                # a shapefile has no multipolygon type, 'change' it to multipolygon
                polygons = each_new_feature.geometry().asMultiPolygon()
                if len(polygons) == 0: # this can be a shapefile
                    polygons = each_new_feature.geometry().asPolygon()
                    # make it as multipolygon
                    polygons = [polygons]

                for polygon in polygons:

                    str_list=[]

                    for ring in polygon:

                        numPts = len(ring)
                        for vertex in ring:
                            str_list.append("%.10f" % vertex[1])    # LAT
                            str_list.append("%.10f" % vertex[0])    # LONG

                    full_csv_list = ','.join(str_list)              # CSV format

                    layer.changeAttributeValue(each_new_feature.id(), field_index_Vertices, full_csv_list )
                    layer.changeAttributeValue(each_new_feature.id(), field_index_Number_Of_Vertices, numPts )
                    #msg = "field index: %d numPts: %d" % (field_index_Number_Of_Vertices, numPts)
                    #self.Add_Message(msg)
                
            layer.commitChanges()
            End_time = datetime.datetime.now()
            self.Add_Message("Finished populating %s's 'Vertices'field %s (%s)" % (layer.name(),End_time, (End_time - Start_time) ) )


    # http://stackoverflow.com/questions/11457839/populating-a-table-in-pyqt-with-file-attributes
    def EditUserSettings(self):

        #self.dlg.tableWidget_uers_settings.setRowCount(10)
        #self.dlg.tableWidget_uers_settings.setColumnCount(2)

        # ToDo: change path to constant
        tree = ET.parse(USER_CONFIG_FILE_PATH)
        root = tree.getroot()

        # ToDo: change path to constant

        number_of_user_settings = len(root.findall("./userSettings/GraticularBlockCuttingTool.My.MySettings/setting"))
        self.dlg.tableWidget_uers_settings.setRowCount(number_of_user_settings)

        # populate table for editing
        row_index = 0

        for setting in root.findall("./userSettings/GraticularBlockCuttingTool.My.MySettings/setting"):

            setting_name = QtGui.QTableWidgetItem(setting.get('name'))
            setting_name.setFlags(PyQt4.QtCore.Qt.ItemIsSelectable | PyQt4.QtCore.Qt.ItemIsEnabled)    # make column NOT editable !! http://stackoverflow.com/questions/17104413/pyqt4-how-to-select-table-rows-and-disable-editing-cells
            setting_value = QtGui.QTableWidgetItem(setting.find('value').text)

            self.dlg.tableWidget_uers_settings.setItem(row_index, 0 , setting_name)
            self.dlg.tableWidget_uers_settings.setItem(row_index, 1 , setting_value)

            row_index = row_index + 1

        self.dlg.tableWidget_uers_settings.resizeColumnsToContents()

    def SaveUserSettings(self):

        tree = ET.parse(USER_CONFIG_FILE_PATH)
        root = tree.getroot()

        for row_index in range(0,self.dlg.tableWidget_uers_settings.rowCount()):    # 0,2,...17

            name_item = self.dlg.tableWidget_uers_settings.item(row_index,0).text()
            value_item = self.dlg.tableWidget_uers_settings.item(row_index,1).text()

            #self.Add_Message(name_item + "," + value_item)

            setting = root.find("./userSettings/GraticularBlockCuttingTool.My.MySettings/setting" + "[@name=\"" + name_item + "\"]")

            if setting:
                value_node = setting.find('value')
                value_node.text = value_item
                #self.Add_Message("Find node, value -> " + value_item )

        tree.write(USER_CONFIG_FILE_PATH)
        self.dlg.tableWidget_uers_settings.clearContents()
        self.dlg.tableWidget_uers_settings.setRowCount(0)

    # http://stackoverflow.com/questions/8539100/can-qlistwidget-be-refreshed-after-an-addition
    def Add_Message(self, msg):
        self.dlg.listWidget_Messages.addItem(msg)
        self.dlg.listWidget_Messages.scrollToBottom()
        self.dlg.listWidget_Messages.repaint() # asynchronous
        self.dlg.repaint()
        QCoreApplication.processEvents()



    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass
