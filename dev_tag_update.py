# Adapted from mmi_wtg version 8/2018
import arcpy
from datetime import datetime
from os import path
import traceback
import sys

# Import local utils
import dev_f_utils as f_utils
import dev_make_path
import dev_wtgfilter
# Code to work with desktop
#mxd = arcpy.mapping.MapDocument('CURRENT')
#df = arcpy.mapping.ListDataFrames(mxd)[0]
#mxd.activeView = df.name

# Set Geoprocessing environments
from arcpy import env
env.addOutputsToMap = False
env.overwriteOutput = True
homeDir = env.workspace
memDir = 'in_memory'
sr = arcpy.SpatialReference(4326)

# ******************************************************************************
##homeDir = 'C:\\CurrentProjects\\Hump18WA\\GIS\\2018WA_2.gdb'
##in_file = 'C:\\CurrentProjects\\Hump18WA\\GIS\\2018WA_2.gdb\\f_23041'
##minTime = 20
##maxSpeed = 14
# ******************************************************************************
in_file = arcpy.GetParameterAsText(0)
minTime = arcpy.GetParameterAsText(1)
maxSpeed = arcpy.GetParameterAsText(2)

in_name = path.basename(in_file)

# **** should incorporate into tool to look for correct file?
in_track = 'tr'+in_name[1:]

try:
    # Find deviceID & last HQ point (LC1+ if possible, otherwise LC0)
    fields = ["feature_id", "timevalue", "tag_id", "quality", "ptt"]
    where = '"quality" > -1'
    sqlClause = (None, 'ORDER BY "timevalue"')
    with arcpy.da.SearchCursor(in_file, fields, where, sr, False, sqlClause) as sCur:
        rowList = [row for row in sCur if row[3] > 0]
        if len(rowList)>0:
            lastPoint = [r for r in rowList][-1][0]
        else:
            sCur.reset()
            for lc in [0, -1, -2]:
                rowList = [row for row in sCur if row[3]==lc]
                if len(rowList)>0:
                    lastPoint = [r for r in rowList][-1][0]
                    break
                else:
                    continue
    tagID = rowList[0][2]
    ptt = rowList[0][4]
    arcpy.AddMessage(str(ptt)+' last HQ feature_id is '+str(lastPoint))

    # clause parts definition
    c0 = '"tag_id" = '
    c1 = '"feature_id" > '
    c2 = '"feature_id" >= '
    c4 = '"FromPoint" >= ' # for track file
    c5 = ' AND "feature_type" = '
    c6 = '"feature_id" = '
    c7 = ' AND "filtername" = "OK"'

    arcpy.AddMessage('deleting points >' + str(lastPoint))
    # remove locations > lastPoint from input points
    fields = ["feature_id", "feature_type"]
    # WHERE "feature_id" > 12345 AND "feature_type" = argos
    where = "{0}{1}{2}'{3}'".format(c1, lastPoint, c5, 'argos')
    with arcpy.da.UpdateCursor(in_file, fields, where) as uCur:
        for row in uCur:
           uCur.deleteRow()

    arcpy.AddMessage('deleting tracks >' + str(lastPoint))
    # remove affected segments from existing track
    # WHERE "FromPoint" >= 12345
    where = "{0}{1}".format(c4, lastPoint)
    py_track = '\\'.join([homeDir,in_track])
    if arcpy.Exists(py_track):
    #if arcpy.Exists('\\'.join([homeDir,in_track])):
        with arcpy.da.UpdateCursor(in_track, "FromPoint", where) as uCur:
#        with arcpy.da.UpdateCursor(py_track, "FromPoint", where) as uCur:
            for row in uCur:
               uCur.deleteRow()

    arcpy.AddMessage('obtaining new points from GDB')
    # obtain new locations from DB server
    ##where = "{0}{1} AND {2}{3}".format(c0, tagID, c2, lastPoint)
    sqlSelect ="SELECT * FROM geodata.v_select_points \
                WHERE tag_id = {0} \
                AND feature_type <> 'sample' \
                AND feature_id >= {1}".format(tagID, lastPoint)
                # v_select_points does the sorting...
    layerName = in_name + '_query'
    # View uses fid as a "sacrificial" key for Arcmap to ingest
    q_layer = arcpy.MakeQueryLayer_management("Database Connections/wtg_gdb.sde",
                                                layerName, sqlSelect, "fid",
                                                "POINT", "4326", sr)
    # *********** persist to GDB *** \\in_memory fails, WHY? *************
    out_name = ''.join(['c'+layerName[1:7]+'_new'])
    env.addOutputsToMap = True
    arcpy.FeatureToPoint_management (q_layer, out_name)
    env.addOutputsToMap = False

    # run Filter on updated points
    dev_wtgfilter.main(out_name, maxSpeed, minTime,
                        'true','false','false','false')
                       # land,  log,   new,   explode
    # trap for nothing filtered

    arcpy.AddMessage('creating temporary track')
    # create temporary track of new filtered update
#    WHERE "feature_id" >= 12345 AND "filtername" = 'OK'
#    where = "{0}{1}".format(c2, lastPoint)#, c7)
#    arcpy.SelectLayerByAttribute_management(out_name,"NEW_SELECTION", where)
    result = dev_make_path.main(out_name)
    new_track = result.getOutput(0)

    arcpy.AddMessage('deleting last HQ from new points')
    # drop first point from update
    # WHERE "feature_id" = 12345
    where = "{0}{1}".format(c6, lastPoint)
    with arcpy.da.UpdateCursor(in_file, "feature_id", where) as uCur:
        for row in uCur: #if row[0] == lastPoint: # search for lastPoint?
            uCur.deleteRow()
            break
    arcpy.AddMessage('appending new points & tracks')
    # append points
    arcpy.Append_management(out_name, in_file, "NO_TEST")  # , {field_mapping})
    # append track
    arcpy.Append_management(new_track, in_track, "NO_TEST")  # , {field_mapping})
    # clean up
    if arcpy.Exists(out_name):
        arcpy.Delete_management(out_name)
    if arcpy.Exists(out_name+'_log'):
        arcpy.Delete_management(out_name+'_log')
    if arcpy.Exists(new_track):
        arcpy.Delete_management(new_track)

    arcpy.AddMessage('Finished with updates')

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

    #load raw updates back to input file <filtered>
##    sqlClause = (None, 'ORDER BY "timevalue"')
##    with arcpy.da.InsertCursor(in_file, f_utils.fieldLists.pointFields) as iCur:
##        with arcpy.da.SearchCursor(out_name, f_utils.fieldLists.pointFields,
##                                    None, sr, sqlClause) as sCur:
##            if f_utils.curPop(sCur)>0:
##                sCur.reset()
##                sCur.next() # skip first row (last LC>0)
##                for row in sCur:
##                    iCur.insertRow(row)
##            else:
##                arcpy.AddMessage('*********** SearchCursor is empty, Why?? ************')




##
##        #load new track to existing
##        if arcpy.Exists(new_track):
##            sqlClause = (None, 'ORDER BY "timevalue"')
##            with arcpy.da.InsertCursor(in_track, f_utils.fieldLists.pathFields) as iCur:
##                with arcpy.da.SearchCursor(new_track, f_utils.fieldLists.pathFields,
##                                             "", sr, sqlClause) as sCur:
##                    for row in sCur:
##                        iCur.insertRow(row)
##
##            arcpy.Delete_management(new_track)
##        else:
##            arcpy.AddMessage('Temporary track empty...exiting')
##    else:
##        arcpy.AddMessage('Track not found...exiting')