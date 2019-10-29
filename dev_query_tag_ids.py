#-------------------------------------------------------------------------------
# Name:        query_tag_ids.py
# Created:     8/30/2018

# Select encounters from WTG_GUI as a Query Layer
#
# Parameters provided by Tool Validation
#
#-------------------------------------------------------------------------------
import arcpy
from arcpy import env
from datetime import datetime
import sys
import traceback

sr = arcpy.SpatialReference(4326)

# input params
devices = arcpy.GetParameterAsText(3)
combine = arcpy.GetParameterAsText(4)
minDate = arcpy.GetParameterAsText(5)
# ArcTool validation code returns a <string of a dict>
#devices = "{'04175': '792', '00827': '786'}"
# eval() converts to Real dict

try:
    devDict = eval(devices)
    c0 = "SELECT * FROM geodata.v_select_points \
          WHERE feature_type <> 'sample'"
    if minDate:
        #startDate = datetime.strptime(minDate, '%m/%d/%Y')
        c2 = ''.join([" AND timevalue > '", minDate, "'"])
    else:
        c2 = ''

    if combine == 'true':
        tagList = ','.join([str(v) for v in devDict.values()])
        c1 = ''.join(['tag_id IN (', tagList, ')'])
        sqlSelect = '{0} AND {1}{2}'.format(c0,c1,c2)
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
            c1 = ''.join(['tag_id = ', str(devID)])
            layerName = 'q_' + str(ptt).zfill(5)
            sqlSelect = '{0} AND {1}{2}'.format(c0,c1,c2)
            q_layer = arcpy.MakeQueryLayer_management("Database Connections/wtg_gdb.sde",
                                                    layerName,
                                                    sqlSelect,
                                                    "fid",
                                                    "POINT",
                                                    "4326",
                                                    sr)
            out_name = 'a'+layerName[1:7]
            f_layer = arcpy.FeatureToPoint_management (layerName, out_name)

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

