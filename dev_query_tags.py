#-------------------------------------------------------------------------------
# Name:        query_tags.py
# Created:     12/14/2017

# Select encounters from WTG_GUI as a Query Layer
#
# Parameters: provided by Tool Validation code
#
#-------------------------------------------------------------------------------
import arcpy
from arcpy import env
from datetime import datetime
import sys
import traceback

#local imports
#import dev_f_utils as f_utils
import dev_db_utils as dbutil

sr = arcpy.SpatialReference(4326)

# Code to work with desktop
#mxd = arcpy.mapping.MapDocument('CURRENT')
#df = arcpy.mapping.ListDataFrames(mxd)[0]
#mxd.activeView = df.name
env.overwriteOutput = True

# input params
devices = arcpy.GetParameterAsText(3)
combine = arcpy.GetParameterAsText(4)
minDate = arcpy.GetParameterAsText(5)
#devices = "{'04175': '792', '00827': '786'}"

conn = dbutil.getDbConn(db='wtg_gdb')
try:
    # ArcTool validation code returns a string of a dict
    # eval() converts to actual dict
    devDict = eval(devices)
    tagList = tuple([int(v) for v in devDict.values()])
    if minDate:
        startDate = datetime.strptime(minDate, '%m/%d/%Y')

    if combine == 'true':
        sqlSelect ="SELECT * FROM geodata.v_select_points \
                    WHERE tag_id IN {0} \
                    AND feature_type <> 'sample' \
                    AND timevalue > '{1}'".format(tagList, startDate)

        layerName = 'q_tags'
        # View uses fid as a "sacrificial" key for Arcmap to ingest
        q_layer = arcpy.MakeQueryLayer_management("Database Connections/wtg_gdb.sde",
                                                    layerName,
                                                    sqlSelect,
                                                    "fid",
                                                    "POINT",
                                                    "4326",
                                                    sr)
        # Persist to feature class
        out_name = 'a'+layerName[1:7]
        f_layer = arcpy.FeatureToPoint_management (layerName, out_name)
    else:
        for ptt, devID in devDict.iteritems():
            layerName = 'q_' + str(ptt).zfill(5)
            sqlSelect ="SELECT * FROM geodata.v_select_points \
                        WHERE tag_id = {0} \
                        AND feature_type <> 'sample' \
                        AND timevalue > '{1}'".format(int(devID), startDate)
            q_layer = arcpy.MakeQueryLayer_management("Database Connections/wtg_gdb.sde",
                                                    layerName,
                                                    sqlSelect,
                                                    "fid",
                                                    "POINT",
                                                    "4326",
                                                    sr)
            out_name = 'a'+layerName[1:7]
            f_layer = arcpy.FeatureToPoint_management (layerName, out_name)

#    lyr = arcpy.mapping.Layer(out_name)
#    arcpy.mapping.AddLayer(df, lyr, 'TOP')
#    df.extent = lyr.getSelectedExtent()

except arcpy.ExecuteError:
    msgs = arcpy.GetMessages(2)
    arcpy.AddError(msgs)
    print msgs
except:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
    arcpy.AddError(pymsg)
    arcpy.AddError(msgs)
    print pymsg + "\n"
    print msgs

