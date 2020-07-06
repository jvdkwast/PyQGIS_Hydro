# Calculate concentration time with Kirpich equation (SI units)
layer = iface.activeLayer()
k = 0.0195
const1 = 0.77
const2 = -0.385
elevation=layer.fields().indexFromName('Z_1')
dz = layer.maximumValue(elevation) - layer.minimumValue(elevation)
length = elevation=layer.fields().indexFromName('distance')
dx = layer.maximumValue(length)
S = dz / dx
tc = k * (dx ** const1) * (S ** const2)
print('k = ', k)
print('L = ', dx, ' m')
print('S = ', S, ' m/m')
print('tc =', tc, ' minutes')
