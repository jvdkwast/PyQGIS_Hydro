# -*- coding: utf-8 -*-
"""
######################################################
#    Import data from foerster Magnetometers         #
#                     Gradient                       #
#                                                    #
#                    Stefan Giese                    #
#                  in medias res GmbH                #
#                   ArcGIS july. 2013                #
#          adapted for qgis3.2 in August 2018        #
#             stefan.giese@wheregroup.com            #
######################################################
"""

from PyQt5.QtCore import QCoreApplication
from qgis.PyQt.QtCore import QVariant
from qgis.core import (QgsField,
                       QgsFeature,
                       QgsFields,
                       QgsGeometry,
                       QgsPointXY,
                       QgsWkbTypes,
                       QgsFeatureSink,
                       QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterCrs,
                       QgsProcessingParameterExtent,
                       QgsProcessingParameterNumber,
                       QgsProcessingParameterFile)
import processing
import sys, os, string, math, array
import codecs


class IterateCatchments(QgsProcessingAlgorithm):
    """
    This is Foerster Magnetomer algorithm that takes a txt file (Foerster Magnetomer Export
    creates a vector point layer
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_POINTS = 'INPUT_POINTS'
    INPUT_DEM = 'INPUT_DEM'
	OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return IterateCatchments()

    def name(self):
        return 'iterateCatchments'

    def displayName(self):
        return self.tr('Calculate catchments of multiple outflow points')

    def group(self):
        return self.tr('Hydrology Toolbox')

    def groupId(self):
        return 'hydrologytoolbox'

    def shortHelpString(self):
        return self.tr("Calculates catchments for each point feature")

    def initAlgorithm(self, config=None):

        # We add the input File Parameter.
        self.addParameter(QgsProcessingParameterPoint(
            self.Outflowpoints,
            self.tr("Outflow Points"), None, False))

        self.addParameter(QgsProcessingParameterRasterLayer(
            self.DEM,
            self.tr("DEM"), None, False))
			
		# Better to write to a folder, so each catchment is stored in a folder 
		self.addParameter(QgsProcessingParameterRasterDestination(
            self.Catchments,
            self.tr("Catchments"),
            None, False))

    def processAlgorithm(self, parameters, context, feedback):
        outflowPoints = self.parameterAsFile(parameters, self.INPUT_POINTS, context)
        fileName, fileExtension = os.path.splitext(inputPoints)
		inputDEM = self.parameterAsFile(parameters, self.INPUT_DEM, context)
        fileNamePoints, fileExtensionPoints = os.path.splitext(outflowPoints)
		fileNameDEM, fileExtensionDEM =os.path.splitext(inputDEM)
        #print (inputFile)
        
		#Iterate over point features
		i = 0
		total = len(outflowPoints)
		print('Iterate over', total, 'points')
		for outflowpoint in outflowPoints.getFeatures():
			i = i + 1
			#print(i)
    
			#Get x and y coordinate from point feature
			geom = outflowpoint.geometry()
			p = geom.asPoint()
			x = p.x()
			y = p.y()
			#print(x,y)
    
			# Calculate catchment raster from point feature
			catchraster = processing.run("saga:upslopearea", {'TARGET':None,
                                        'TARGET_PT_X':x,
                                        'TARGET_PT_Y':y,
                                        'ELEVATION':INPUT_DEM,
                                        'SINKROUTE':None,
                                        'METHOD':0,'CONVERGE':1.1,
                                        'AREA':TEMP_RASTER})
			#Polygonize raster catchment
			catchpoly = processing.run("gdal:polygonize", {'INPUT':catchraster['AREA'],
										'BAND':1,
                                        'FIELD':'DN',
                                        'EIGHT_CONNECTEDNESS':False,
                                        'OUTPUT':TEMP_VECTOR})
			#Select feature with DN = 100
			result = processing.run("native:extractbyattribute", {'INPUT':catchpoly['OUTPUT'],
                                    'FIELD':'DN',
                                    'OPERATOR':0,
                                    'VALUE':'100',
                                    'OUTPUT':'memory:'})
			#percentage = (i/total) * 100
			#print('%.1f' % percentage, '% done\r'),
		QgsProject.instance().addMapLayer(result['OUTPUT'])
        return {self.OUTPUT: dest_id}        
        
        

