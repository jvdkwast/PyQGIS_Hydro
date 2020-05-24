# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import (QVariant, QCoreApplication)
from qgis.core import (QgsProcessing,
                       QgsField,
                       QgsVectorLayer,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterRasterLayer,
                       QgsProcessingParameterVectorDestination)
from qgis import processing
import os


class StageVolumeTool(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_DEM = 'INPUT'
    OUTPUT_DBF = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return StageVolumeTool()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'stagevolumetool'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Stage Volume Tool')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Hydrology')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'scripts'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("This tool generates a table with stage and volume that can be further visualised with the DataPlotly plugin or opened in a spreadsheet program")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DEM,
                self.tr('Input DEM raster layer'),
            )
        )

        # We add a feature sink in which to store our processed features (this
        # usually takes the form of a newly created vector layer when the
        # algorithm is run in QGIS).
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT_DBF,
                self.tr('Output Stage Volume Table')
            )
        )

    def frange(self, start, stop, step):
        i = start
        while i < stop:
            yield i
            i += step
    
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        demLayer = self.parameterAsRasterLayer(
            parameters,
            self.INPUT_DEM,
            context
        )

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if demLayer is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_DEM))

        outDBF = self.parameterAsOutputLayer(
            parameters,
            self.OUTPUT_DBF,
            context
        )


        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if outDBF is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_DBF))



        # To run another Processing algorithm as part of this algorithm, you can use
        # processing.run(...). Make sure you pass the current context and feedback
        # to processing.run to ensure that all temporary layer outputs are available
        # to the executed algorithm, and that the executed algorithm can send feedback
        # reports to the user (and correctly handle cancellation and progress reports!)
        stats = demLayer.dataProvider().bandStatistics(1)
        demMinimum = stats.minimumValue
        demMaximum = stats.maximumValue
        print("min:",demMinimum,"m")
        print("max:",demMaximum,"m")
        demRange = demMaximum - demMinimum
        print("Elevation Difference:",demRange,"m")
        increment = demRange / 10.0
        print("Increment:",increment)
        i = 0
        dbfList = []
        for level in self.frange(demMinimum,demMaximum + 1,increment):
            outTable = os.path.join(os.path.dirname(outDBF),"volume" + str(round(level*100.0)))
            outTableDbf = str(outTable) + ".dbf"
            processing.run("native:rastersurfacevolume", {'INPUT':demLayer,
                                                            'BAND':1,
                                                            'LEVEL':level,
                                                            'METHOD':1,
                                                            'OUTPUT_HTML_FILE':'TEMPORARY_OUTPUT',
                                                            'OUTPUT_TABLE':outTable + ".shp"
                                                        })
    
            dbfTable = QgsVectorLayer(outTable + ".dbf", outTable, "ogr")
            for feature in dbfTable.getFeatures():
                VolumeKm3 = abs(feature["Volume"])/1000000000.0
    
  
            pr = dbfTable.dataProvider()
            pr.addAttributes([QgsField("Level", QVariant.Double),QgsField("VolAbsKm3", QVariant.Double)])
            dbfTable.updateFields()
            dbfTable.startEditing()
            for f in dbfTable.getFeatures():
                f["Level"] = level
                f["VolAbsKm3"] = VolumeKm3
                dbfTable.updateFeature(f)
            dbfTable.commitChanges()
 
            dbfList.append(outTableDbf)

        volumetable = processing.run("native:mergevectorlayers", {'LAYERS':dbfList,
                                                    'CRS':None,
                                                    'OUTPUT':outDBF
                                                    })

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        outFile = os.path.splitext(outDBF)[0]+".dbf"
        return {self.OUTPUT_DBF: outFile}
