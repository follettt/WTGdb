# extract_habitat_values.py
import arcpy
arcpy.CheckOutExtension("spatial")
from arcpy import env
env.addOutputsToMap = False
env.overwriteOutput = True

# Tool parameters
point_layer = arcpy.GetParameterAsText(0)
poly_layers = arcpy.GetParameterAsText(1)
poly_list = poly_layers.split(";")
raster_layers = arcpy.GetParameterAsText(2)
raster_list = raster_layers.split(";")
near_layers = arcpy.GetParameterAsText(3)
near_list = near_layers.split(";")

poly_dict = {'GSHHS_Low_Buf50k':"'Inside'",
             'HI_Buffer50km':"'HI'",
             'AK_Buffer50km':"'SEAK'"}
raster_dict = {'nepac1':['depth','depth_m'],
               'nepac1_slope':['slope','slope_deg'],
               'nepac1_aspect':['aspect','aspect_deg']}
near_dict = {'Contour_nepac':['isobath_dist_m','DeleteMe'],
             'cntry_06':['shore_dist_m','shore_angle_deg']}
# clear selections
arcpy.SelectLayerByAttribute_management(point_layer,'CLEAR_SELECTION')

# add buffer field
arcpy.AddField_management(point_layer,"buffer50km","Text","","",16)
# set default value to "Outside"
arcpy.CalculateField_management(point_layer,"buffer50km","'Outside'","PYTHON")
for poly in poly_list:
    # select points in polygon
    arcpy.SelectLayerByLocation_management(point_layer,"INTERSECT",poly)
    # find value to insert for selected points
    poly_name = poly_dict.get(poly)
    # insert value
    arcpy.CalculateField_management(point_layer,"buffer50km",poly_name,"PYTHON")
# clear selections
arcpy.SelectLayerByAttribute_management(point_layer,'CLEAR_SELECTION')

# extract point values
in_name = point_layer
for raster in raster_list:
    # new output feature class
    out_name = ''.join([in_name,'_',raster_dict.get(raster)[0]])
    # field name for extracted values
    field_name = raster_dict.get(raster)[1]
    out_file = arcpy.gp.ExtractValuesToPoints_sa(in_name,raster,out_name,True,"VALUE_ONLY")
    # rename default extract field
    arcpy.AlterField_management(out_file,'RASTERVALU',field_name,
                                "","","","NON_NULLABLE","false")
    in_name = out_name

# get distances
for layer in near_list:
    # find name for distance field
    near_field = near_dict.get(str(layer))[0]
    # find name for angle field
    angle_field = near_dict.get(str(layer))[1]
    # run Near tool
    arcpy.Near_analysis(in_name,layer,None,'NO_LOCATION','ANGLE','GEODESIC')
    # rename new fields
    arcpy.AlterField_management(in_name,'NEAR_DIST',near_field,
                                    "","","","NON_NULLABLE","false")
    arcpy.AlterField_management(in_name,'NEAR_ANGLE',angle_field,
                                    "","","","NON_NULLABLE","false")
    # delete unneeded fields
    arcpy.DeleteField_management(in_name,"NEAR_FID")
    arcpy.DeleteField_management(in_name,"DeleteMe")






