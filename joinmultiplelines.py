# -------------------------------------------------------------------------------
# Name:        joinmultiplelines
# Purpose:     Join multiple lines into one continuous line
#
# Author:      Daan Goedkoop
#
# Created:     26-04-2013
# Copyright:   (c) Daan Goedkoop 2013-2018
# Licence:     All rights reserved.
#
#              Redistribution and use in source and binary forms, with or
#              without modification, are permitted provided that the following
#              conditions are met:
#
#              - Redistributions of source code must retain the above copyright
#                notice, this list of conditions and the following disclaimer.
#              - Redistributions in binary form must reproduce the above
#                copyright notice, this list of conditions and the following
#                disclaimer in the documentation and/or other materials
#                provided with the distribution.
#
#              THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
#              CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#              INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
#              MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#              DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
#              CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#              SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#              LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#              USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
#              AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#              LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#              IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#              THE POSSIBILITY OF SUCH DAMAGE.
#
# Version 0.1: 26-04-2013
#              initial version
#         0.2: 29-04-2013
#              Produce valid geometry if begin and end vertices are identical.
#         0.3: 03-02-2014
#              Update for QGis 2.0
#              Operation is now a single undo/redo-step, instead of having a
#                  separate step for the removal of the superfluous features.
#         0.4: 22-01-2018
#              Update for QGis 3.0
#              Support multi-part lines
#         0.4.1: 22.01.2018
#              Bug fix for displaying warnings
# -------------------------------------------------------------------------------

from pathlib import Path

from qgis.core import Qgis, QgsGeometry
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction


class JoinMultipleLines:
    def __init__(self, iface):
        # save reference to the QGIS interface
        self.iface = iface
        self.plugin_dir = Path(__file__).parent

    def initGui(self):
        icon_path = str(self.plugin_dir / "icon.png")
        self.action = QAction(
            QIcon(icon_path),
            "Join multiple lines",
            self.iface.mainWindow(),
        )
        self.action.setWhatsThis("Permanently join multiple lines")
        self.action.setStatusTip(
            "Permanently join multiple lines (removes lines used for joining)"
        )

        self.action.triggered.connect(self.run)

        self.iface.addVectorToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu("&Join multiple lines", self.action)

    def unload(self):
        self.iface.removePluginVectorMenu("&Join multiple lines", self.action)
        self.iface.removeVectorToolBarIcon(self.action)

    def _distance(self, vertex1, vertex2):
        return vertex1.distanceSquared(vertex2)

    def _first_vertex(self, geom):
        return geom.vertexAt(0)

    def _last_vertex(self, geom):
        return geom.vertexAt(len(geom.asPolyline()) - 1)

    def _step(self, geom, queue_list):
        if geom is None:
            if queue_list:
                return queue_list.pop()
            return None

        base_firstvertex = self._first_vertex(geom)
        base_lastvertex = self._last_vertex(geom)
        found_geom = None
        found_distance = 0
        found_base_reverse = False
        found_i_reverse = False

        for i_geom in queue_list:
            i_firstvertex = self._first_vertex(i_geom)
            i_lastvertex = self._last_vertex(i_geom)
            distance_baselast_ifirst = self._distance(base_lastvertex, i_firstvertex)
            distance_baselast_ilast = self._distance(base_lastvertex, i_lastvertex)
            distance_basefirst_ifirst = self._distance(base_firstvertex, i_firstvertex)
            distance_basefirst_ilast = self._distance(base_firstvertex, i_lastvertex)
            distance = distance_baselast_ifirst
            base_reverse = False
            i_reverse = False
            if distance_baselast_ilast < distance:
                distance = distance_baselast_ilast
                base_reverse = False
                i_reverse = True
            if distance_basefirst_ifirst < distance:
                distance = distance_basefirst_ifirst
                base_reverse = True
                i_reverse = False
            if distance_basefirst_ilast < distance:
                distance = distance_basefirst_ilast
                base_reverse = True
                i_reverse = True
            if found_geom is None or distance < found_distance:
                found_geom = i_geom
                found_distance = distance
                found_base_reverse = base_reverse
                found_i_reverse = i_reverse

        if found_geom is not None:
            queue_list.remove(found_geom)
            geom_line = geom.constGet()
            found_geom_line = found_geom.constGet()
            if found_base_reverse:
                geom_line = geom_line.reversed()
            if found_i_reverse:
                found_geom_line = found_geom_line.reversed()
            # .append automatically takes care not to create a duplicate
            # vertex when the last respectively first vertex of the two
            # segments are identical.
            geom_line.append(found_geom_line)
            geom.set(geom_line)
            return geom

        return None

    def run(self):
        cl = self.iface.mapCanvas().currentLayer()

        if cl is None:
            self.iface.messageBar().pushMessage(
                "Join multiple lines",
                "No layers selected",
                Qgis.MessageLevel.Warning,
                10,
            )
            return
        if cl.type() != Qgis.LayerType.Vector:
            self.iface.messageBar().pushMessage(
                "Join multiple lines",
                "Not a vector layer",
                Qgis.MessageLevel.Warning,
                10,
            )
            return
        if cl.geometryType() != Qgis.GeometryType.Line:
            self.iface.messageBar().pushMessage(
                "Join multiple lines",
                "Not a line layer",
                Qgis.MessageLevel.Warning,
                10,
            )
            return

        selfeats = cl.selectedFeatures()
        if len(selfeats) < 2:
            self.iface.messageBar().pushMessage(
                "Join multiple lines",
                "At least two lines should be selected",
                Qgis.MessageLevel.Warning,
                10,
            )
            return

        geomlist = []
        for feat in selfeats:
            geom = QgsGeometry(feat.geometry())
            if geom.isMultipart():
                geomlist.extend(geom.asGeometryCollection())
            else:
                geomlist.append(geom)

        newgeom = None
        while geomlist:
            newgeom = self._step(newgeom, geomlist)

        cl.startEditing()
        cl.beginEditCommand("Join multiple lines")
        cl.changeGeometry(selfeats[0].id(), newgeom)
        for feat in selfeats[1:]:
            cl.deleteFeature(feat.id())

        cl.endEditCommand()
        self.iface.mapCanvas().refresh()
