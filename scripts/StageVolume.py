from qgis.PyQt.QtCore import QVariant

# Python can not iterate with floats, therefore we define this function
# VP: Not needed if you iterate over list (see below)
# def frange(start, stop, step):
#     i = start
#     while i < stop:
#         yield i
#         i += step

# Set the path to your folder and the DTM file
current_project = QgsProject.instance()
projectPath = current_project.homePath()
inputRasterDEM = "GPKG:" + os.path.join(projectPath,"data_stagevolume.gpkg:DTM")
demLayer = iface.addRasterLayer(inputRasterDEM,"DEM","gdal")

# Calculate the statistics (min/max) of the DTM
stats = demLayer.dataProvider().bandStatistics(1)
demMinimum = stats.minimumValue
demMaximum = stats.maximumValue
print("min:",demMinimum,"m")
print("max:",demMaximum,"m")

# Determine the range
demRange = demMaximum - demMinimum
print("Elevation Difference:",demRange,"m")

# Set the increment for the iteration at 10% of the range
# VP: replaced commented line below by two new lines
# increment = demRange / 10.0
n_increments = 10
increment = demRange / n_increments
print("Increment:",increment)

# VP: Create a list of levels to iterate over using list comprehension
levels = [demMinimum + i * increment for i in range(n_increments + 1)]

# Create an empty list for the dbf files
dbfList = []

# Loop over the elevation range from the minimum to the maximum with the increment
# Replaced the line below by a for loop that steps through the items in levels
# for level in frange(demMinimum,demMaximum + 1,increment):
for level in levels:
    # Define the output table name
    outTable = projectPath +"volume" + str(round(level*100.0))
    outTableDbf = outTable + ".dbf"
    
    # Run the raster surface volume tool with the variables
    processing.run("native:rastersurfacevolume", {'INPUT':demLayer,'BAND':1,'LEVEL':level,'METHOD':1,'OUTPUT_HTML_FILE':'TEMPORARY_OUTPUT','OUTPUT_TABLE':outTable + ".shp"})
    
    # Read the table
    dbfTable = QgsVectorLayer(outTableDbf, outTable, "ogr")
    
    # Convert the volumes from m3 to km3
    for feature in dbfTable.getFeatures():
        VolumeKm3 = abs(feature["Volume"])/1000000000.0
    
    # Add the km3 field to the table
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

# Merge all dbf files into one
processing.run("native:mergevectorlayers", {'LAYERS':dbfList,'CRS':None,'OUTPUT':projectPath + 'stagevolume.shp'})
vlayer = QgsVectorLayer(projectPath + 'stagevolume.dbf', "StageVolume", "ogr")

# Add the result to the project
QgsProject.instance().addMapLayer(vlayer)
