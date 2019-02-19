# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GraticularBlockCuttingTool_QGIS
                                 A QGIS plugin
 This plugin cuts graticular polygon blocks
                             -------------------
        begin                : 2016-04-29
        copyright            : (C) 2016 by Qing Zhong
        email                : Qing.Zhong@ga.gov.au
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GraticularBlockCuttingTool_QGIS class from file graticular_block_cutting_tool.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .graticular_block_cutting_tool import GraticularBlockCuttingTool_QGIS
    return GraticularBlockCuttingTool_QGIS(iface)
