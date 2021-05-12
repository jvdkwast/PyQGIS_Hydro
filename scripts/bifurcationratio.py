channels = "Z:/delineation_Rur/rur_channels_clip.shp"
vlayer = iface.addVectorLayer(channels, "channels", "ogr")
stats = "Z:/delineation_Rur/statistics.csv"

# Run Statistics by categories tool
result = processing.run("qgis:statisticsbycategories", {
    'INPUT':channels,
    'VALUES_FIELD_NAME':'',
    'CATEGORIES_FIELD_NAME':['ORDER'],
    'OUTPUT':stats
    })
    
statstable = iface.addVectorLayer(result['OUTPUT'], "stats", "ogr")

# Make a list with the count of channels per Strahler order
countList = []
for feature in statstable.getFeatures():
    countList.append(feature["count"])
    
# Calculate Bifurcation Ratio for each order except last one
BrList = []
Orders = len(countList) - 1
for order in range(0,Orders):
    Br = float(countList[order]) / float(countList[order + 1])
    print("The Bifurcation Ratio of order {} is {:.2f}".format(order+1,Br))
    BrList.append(Br)
    
# Calculate average Bifurcation Ratio
BrAverage = sum(BrList)/len(BrList)
print("The Average Bifurcation Ratio is {:.2f}".format(BrAverage))