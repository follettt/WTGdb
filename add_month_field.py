# add_month_field.py

""" INSTEAD how about creating the deploy-last featureclass right here?
    Add in tagtype, sex, haplo, month and locality
=======================================================
snippet to extract deploy and last from points

fields = ("FromLoc", "ToLoc", "ptt", "SHAPE@XY")
for ptt in pttList
    with arcpy.da.SearchCursor(in_layer, fields, None, sr, None, sql_clause) as sCur:
        row = sCur.next()
        # get begin & end dates
        startLoc = row[0]
        ptt = row[2]
        for row in sCur:
            if not row == None:
                if row[2] != ptt
                    ptt = row[2]
** NOT finished *****
                pass
        endLoc = row[1]

"""


import arcpy
from arcpy import env
from datetime import datetime
from os import path

# Local Imports
import dev_f_utils as util

# Set Geoprocessing environments
#mxd = arcpy.mapping.MapDocument("CURRENT")
#env.addOutputsToMap = True
#env.overwriteOutput = True

# Global vars
sr = arcpy.SpatialReference(4326)
fmt = '%m/%d/%Y %H:%M:%S'

# Parameters
in_layer  = arcpy.GetParameterAsText(0) #
ptt_field = arcpy.GetParameterAsText(1)
time_field = arcpy.GetParameterAsText(2)

arcpy.AddField_management(in_layer, 'month', 'INTEGER')
arcpy.AddField_management(in_layer, 'doy', 'INTEGER')
arcpy.AddField_management(in_layer, 'hourday', 'INTEGER')
f_names = [time_field, 'month', 'doy'] #,'hourday']

with arcpy.da.UpdateCursor(in_layer, f_names, None, sr) as uCur:
    for row in uCur:
        row_list = row
        timeVal = row[0]
        if type(timeVal) == datetime:
            row_list[-2] = timeVal.strftime('%m')
            row_list[-1] = timeVal.strftime('%j')

        else:
            arcpy.AddMessage(timeVal)
#        row_list, timeVal,  = [row, timeVal = row[0], row_list[-1] = timeVal.strftime('%m') for row in uCur]
        uCur.updateRow(row_list)



### get shape type
##descLayer = arcpy.Describe(in_layer)
##
### apply symbology
### Set layer that output symbology will be based on
##if descLayer.shapeType == 'Point':
##    symbologyLayer = util.symbolLayers.f_month_point
##elif descLayer.shapeType == 'Polyline':
##    symbologyLayer = util.symbolLayers.tr_month_track
##else:
##    symbologyLayer = None
### Apply the symbology from the symbology layer to the input layer
##arcpy.ApplySymbologyFromLayer_management (in_layer, symbologyLayer)


