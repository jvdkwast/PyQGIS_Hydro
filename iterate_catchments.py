#Calculate from selected point vector layer
outflowpoints = iface.activeLayer()
print(outflowpoints.name())

#Iterate over point features
i = 0
total = len(outflowpoints)
print('Iterate over', total, ' points')
for outflowpoint in outflowpoints.getFeatures():
    i = i + 1
    #print(i)
    print((i/total)*100, '% done\n')
    #Get x and y coordinate from point feature
    geom = outflowpoint.geometry()
    p = geom.asPoint()
    x = p.x()
    y = p.y()
    #print(x,y)
    
    # Calculate catchment raster from point feature
    processing.run("saga:upslopearea", {'TARGET':None,
                                        'TARGET_PT_X':x,
                                        'TARGET_PT_Y':y,
                                        'ELEVATION':'Z:/QGIS_Exercises/Exercise_5/dem_filled.sdat',
                                        'SINKROUTE':None,
                                        'METHOD':0,'CONVERGE':1.1,
                                        'AREA':'C:/Users/hansa/AppData/Local/Temp/processing_de4cbd791bd949f38667077db58987fb/1f97df2d23b94fa5bb956d8c1628ba4a/AREA.sdat'})
    
    #Polygonize raster catchment
    processing.run("gdal:polygonize", {'INPUT':'C:/Users/hansa/AppData/Local/Temp/processing_de4cbd791bd949f38667077db58987fb/1f97df2d23b94fa5bb956d8c1628ba4a/AREA.sdat',
                                        'BAND':1,
                                        'FIELD':'DN',
                                        'EIGHT_CONNECTEDNESS':False,
                                        'OUTPUT':'Z:/QGIS_exercises/Exercise_5/catchpoly.shp'})
    #Select feature with DN = 100
    result = processing.run("native:extractbyattribute", {'INPUT':'Z:/QGIS_exercises/Exercise_5/catchpoly.shp',
                                                 'FIELD':'DN',
                                                 'OPERATOR':0,
                                                 'VALUE':'100',
                                                 'OUTPUT':'memory:'})
QgsProject.instance().addMapLayer(result['OUTPUT'])
