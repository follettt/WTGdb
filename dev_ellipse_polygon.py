# dev_ellipse_polygon.py
import arcpy
from arcpy import env
from sys import exit

inLayer = arcpy.GetParameterAsText(0)
#outName = arcpy.GetParameterAsText(1)

sr = arcpy.SpatialReference(4326)
# Code to work with desktop
mxd = arcpy.mapping.MapDocument('CURRENT')
df = arcpy.mapping.ListDataFrames(mxd)[0]
mxd.activeView = df.name

env.workspace = 'in_memory\\'
env.addOutputsToMap = True
env.overwriteOutput = True

erase_land = 'R:\\Data\\GIS_Base\\Coast\\GSHHS\\GSHHS_high.shp'

# Feature To Polygon
poly_name = 'ellipse_poly'
ellPoly   = arcpy.FeatureToPolygon_management(inLayer, poly_name,
                            "","ATTRIBUTES","raw_selected")

# Erase polygon over land
erase_name = 'ellipse_poly_erase'
ellPolyErase = arcpy.Erase_analysis(ellPoly, erase_land, erase_name)

# Determine if multipart...MultipartToSinglepart tool
parts_name = 'ellipse_parts'
ellParts = arcpy.MultipartToSinglepart_management(ellPolyErase,parts_name)


