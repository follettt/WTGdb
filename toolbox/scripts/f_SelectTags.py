# f_SelectTags.py

import arcpy
from arcpy import env
import os
import sys
import traceback

# local imports
import f_utils
reload(f_utils)

sr = arcpy.SpatialReference(4326)

def main(devices=None, combine='false'):

    # ***************** something being done to list? because it's a dict?
    devDict = eval(devices)
    inFeats = 'R:\\Data\\GIS_Data\\mmi_sde.sde\\mmi_sde.sde.telemetry\\mmi_sde.sde.encounter'
    tempName = 'in_memory\\enc_Select'

    fields = f_utils.fieldLists.pointFields
    # list for names of FC's created
    out_list = []
    # define query elements
    c1 = '"device" = '
    # Eliminate Z class
    c2 = '"lc" > -4'
    c3 = '"timevalue" >= '
    c4 = '"timevalue" <= '
    try:
        if combine == 'true':
            loop = 0
            # define output FC name
            out_name = 'p_tag_group'
            sort_name = 'in_memory\\enc_Sort'
            if arcpy.Exists(out_name):
                out_name = f_utils.uniqName(out_name)
            for ptt, devID in devDict.iteritems():
                # find startdate
                start, end = f_utils.getStartStop(int(devID))
                sqlClause = "{0}{1} AND {2} AND {3} timestamp '{4}' AND {5} timestamp '{6}'".format(c1,devID,c2,c3,start,c4,end)
                # select into temp FC
                tempFC = arcpy.Select_analysis(inFeats, tempName, sqlClause)
                if loop == 0:
                    # sort tempFC into new FC
                    arcpy.Sort_management(tempFC, out_name, [["timevalue","ASCENDING"]],"UR")
                    loop += 1
                    continue
                # sort tempFC into another tempSorted
                arcpy.Sort_management(tempFC, sort_name, [["timevalue","ASCENDING"]],"UR")
                # append sorted into output
                with arcpy.da.InsertCursor(out_name, fields) as iCur:
                    with arcpy.da.SearchCursor(sort_name, fields, None, sr, False) as sCur:
                        for sRow in sCur:
                            iCur.insertRow(sRow)
                # add new FC to list
                out_list.append(out_name)
        elif combine == 'false':
            for ptt, devID in devDict.iteritems():
                # find startdate
                start, end = f_utils.getStartStop(int(devID))
                # define output FC name
                out_name = 'p_' +ptt.zfill(5)
                if arcpy.Exists(out_name):
                    out_name = f_utils.uniqName(out_name)
                sqlClause = "{0}{1} AND {2} AND {3} timestamp '{4}' AND {5} timestamp '{6}'".format(c1,devID,c2,c3,start,c4,end)
                # select into temp FC
                tempFC = arcpy.Select_analysis(inFeats, tempName, sqlClause)
                # sort tempFC into new "p_number" in GDB
                arcpy.Sort_management(tempFC, out_name, [["timevalue","ASCENDING"]],"UR")
                # index FeatureID
                arcpy.AddIndex_management (out_name, "featureid", 'fid01', 'UNIQUE', 'ASCENDING')
                # add new FC to list
                out_list.append(out_name)

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

        return(out_list)

# when executing as a standalone script get parameters from sys
if __name__ == '__main__':
    # Defaults when no configuration is provided
    defaults_tuple = (
                    ('devices', "{'00847': '625'}"),
                    ('combine','false')
                    )

    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)

