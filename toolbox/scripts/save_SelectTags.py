# f_SelectTags.py

import arcpy
from arcpy import env
import os
import sys
import traceback

# local imports
import f_utils
import s_utils

sr = arcpy.SpatialReference(4326)
env.overwriteOutput = True

def main(devices=None):

    # something being done to list?
    devDict = eval(devices)
    inFeats = 'R:\\Data\\GIS_Data\\mmi_sde.sde\\mmi_sde.sde.telemetry\\mmi_sde.sde.encounter'
    tempName = 'in_memory\\enc_Select'

    out_list = []
    try:
        for ptt, devID in devDict.iteritems():
            # define output FC name
            outName = f_utils.uniqName('p_' +ptt.zfill(5))
            # define query string
            sqlClause = '"device" = '+ devID
            # select into temp FC
            tempFC = arcpy.Select_analysis(inFeats,tempName,sqlClause)
            # sort tempFC into  new FC in GDB
            arcpy.Sort_management(tempFC, outName, [["timevalue","ASCENDING"]],"UR")
            # index FeatureID
            arcpy.AddIndex_management (outName, "featureid", 'fid01', 'UNIQUE', 'ASCENDING')
            out_list.append(outName)

    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        print msgs
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        # Concatenate information together concerning the error into a message string
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        # Return python error messages for use in script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        # Print Python error messages for use in Python / Python Window
        print pymsg + "\n"
        print msgs

    return(out_list)

# when executing as a standalone script get parameters from sys
if __name__ == '__main__':
    # Defaults when no configuration is provided
    defaults_tuple = (('devices', "{}"))

    defaults = s_utils.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)

