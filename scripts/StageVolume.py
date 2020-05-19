from qgis.PyQt.QtCore import QVariant
def frange(start, stop, step):
    i = start
    while i < stop:
        yield i
        i += step

projectPath = "Z:/Volume/"
inputRasterDEM = "Z:/Volume/MineDem.tif"
demLayer = iface.addRasterLayer(inputRasterDEM,"DEM","gdal")
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
for level in frange(demMinimum,demMaximum + 1,increment):
    outTable = projectPath +"volume" + str(round(level*100.0))
    outTableDbf = outTable + ".dbf"
    processing.run("native:rastersurfacevolume", {'INPUT':demLayer,'BAND':1,'LEVEL':level,'METHOD':1,'OUTPUT_HTML_FILE':'TEMPORARY_OUTPUT','OUTPUT_TABLE':outTable + ".shp"})
    
    dbfTable = QgsVectorLayer(outTableDbf, outTable, "ogr")
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

processing.run("native:mergevectorlayers", {'LAYERS':dbfList,'CRS':None,'OUTPUT':projectPath + 'stagevolume.shp'})
vlayer = QgsVectorLayer(projectPath + 'stagevolume.dbf', "StageVolume", "ogr")
QgsProject.instance().addMapLayer(vlayer)