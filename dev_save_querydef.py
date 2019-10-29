# dev_make_proxy.py
import arcpy
from arcpy import env
#from sys import exit

inLayer = arcpy.GetParameterAsText(0)

sr = arcpy.SpatialReference(4326)
# Code to work with desktop
mxd = arcpy.mapping.MapDocument('CURRENT')
df = arcpy.mapping.ListDataFrames(mxd)[0]
mxd.activeView = df.name

#env.workspace = 'in_memory\\'
arcpy.ClearEnvironment("workspace")
env.addOutputsToMap = True
env.overwriteOutput = True

# save selections to local FC
out_name = 'sel'+inLayer[1:7]
raw_selected = arcpy.FeatureToPoint_management (inLayer, out_name)

# Step through the locations and decide what to do with them





