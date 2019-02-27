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

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import Resources_rc
# Import the code for the dialog
from graticular_block_cutting_tool_dialog import GraticularBlockCuttingTool_QGISDialog
import os.path

import xml.etree.ElementTree as ET

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
        self.dlg.btn_EditUserSettings.clicked.connect(self.EditUserSettings)
        self.dlg.btn_SaveUserSettings.clicked.connect(self.SaveUserSettings)
        self.dlg.btn_CutPolygons.clicked.connect(self.CutPolygons)
        self.dlg.btn_ClearMessage.clicked.connect(self.ClearMessage)
        self.dlg.btn_CheckArea.clicked.connect(self.CheckArea)
        self.dlg.btn_PopulateFieldAttributes.clicked.connect(self.PopulateFieldAttributes)


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
            if top_layer.wkbType() == QGis.WKBLineString:
                # msg = 'Top layer is a linestring layer'
                # self.dlg.listWidget_Messages.addItem(msg)
                return True
            else:
                msg = 'Top layer is NOT a linestring layer'
                self.dlg.listWidget_Messages.addItem(msg)
                return False
        else:
                msg = "Need at least two feature classes: 'Cutter' and 'Cutted'"
                self.dlg.listWidget_Messages.addItem(msg)
                return False

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

            # make sure the layer to be cut is a polygon feature class
            if cutted_layer.wkbType() <> QGis.WKBPolygon:
                continue

            self.dlg.listWidget_Messages.addItem("Cutting polygons ...")

            # *************************************************************************************************************

            selected_cutted_features = cutted_layer.selectedFeatures()

            cutted_layer.startEditing()

            for each_polygon_feature in selected_cutted_features:

                field_index_Vertices = each_polygon_feature.fields().indexFromName('Vertices')

                # search for cutter features which intersect with each_polygon_feature

                myGeometry = each_polygon_feature.geometry()
                areaOfInterest = myGeometry.boundingBox()

                request = QgsFeatureRequest()
                request .setFilterRect(areaOfInterest)

                cutter_features = cutter_layer.getFeatures(request)

                merged_cutter_geom = QgsGeometry().asPolyline()
                first_cutter_geom_defined = False

                for each_cutter_feature in cutter_features:

                    current_geom = each_cutter_feature.geometryAndOwnership()

                    if first_cutter_geom_defined == False:
                        merged_cutter_geom = current_geom
                        first_cutter_geom_defined = True
                    else:
                        merged_cutter_geom = merged_cutter_geom.combine(current_geom)

                if merged_cutter_geom:

                    if myGeometry.intersects(merged_cutter_geom):

                        #split geometry
                        result, newGeometries, topoTestPoints = myGeometry.splitGeometry(merged_cutter_geom.asPolyline(), True)

                        if result ==0:
                            #update the original feature
                            each_polygon_feature.setGeometry(myGeometry)
                            each_polygon_feature.setAttribute(field_index_Vertices, '') # if use GEO_NONE then it is a string 'NONE'
                            # 'Vertices' field need to be re-attributed, set to blank here so that at next proceesing phase will know which feature to be attributed
                            cutted_layer.updateFeature(each_polygon_feature)

                            for aGeom in newGeometries:

                                newFeature = QgsFeature()
                                newFeature.setGeometry(aGeom)
                                # copy all attributes. Must have this, otherwise the new feature will NOT be created, unlike ArcGIS's way of creating new features
                                newFeature.setAttributes(each_polygon_feature.attributes())
                                # 'Vertices' field need to be re-attributed, set to blank here so that at next proceesing phase will know which feature to be attributed
                                newFeature.setAttribute(field_index_Vertices, '')

                                # No for QGSI 2.8.3-Wien
                                # newFeature.setAttribute('BLOCK_ID',each_polygon_feature[field_index_BLOCK_ID])

                                # Yes for QGSI 2.8.3-Wien
                                # field_index_BLOCK_ID = each_polygon_feature.fields().indexFromName('BLOCK_ID')
                                # newFeature.setAttribute(field_index_BLOCK_ID, each_polygon_feature[field_index_BLOCK_ID])

                                cutted_layer.addFeatures([newFeature])


            cutted_layer.commitChanges()

            self.PopPolygon_Area_Fields(cutted_layer)

        msg = 'All finished'
        self.dlg.listWidget_Messages.addItem(msg)

        #self.iface.mapCanvas().refresh()

        #  *************************************************************************************************************

    def PopPolygon_Area_Fields(self,layer):

        # http://gis.stackexchange.com/questions/114735/qgis-python-convert-the-crs-of-an-in-memory-vector-layer
        # http://www.digital-geography.com/creating-arcs-qgis-python-way/?subscribe=success#518

        # http://gis.stackexchange.com/questions/102119/how-to-change-the-value-of-an-attribute-using-qgsfeature-in-pyqgis

        layer.startEditing()

        #sourceCrs = QgsCoordinateReferenceSystem(4283)
        sourceCrs = layer.crs()
        destCrs = QgsCoordinateReferenceSystem(3577)
        xform = QgsCoordinateTransform(sourceCrs, destCrs)

        iter = layer.getFeatures()

        # ? why no fields() attribute
        #field_index = layer.fields().indexFromName('Area_Hecta')

        for feature in iter:

            field_index_Area_Hecta = feature.fields().indexFromName('Area_Hecta')
            field_index_Area_Acres = feature.fields().indexFromName('Area_Acres')

            geom = feature.geometryAndOwnership()
            geom.transform(xform)

            #print "Feature ID %d: %f %f" % (feature.id(),  feature['Area_Acres'], geom.area()*0.0001)
            msg = "Feature ID %d: %f %f" % (feature.id(),  feature['Area_Acres'], geom.area()*0.0001)
            self.dlg.listWidget_Messages.addItem(msg)

            # DO NOT USE THIS, GEOMETRY WILL BE CHANGED AS WELL
            #feature['Area_Hecta'] = geom.area()*0.0001
            #layer.updateFeature(feature)

            layer.changeAttributeValue(feature.id(), field_index_Area_Acres, geom.area()*0.0002471054)
            layer.changeAttributeValue(feature.id(), field_index_Area_Hecta, geom.area()*0.0001)

        layer.commitChanges()

    def CheckArea(self):

        # clear message display
        self.dlg.listWidget_Messages.clear()

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)

            # if area of a feature is smaller than specified value, list the feature
            request = QgsFeatureRequest().setFilterExpression( u'"Area_Hecta" < 1000' )
            small_features = layer.getFeatures( request )

            for each_small_feature in small_features:
                msg = "Found small feature: layer=%s ID=%d where %s < %f" % (layer.name(),  each_small_feature.id(),  'Area_Acres', 1000)
                self.dlg.listWidget_Messages.addItem(msg)

    def PopulateFieldAttributes(self):
        #self.Populate_User_Defined_Field_Attributes()
        #self.Populate_Block_Number_Field()
        #self.Populate_Map_Sheet_Field()
        #self.Populate_Polygon_Part_and_Total_Fields()
        self.Populate_Vertices_Field()

    def Populate_User_Defined_Field_Attributes(self):

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        # ToDo: change path to constant
        tree = ET.parse("c:/Workspace/QGIS/CodeDev/user.config")
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

                    field_index = feature.fields().indexFromName(attribute_name)

                    if field_index <> -1:
                        layer.changeAttributeValue(feature.id(), field_index, attribute_value)

            layer.commitChanges()

            self.Add_Message("Finished populating %s's user defined field attributes" % (layer.name()) )

    def Populate_Block_Number_Field(self):

        # BLOCK_ID = SC54_1234 --> Block_Number = 1234

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)

            self.Add_Message("Populating %s's 'BLOCK_Number' field" % (layer.name()) )

            layer.startEditing()

            features = layer.getFeatures()

            for feature in features:

                # ToDo: change field name width: shape file allows only 10 characters long
                field_index_BLCOK_ID = feature.fields().indexFromName('BLOCK_ID')
                field_index_Block_Number = feature.fields().indexFromName('Block_Numb')

                if field_index_BLCOK_ID <> -1 and field_index_Block_Number <> -1:
                   layer.changeAttributeValue(feature.id(), field_index_Block_Number, feature[field_index_BLCOK_ID].split('_')[-1] )

            layer.commitChanges()

            self.Add_Message("Finished populating %s's 'BLOCK_Number' field" % (layer.name()) )

    def Populate_Map_Sheet_Field(self):
        # BLOCK_ID = SC54_1234 --> Map_Sheet = SC54

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)

            self.Add_Message("Populating %s's 'Map_Sheet' field" % (layer.name()) )

            layer.startEditing()

            features = layer.getFeatures()

            for feature in features:

                # ToDo: change field name width: shape file allows only 10 characters long
                field_index_BLCOK_ID = feature.fields().indexFromName('BLOCK_ID')
                field_index_Block_Number = feature.fields().indexFromName('Map_Sheet')

                if field_index_BLCOK_ID <> -1 and field_index_Block_Number <> -1:
                   layer.changeAttributeValue(feature.id(), field_index_Block_Number, feature[field_index_BLCOK_ID].split('_')[0] )

            layer.commitChanges()

            self.Add_Message("Finished populating %s's 'Map_Sheet' field" % (layer.name()) )

    def Populate_Polygon_Part_and_Total_Fields(self):

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)

            self.Add_Message("Populating %s's 'Part' and 'Total' fields" % (layer.name()) )

            layer.startEditing()

            BLOCK_ID_int = 0

            for Lat_index in range(1,49,1): # 48 rows

                for Long_Index in range(1,73,1): # 72 lines

                    BLOCK_ID_int = BLOCK_ID_int + 1

                    request = QgsFeatureRequest().setFilterExpression( u'"Block_Numb" =\'' + "%04d" % BLOCK_ID_int + '\'' ) # "Block_Num" = '0123'
                    features = layer.getFeatures( request )

                    # get total number of features with the same Block_Number
                    Total = 0
                    for each_feature in features:
                        Total = Total + 1

                    # get all the features again (features.rewind() does no work, returns False)
                    features = layer.getFeatures( request )
                    Part_Index  = 0

                    for each_feature in features:

                         Part_Index = Part_Index +1

                         field_index_Part = each_feature.fields().indexFromName('Part')
                         field_index_Total = each_feature.fields().indexFromName('Total')

                         if field_index_Part <> -1:
                            layer.changeAttributeValue(each_feature.id(), field_index_Part, str(Part_Index) )

                         if field_index_Total <> -1:
                            layer.changeAttributeValue(each_feature.id(), field_index_Total, str(Total) )

                    #msg = "layer=%s ID=%d Total:%d" % (layer.name(),  BLOCK_ID_int, Total)
                    #self.dlg.listWidget_Messages.addItem(msg)

            layer.commitChanges()

            self.Add_Message("Finished populating %s's 'Part' and 'Total' fields" % (layer.name()) )


    def Populate_Vertices_Field(self):

        # clear message display
        self.dlg.listWidget_Messages.clear()

        # make sure layers are in right order
        if  self.PassInitialChecks() is False:
            return ()

        number_of_layers = self.iface.mapCanvas().layerCount()

        for i in range(1,number_of_layers,1):

            layer = self.iface.mapCanvas().layer(i)

            layer.startEditing()

            # select features with blank 'Vertices' field
            request = QgsFeatureRequest().setFilterExpression( u'"Vertices" is null' )
            new_features = layer.getFeatures( request )

            for each_new_feature in new_features:

                field_index_Vertices = each_new_feature.fields().indexFromName('Vertices')
                field_index_Number_of_Vertices = each_new_feature.fields().indexFromName('Number_of_')

                msg = "This feature need to be atrributed: layer=%s ID=%d" % (layer.name(),  each_new_feature.id())
                self.dlg.listWidget_Messages.addItem(msg)

                polygons = each_new_feature.geometry().asPolygon()
                if len(polygons) > 1:
                    Add_Message("This feature has inner rings: layer=%s ID=%d" % (layer.name(),  each_new_feature.id()))
                    return()

                numPts = 0
                str_list=[]
                for ring in polygons:
                    numPts += len(ring)
                    for vertex in ring:
                        str_list.append("%.10f" % vertex[1])    # LAT
                        str_list.append("%.10f" % vertex[0])    # LONG

                full_csv_list = ','.join(str_list)              # CSV format

                layer.changeAttributeValue(each_new_feature.id(), field_index_Vertices, full_csv_list )
                layer.changeAttributeValue(each_new_feature.id(), field_index_Number_of_Vertices, numPts )

            layer.commitChanges()

    # http://stackoverflow.com/questions/11457839/populating-a-table-in-pyqt-with-file-attributes
    def EditUserSettings(self):
        #self.dlg.tableWidget_uers_settings.setRowCount(10)
        #self.dlg.tableWidget_uers_settings.setColumnCount(2)

        # ToDo: change path to constant
        tree = ET.parse("c:/Workspace/QGIS/CodeDev/user.config")
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

        tree = ET.parse("c:/Workspace/QGIS/CodeDev/user.config")
        root = tree.getroot()

        for row_index in range(0,self.dlg.tableWidget_uers_settings.rowCount()):    # 0,2,...17

            name_item = self.dlg.tableWidget_uers_settings.item(row_index,0).text()
            value_item = self.dlg.tableWidget_uers_settings.item(row_index,1).text()

            self.Add_Message(name_item + "," + value_item)

            setting = root.find("./userSettings/GraticularBlockCuttingTool.My.MySettings/setting" + "[@name=\"" + name_item + "\"]")

            if setting:
                 self.Add_Message("Find node")



    def Add_Message(self, msg):
        self.dlg.listWidget_Messages.addItem(msg)
        self.dlg.repaint()

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
