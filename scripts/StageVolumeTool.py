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

        # We add the input DEM raster layer.
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DEM,
                self.tr('Input DEM raster layer'),
            )
        )

        # We add a vector layer destination (the DBF is considered a vector layer)
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                self.OUTPUT_DBF,
                self.tr('Output Stage Volume Table')
            )
        )
    
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """


        demLayer = self.parameterAsRasterLayer(
            parameters,
            self.INPUT_DEM,
            context
        )

        # If DEM layer was not found, throw an exception to indicate that the algorithm
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


        # If output DBF was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        if outDBF is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT_DBF))



        # Run the script
        stats = demLayer.dataProvider().bandStatistics(1)
        demMinimum = stats.minimumValue
        demMaximum = stats.maximumValue
        print("min:",demMinimum,"m")
        print("max:",demMaximum,"m")
        demRange = demMaximum - demMinimum
        print("Elevation Difference:",demRange,"m")
        n_increments = 10
        increment = demRange / n_increments
        print("Increment:",increment)

        levels = [demMinimum + i * increment for i in range(n_increments + 1)]
        dbfList = []
        for level in levels:
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

        # Return the results of the algorithm.
        outFile = os.path.splitext(outDBF)[0]+".dbf"
        return {self.OUTPUT_DBF: outFile}
