# Calculate concentration time with Kirpich equation (SI units)

# Use the selected layer (firstlastz)
layer = iface.activeLayer()

# define the constants
k = 0.0195
const1 = 0.77
const2 = -0.385

# retrieve the elevation field
elevation = layer.fields().indexFromName('Z_1')

# calculate the elevation difference
dz = layer.maximumValue(elevation) - layer.minimumValue(elevation)

# retrieve the length of the river (distance field)
length = layer.fields().indexFromName('distance')

# Select the largest value, which is the length of the river
dx = layer.maximumValue(length)

# Calculate S
S = dz / dx

# Calculate tc
tc = k * (dx ** const1) * (S ** const2)

# Print the results to the screen
print('k = ', k)
print('L = ', dx, ' m')
print('S = ', S, ' m/m')
print('tc =', tc, ' minutes')
