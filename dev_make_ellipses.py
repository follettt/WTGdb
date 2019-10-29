# dev_make_proxy.py
import arcpy
from arcpy import env
from sys import exit

inLayer = arcpy.GetParameterAsText(0) # from Query Layer
#outName = arcpy.GetParameterAsText(1)

sr = arcpy.SpatialReference(4326)
# Code to work with desktop
mxd = arcpy.mapping.MapDocument('CURRENT')
df = arcpy.mapping.ListDataFrames(mxd)[0]
mxd.activeView = df.name

env.workspace = 'in_memory\\'
env.addOutputsToMap = True
env.overwriteOutput = True

# save selections to temporary FC
select_name = 'raw_selected'
sql_where = ''#'"semi_major" > 0 AND "semi_major" < 100000'
# Filter out unreasonable error radius
raw_selected = arcpy.Select_analysis(inLayer, select_name, sql_where)

# build ellipses
ellipse_name = 'ellipse_temp'
ell_temp = arcpy.TableToEllipse_management(select_name, ellipse_name,
                "longitude","latitude",
                #"semi_major","semi_minor",
                "error_radius","error_radius",
                "METERS",
                "ellipse","DEGREES","feature_id",sr)

featList = []
# iterate through ellipses
for feat in featList:

    sql_where = "{0}{1}".format('"feature_id" = ', feat)
    arcpy.SelectLayerByAttribute_management('ellipse_temp', "NEW_SELECTION", sql_where)
    # Line to polygon
    poly_name = "{0}_{1}".format('ellipse',str(feat))
    ellPoly = arcpy.FeatureToPolygon_management('ellipse_temp', poly_name,
                        "","ATTRIBUTES", 'ellipse_temp')
    # Erase polygon over land
    erase_name = "{0}_{1}".format('erase', str(feat))
    ellPolyErase = arcpy.Erase_analysis(poly_name, land_cover, erase_name)
