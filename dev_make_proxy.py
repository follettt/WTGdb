# dev_make_proxy.py
import arcpy
from arcpy import env
#from sys import exit

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

# Shapefiles on MMIDATA
erase_land = 'R:\\Data\\GIS_Base\\Coast\\GSHHS\\GSHHS_high.shp'
select_land = 'R:\\Data\\GIS_Base\\Coast\\NA_full.shp'
dist_land = 'R:\\Data\\GIS_Base\\Coast\\NA_full_Line.shp'

# select only the ellipses that overlap shoreline

# ***************"Invalid input" --> need to strip "in_memory\" from name [10:]
#arcpy.SelectLayerByLocation_management(ell_temp_name,"COMPLETELY_WITHIN",
#                                       select_land,"","NEW_SELECTION", "INVERT")
#*******************************************************
#ellipse_name = arcpy.CreateUniqueName('ellipse_line')
#ell_select = arcpy.Select_analysis(ell_temp, ellipse_name)

# *****OR construct Point from SearchCursor?
#pt = arcpy.Point()
#arcpy.CopyFeatures_management(pt, output_name)

#--------------------------------------------------------------------------------

# Revert to mxd's default GDB
arcpy.ClearEnvironment("workspace")

# create new FC to receive new points
proxy_name = 'proxy_temp'
proxy_file = arcpy.CreateFeatureclass_management(None, proxy_name,"POINT",
                                                None,"DISABLED","DISABLED",sr)
proxy_fields = [('animal_id', 'LONG'),
                 ('tag_id','LONG'),
                 ('timevalue','DATE'),
                 ('feature_type','TEXT'),
                 ('quality','LONG'),
                 ('longitude','DOUBLE'),
                 ('latitude','DOUBLE'),
                 ('replace_fid','LONG'),
                 ('source','TEXT')]
f_names = []
f_names.append("SHAPE")
# add fields
for f_name, f_type in proxy_fields:
    arcpy.AddField_management(proxy_file, f_name, f_type)
    f_names.append(f_name)

# encounter fields ['animal_id','tag_id','timevalue','quality']

env.workspace = 'in_memory\\'
# InsertCursor to insert new proxy features
with arcpy.da.InsertCursor(proxy_file, proxy_fields) as proxyCur:
# for each ellipse, go through steps to build a proxy location
    ellipse_fields = ['SHAPE','feature_id','longitude','latitude','semi_major',
                        'semi_minor','ellipse','gdop','lon2','lat2']
    with arcpy.da.SearchCursor(land_selected, ellipse_fields, None, sr,
                                False, None) as ellCur:
            for row in ellCur:
# 1 - Feature To Polygon
                poly_name = 'ellipse_poly'
                ellPoly   = arcpy.FeatureToPolygon_management(ellLine, poly_name,
                                                "","ATTRIBUTES","valid_selected")

# 2 - Erase polygon over land
                erase_name = 'ellipse_poly_erase'
                ellPolyErase = arcpy.Erase_analysis(ellPoly, erase_land, erase_name)
                with arcpy.da.SearchCursor(ell_poy_erase, ellipse_fields,
                                            None, sr, False, None) as polyCur:
                    pass

# determine if multipart...MultipartToSinglepart tool

# 4 - Write centroids to featureclass
                candidate = arcpy.FeatureToPoint_management(ellPolyErase, outName)
                arcpy.AddXY_management(candidate)



"""
