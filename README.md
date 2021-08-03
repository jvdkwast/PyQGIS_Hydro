# PyQGIS_Hydro
Hydrological tools for PyQGIS.

Each tool is an individual processing plugin. To install: add the folder of the tool to your QGIS profile folder under python\plugins. Don't copy the root of the repository there. It will not work.

* Iterate point features and calculate a catchment for each feature. Results in polygon shapefiles of the catchment of each point. The polygons are saved in an output folder.

The processing script has an improved interface has an option to choose the field with catchment ID's and the output format (shp or gpkg).

Video for installation: https://youtu.be/e738L1MueeM

Note that with the new dependencies in QGIS this will not work.
For work around see: https://youtu.be/B1LMOOPMWgo
And also see: https://github.com/qgis/QGIS/issues/44514
