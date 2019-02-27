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

from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon
# Initialize Qt resources from file resources.py
import Resources_rc
# Import the code for the dialog
from graticular_block_cutting_tool_dialog import GraticularBlockCuttingTool_QGISDialog
import os.path


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
        self.dlg.btn_CutPolygons.clicked.connect(self.CutPolygons)

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

    def CutPolygons(self):

        # clear message display
        self.dlg.listWidget_Messages.clear()

        # make sure the top layer is a line feature class
        top_layer = self.iface.mapCanvas().layer(0)
        if top_layer.wkbType() == QGis.WKBLineString:
            msg = 'Top layer is a linestring layer'
            # self.dlg.listWidget_Messages.addItem(msg)
        else:
            msg = 'Top layer is NOT a linestring layer'
            self.dlg.listWidget_Messages.addItem(msg)
            return ()

        cutter_layer = top_layer

        # make sure the layer to be cut is a polygon feature class

        cutted_layer = self.iface.mapCanvas().layer(1)
        if cutted_layer.wkbType() <> QGis.WKBPolygon:
           msg = 'layer to be cut is NOT a polygon layer'
           self.dlg.listWidget_Messages.addItem(msg)
           return ()

        self.dlg.listWidget_Messages.addItem("Cutting polygons ...")

        # *************************************************************************************************************
        # Merge selected features from 'cutter' layer
        selected_cutter_feature_count = cutter_layer.selectedFeatureCount()
        msg = "selected from cutter layer: " + selected_cutter_feature_count
        self.dlg.listWidget_Messages.addItem(msg)

        if selected_cutter_feature_count == 0:
            return ()

        selected_cutter_features = cutter_layer.selectedFeatures()

        merged_geom = selected_cutter_features[0].geometry()

        for feature in selected_cutter_features:
            current_geom = feature.geometry()
            merged_geom = merged_geom.combine(current_geom)


        # http://gis.stackexchange.com/questions/72907/split-a-feature-when-intersecting-with-a-feature-of-another-layer-using-pyqgis-p

        # Create a memory layer to store the result
        resultl = QgsVectorLayer("Polygon", "result", "memory")
        resultpr = resultl.dataProvider()
        QgsMapLayerRegistry.instance().addMapLayer(resultl)

        for feature in cutted_layer.getFeatures():
            if feature.geometry().intersects(merged_geom):
              # Save the original geometry
                geometry = QgsGeometry.fromPolygon(feature.geometry().asPolygon())

                # Intersect the polygon with the line. If they intersect, the feature will contain one half of the split
                t = feature.geometry().reshapeGeometry(merged_geom.asPolyline())
                if (t==0):
                  # Create a new feature to hold the other half of the split
                  diff = QgsFeature()
                  # Calculate the difference between the original geometry and the first half of the split
                  diff.setGeometry( geometry.difference(feature.geometry()))
                  # Add the two halves of the split to the memory layer
                  resultpr.addFeatures([feature])
                  #resultpr.addFeatures([diff])
        #  *************************************************************************************************************

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
