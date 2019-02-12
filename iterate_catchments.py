#Calculate from selected point vector layer
outflowpoints = iface.activeLayer()
DEM = 'Z:/QGIS_Exercises/Exercise_5/dem_filled.sdat'
TEMP_RASTER = 'C:/Users/hansa/AppData/Local/Temp/temp.sdat'
TEMP_VECTOR = 'C:/Users/hansa/AppData/Local/Temp/temp.shp'
print('Point feature layer:',outflowpoints.name())
print('Filled DEM layer:', DEM)
#Iterate over point features
i = 0
total = len(outflowpoints)
print('Iterate over', total, 'points')
for outflowpoint in outflowpoints.getFeatures():
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
                                        'ELEVATION':DEM,
                                        'SINKROUTE':None,
                                        'METHOD':0,'CONVERGE':1.1,
                                        'AREA':TEMP_RASTER})
    #Polygonize raster catchment
    catchpoly = processing.run("gdal:polygonize", {'INPUT':catchraster['AREA'],                                        'BAND':1,
                                        'FIELD':'DN',
                                        'EIGHT_CONNECTEDNESS':False,
                                        'OUTPUT':TEMP_VECTOR})
    #Select feature with DN = 100
    result = processing.run("native:extractbyattribute", {'INPUT':catchpoly['OUTPUT'],
                                                 'FIELD':'DN',
                                                 'OPERATOR':0,
                                                 'VALUE':'100',
                                                 'OUTPUT':'memory:'})
    percentage = (i/total) * 100
    print('%.1f' % percentage, '% done\r'),
QgsProject.instance().addMapLayer(result['OUTPUT'])
