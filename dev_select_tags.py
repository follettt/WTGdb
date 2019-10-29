#-------------------------------------------------------------------------------
# Name:        select_tags.py
# Created:      7/20/2016
# Updated:      12/12/2017

# Select encounters from WTG_GUI
#
# Parameters: provided by Tool Validation code
#
"""Superseded by dev_query_tags"""
#-------------------------------------------------------------------------------
import arcpy
#from arcpy import env
import sys
import traceback

# local imports
import dev_f_utils as f_utils
import dev_db_utils as db_utils

sr = arcpy.SpatialReference(4326)

mxd = arcpy.mapping.MapDocument('CURRENT')

# input params
devices = arcpy.GetParameterAsText(3)
combine = arcpy.GetParameterAsText(4)
#devices = "{'04175': '792', '00827': '786'}"
#combine = False

# devices from validation code is string quoted dict; eval() turns it back into a dict
devDict = eval(devices)

# query layer style
tagList = [int(v) for v in devDict.values()]
tagTup = tuple(tagList)
sqlSelect ="SELECT * FROM geodata.v_select_points WHERE tag_id in {0}".format(tagTup)
layerName = 'test_view'
arcpy.MakeQueryLayer_management("Database Connections/wtg_gdb.sde",
                                            layerName,
                                            sqlSelect,
                                            "feature_id",
                                            "POINT",
                                            "4326",
                                            sr)

lyr = arcpy.mapping.Layer(layerName)
data_frame = arcpy.mapping.ListDataFrames(mxd)[0]
mxd.activeView = data_frame.name
arcpy.mapping.AddLayer(data_frame, lyr, 'TOP')

### Arc is NOT happy with this view ****************************************
##view = 'R:\\Data\\GIS_Data\\wtg_gdb.sde\\wtg_gdb.geodata.v_select_points'
###************************************************************************
### make new FC style
##tempEncounter = 'in_memory\\enc_Master'
##viewCols = [('feature_id','INTEGER'),
##            ('timevalue','DATE'),
##            ('animal_name','TEXT'),
##            ('species_name','TEXT'),
##            ('ptt','INTEGER'),
##            ('tag_name','TEXT'),
##            ('tag_class','TEXT'),
##            ('feature_type','TEXT'),
##            ('tag_id','INTEGER'),
##            ('animal_id','INTEGER'),
##            ('quality','INTEGER'),
##            ('latitude','DOUBLE'),
##            ('longitude','DOUBLE')
##           ]
##view_FC = arcpy.CreateFeatureclass_management('in_memory', tempEncounter,
##                'POINT', None, 'DISABLED', 'DISABLED', sr)
##f_names = []
### First add shape
##f_names.append("SHAPE@")
### add fields
##for f_name, f_type in viewCols:
##    arcpy.AddField_management(view_FC, f_name, f_type)
##    f_names.append(f_name)
###*****************************************************************************


### define SQL clause parts
##c1 = '"device_id" = '
##c2 = '"timevalue" >= '
##c3 = '"timevalue" <= '
##
##try:
##
##    # list for names of FC's created
##    out_list = []
##    # build new FC or append it?
##    first = True
##
##    tempName = 'in_memory\\enc_Select'
##    tempSort = 'in_memory\\enc_Sort'
##
##    for ptt, devID in devDict.iteritems():
##        # find startdate, stopdate
##        start, end = f_utils.getStartStop(int(devID))
##        # SQL query
##        sqlClause = "{0}{1} AND {2} timestamp '{3}' AND {4} timestamp '{5}'".format(c1,devID,c2,start,c3,end)
##        # select into temp FC
##        tempFC = arcpy.Select_analysis(inFeats, tempName, sqlClause)
##        arcpy.env.overwriteOutput = True
##        # define output FC name
##        if combine == 'true':
##            out_name = 'p_AllTags'
##            if first:
##                # sort tempFC into new FC
##                arcpy.Sort_management(tempFC, out_name, [["timevalue","ASCENDING"]],"UR")
##                first = False
##            else:
##                # sort tempFC into another temp
##                arcpy.Sort_management(tempFC, tempSort, [["timevalue","ASCENDING"]],"UR")
##                # Append to out FC
##                with arcpy.da.SearchCursor(tempSort, f_utils.fieldLists.pointFields) as sCur:
##                    with arcpy.da.InsertCursor(out_name, f_utils.fieldLists.pointFields) as iCur:
##                        for sRow in sCur:
##                            iCur.insertRow(sRow)
##        else:
##            out_name = 'p_' +ptt.zfill(5)
##            if arcpy.Exists(out_name):
##                out_name = f_utils.uniqName(out_name)
##                # sort tempFC into new "p_number" in GDB
##                arcpy.Sort_management(tempFC, out_name, [["timevalue","ASCENDING"]],"UR")
##                # index FeatureID
##                arcpy.AddIndex_management (out_name, "featureid", 'fid01', 'UNIQUE', 'ASCENDING')
##        # add new FC to list
##        out_list.append(out_name)
##
##except arcpy.ExecuteError:
##    msgs = arcpy.GetMessages(2)
##    arcpy.AddError(msgs)
##    print msgs
##except:
##    tb = sys.exc_info()[2]
##    tbinfo = traceback.format_tb(tb)[0]
##    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
##    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
##    arcpy.AddError(pymsg)
##    arcpy.AddError(msgs)
##    print pymsg + "\n"
##    print msgs

##    return(out_list)

# when executing as a standalone script get parameters from sys
##if __name__ == '__main__':
##    # When run from tool, devices is generated in tool Validation
##    # Defaults when no configuration is provided
##    defaults_tuple = (
##                    ('devices', "{'00841': '850',}"),
##                    ('combine', 'false')
##                    )
##    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
##    #main(mode='script', **defaults)
##    main(**defaults)

