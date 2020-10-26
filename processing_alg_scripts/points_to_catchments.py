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
import os
from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsCoordinateTransformContext,
    QgsExpression,
    QgsFeatureRequest,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingOutputMultipleLayers,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingUtils,
    QgsVectorFileWriter,
)
from processing.tools.system import mkdir
from qgis import processing


class PointsToCatchmentsAlgorithm(QgsProcessingAlgorithm):
    """
    Algorithm for calculating catchments for a set of locations...
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT_POINTS = 'INPUT_POINTS'
    INPUT_FIELD = 'INPUT_FIELD'
    INPUT_DEM = 'INPUT_DEM'
    LOAD_RESULTS = 'LOAD_RESULTS'
    OUTPUT_DIR = 'OUTPUT'
    OUTPUT_TYPE = 'OUTPUT_TYPE'
    OUTPUT_LAYERS = 'OUTPUT_LAYERS'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PointsToCatchmentsAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'catchments_for_points'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Catchments for Points')

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
        return 'hydrology'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr(
            """Create catchment areas for points and DEM...
            
            <a href="https://youtu.be/Hqc_1CMadhA"> See how it works.</a>
            
            Parameters:
            
             * <b>Input points</b> (required) - locations for catchment areas calculation. Users have an option to run the algorithm only for selected features.
             * <b>Unique field</b> (optional) - field with unique values that can be used to name the resulting catchments. If blank, catchments will be auto-numbered.
             * <b>Input DEM</b> (required) - digital elevation model for catchment calculation.
             * <b>Output type</b> (optional) - GPKG (single file for all results) / ESRI Shapefile (multiple files).
             * <b>Load result catchments</b> (optional) - switch for loading the results, default is True
             * <b>Output directory</b> (optional) - where the results will be saved.
             
            Results:
            
             * OUTPUT_DIRECTORY
             * OUTPUT_LAYERS - list of resulting catchment layers
            """
        )

    def helpUrl(self):
        return "https://youtu.be/Hqc_1CMadhA"

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT_POINTS,
                self.tr('Input points layer'),
                [QgsProcessing.TypeVectorPoint],
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.INPUT_FIELD,
                self.tr('Unique field'),
                None,
                self.INPUT_POINTS,
                QgsProcessingParameterField.Any,
                False,  # allow multiple
                True,  # optional
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT_DEM,
                self.tr('Input DEM'),
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT_DIR,
                self.tr('Output directory'),
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.OUTPUT_TYPE,
                self.tr('Output type'),
                QgsVectorFileWriter.supportedFormatExtensions()[:2],
                False,
                'gpkg',
                False,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.LOAD_RESULTS,
                self.tr('Load result catchments'),
                True
            )
        )
        self.addOutput(
            QgsProcessingOutputMultipleLayers(
                self.OUTPUT_LAYERS,
                self.tr('Output layers')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
        source_pts = self.parameterAsSource(parameters, self.INPUT_POINTS, context)
        input_field = self.parameterAsString(parameters, self.INPUT_FIELD, context)
        source_dem = self.parameterAsRasterLayer(parameters, self.INPUT_DEM, context)
        out_directory = self.parameterAsString(parameters, self.OUTPUT_DIR, context)
        out_type_nr = self.parameterAsInt(parameters, self.OUTPUT_TYPE, context)
        out_type = QgsVectorFileWriter.supportedFormatExtensions()[:2][out_type_nr]
        to_gpkg = out_type == 'gpkg'
        load_results = self.parameterAsBool(parameters, self.LOAD_RESULTS, context)
        if source_pts is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_POINTS))
        if source_dem is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT_DEM))

        feedback.pushInfo("Input data loaded! Creating catchments...")
        feedback.setProgress(1)

        unique_field = input_field if input_field else ""
        if unique_field:
            field_idx = source_pts.fields().lookupField(unique_field)
            unique_values = source_pts.uniqueValues(field_idx)
        else:
            unique_values = [f.id() for f in source_pts.getFeatures()]

        feedback.pushInfo(f"Creating directory: {out_directory}")
        mkdir(out_directory)
        bname = f"catchment{'s' if to_gpkg else ''}"
        output_basename = os.path.join(out_directory, bname)

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total_nr = len(unique_values)
        total = 100. / total_nr if source_pts.featureCount() else 1
        output_layers = []

        for i, unique_value in enumerate(unique_values):
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            table = f"catchment_{unique_value}" if to_gpkg else ""
            file_mod = "" if to_gpkg else f"_{unique_value}"
            filename = f"{output_basename}{file_mod}"
            destination = f"{filename}.{out_type}"
            output_uri = destination + (f"|layername={table}" if to_gpkg else "")
            feedback.pushInfo(self.tr('Creating layer: {}').format(destination))

            if unique_field:
                req_filter = f"{QgsExpression.quotedColumnRef(unique_field)}={QgsExpression.quotedValue(unique_value)}"
                req = QgsFeatureRequest().setFilterExpression(req_filter)
            else:
                req = QgsFeatureRequest(unique_value)  # feature id

            for source_pt in source_pts.getFeatures(req):
                if feedback.isCanceled():
                    break

                # Get x and y coordinate from point feature
                geom = source_pt.geometry()
                p = geom.asPoint()
                x = p.x()
                y = p.y()

                feedback.pushInfo('Creating upslope area for point ({:.2f}, {:.2f}) - {} of {}'.format(
                    x, y, i + 1, total_nr))

                # Calculate catchment raster from point feature
                catchraster = processing.run(
                    "saga:upslopearea",
                    {
                        'TARGET': None,
                        'TARGET_PT_X': x,
                        'TARGET_PT_Y': y,
                        'ELEVATION': source_dem,
                        'SINKROUTE': None,
                        'METHOD': 0, 'CONVERGE': 1.1,
                        'AREA': 'TEMPORARY_OUTPUT'
                    },
                    context=context,
                    feedback=feedback,
                    )

                # Polygonize raster catchment
                catchpoly = processing.run(
                    "gdal:polygonize",
                    {
                        'INPUT': catchraster["AREA"],
                        'BAND': 1,
                        'FIELD': 'DN',
                        'EIGHT_CONNECTEDNESS': False,
                        'OUTPUT': 'TEMPORARY_OUTPUT'
                    },
                    context=context,
                    feedback=feedback,
                )

                # Select features having DN = 100
                catchpoly_lyr = QgsProcessingUtils.mapLayerFromString(catchpoly["OUTPUT"], context=context)
                catchpoly_lyr.selectByExpression('"DN"=100')

                options = QgsVectorFileWriter.SaveVectorOptions()
                options.driverName = "GPKG" if to_gpkg else "ESRI Shapefile"
                options.layerName = table
                options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
                options.onlySelectedFeatures = True
                trans_context = QgsCoordinateTransformContext()

                write_result, error_message = QgsVectorFileWriter.writeAsVectorFormatV2(
                    catchpoly_lyr, destination, trans_context, options)
                if write_result != 0:
                    feedback.pushInfo(f"Initial write failed: {error_message}")
                    # retry with option for creating the dataset
                    options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteFile
                    write_result, error_message = QgsVectorFileWriter.writeAsVectorFormatV2(
                        catchpoly_lyr, destination, trans_context, options)

                feedback.pushInfo(f"Final write attempt: {write_result} == 0 -> SUCCESS or {error_message}")

                output_layer = QgsProcessingUtils.mapLayerFromString(output_uri, context=context)
                output_layers.append(output_uri)
                if load_results:
                    context.temporaryLayerStore().addMapLayer(output_layer)
                    context.addLayerToLoadOnCompletion(
                        output_layer.id(),
                        QgsProcessingContext.LayerDetails(
                            table if to_gpkg else f"catchment {unique_value}",
                            context.project(),
                            self.OUTPUT_LAYERS
                        )
                    )

            feedback.setProgress(int((i + 1) * total))

        return {self.OUTPUT_DIR: out_directory, self.OUTPUT_LAYERS: output_layers}
