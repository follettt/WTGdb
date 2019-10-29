# residence-2.py

"""
***********************
    Multi tag version *
***********************
Interpolated locations were derived at <nn-min> intervals between filtered
locations, assuming a linear track and a constant speed. These interpolated
locations provided evenly spaced time segments from which reasonable estimates
of residence times could be generated and were especially useful when tracklines
crossed <Area> boundaries. Residence time was calculated as the sum of all
<Time increment> segments from the interpolated tracks that were completely
within each area of interest. Percentage of time spent in these areas was
expressed as a proportion of the total track duration.



TODO:   project_id field1 of csv
        multiple AOIs
        csv format:
        proj, ptt, sumloc, sumday, AOI, pctloc, pctday, AOI, pctloc, pctday...


  """


import arcpy
from arcpy import env
from datetime import datetime
from os import path
from math import modf
import csv
import sys
import traceback

# Local Imports
import dev_f_utils as util

# Set Geoprocessing environments
#mxd = arcpy.mapping.MapDocument("CURRENT")
env.addOutputsToMap = True
env.overwriteOutput = True

# Global vars
sr = arcpy.SpatialReference(4326)
fmt = '%m/%d/%Y %H:%M:%S'
inc_dict = {'1 hour':1,'10 min':6.0,'20 min':3.0,'30 min':2.0}

# Parameters
in_points  = arcpy.GetParameterAsText(0) # Use points layer
tag_field = arcpy.GetParameterAsText(1)
time_field = arcpy.GetParameterAsText(2)
in_fields = arcpy.GetParameterAsText(3)
field_list = in_fields.split(";")
sel_layer = arcpy.GetParameterAsText(4)
layer_list = sel_layer.split(";")
suffix = path.basename(sel_layer)
increment = arcpy.GetParameterAsText(5)
out_csv = arcpy.GetParameterAsText(6)

# Workspace
homeDir = path.dirname(in_points) # GDB FC input
if not homeDir:
    workspace = env.workspace     # Map Layer input
    homeDir = path.dirname(workspace)
out_path = path.join(homeDir, out_csv)

# port add'l fields to Columns tuple
in_cols = []
for field in arcpy.ListFields(in_points):
    if field.name in field_list:
        in_cols.append((field.name, field.type))

try:
    # clear any selections!
    arcpy.SelectLayerByAttribute_management(in_points,'CLEAR_SELECTION')

    # get list of tags in input layer
    ptt_list = []
    fields = (tag_field, "project_id")
    order = ''.join(['ORDER BY ', tag_field])
    sql = ('DISTINCT', order)
    with arcpy.da.SearchCursor(in_points, fields, None, sr, False, sql) as sCur:
        proj_id = sCur.next()[1]
        sCur.reset()
        ptt_list = [row[0] for row in sCur]

    row_list = []
    for ptt in ptt_list:
        # select this tag
        sql = ''.join([tag_field, '=', str(ptt)])
        arcpy.SelectLayerByAttribute_management(in_points,'NEW_SELECTION', sql)
        arcpy.AddMessage('Processing ' + str(ptt))

        # count of ALL locations for ptt
        result = arcpy.GetCount_management(in_points)
        count_all = int(result.getOutput(0))
        if count_all < 2:
            arcpy.AddMessage(str(ptt) + ': No locations found in area')
            continue

        # save first/last dates from points
        fields = (time_field)
        where = ''.join([tag_field, '=', str(ptt)])
        order = ''.join(['ORDER BY ', time_field])
        sql = (None, order)
        with arcpy.da.SearchCursor(in_points, fields, where, sr, False, sql) as sCur:
            start_date = sCur.next()[0]
            for row in sCur:
                if not row == None:
                    pass
            stop_date = row[0]
        delta = stop_date - start_date
        all_days = delta.total_seconds() / 86400

##        # Look for existing track
##        track_name = ''.join(['tr', in_points[1:]]) # ******* find underscore in name
##  #      track_name = ''.join(['tr_', str(ptt).zfill(5)])
##        if not arcpy.Exists(track_name):
##            arcpy.AddMessage("Track not found, creating " + track_name)
##            # create in_memory track layer from selected ptt's points
##            import dev_make_path
##            track_file = dev_make_path.main(in_points)
##            #track_name = dev_make_path.main(in_points)

        for layer in layer_list:
            arcpy.AddMessage('AOI: ' +layer)
            # re-select ptt
            sql = ''.join([tag_field, '=', str(ptt)])
            arcpy.SelectLayerByAttribute_management(in_points,'NEW_SELECTION', sql)
            # subset select points for inLocs count
            arcpy.SelectLayerByLocation_management(in_points, "INTERSECT",
                                                    layer, None,'SUBSET_SELECTION')
            result = arcpy.GetCount_management(in_points)
            count_pts = int(result.getOutput(0))

            # Assumes events already in root TOC
            eventName = ''.join(['pt_', proj_id, '_', str(ptt).zfill(5), '_', layer])
            arcpy.AddMessage('Event layer = ' + eventName)
            if not arcpy.Exists(eventName):
                arcpy.AddMessage("No events in AOI")
                #row_list.append([proj_id, ptt, count_all, all_days, layer, str(0),  str(0), str(0), str(0)])
            else:
                # select events inside AOI
                arcpy.SelectLayerByLocation_management(eventName, "INTERSECT", layer)
                # count selected events & convert into days
                result = arcpy.GetCount_management(eventName)
                count_interp = int(result.getOutput(0))
                hours = count_interp / inc_dict[increment]
                days = hours/24.0
                arcpy.AddMessage('# days inside AOI: ' + str(days))
                # If tag was 100% inside, adding up event hours can slightly exceeed all_time
                if all_days < days:
                    days = all_days
                # calc percentages
                pct_locs = count_pts / float(count_all)
                pct_time = days / float(all_days)
                # add results to matrix
                row_list.append([proj_id, ptt, count_all, all_days, layer, pct_locs,  pct_time, count_pts, days])

    # prepare CSV
    outFile = open(out_path, 'ab')
    writer = csv.writer(outFile)
    csv_fields = ['Project', 'PTT','Sum Locs','Sum Days','Area',
                    'Pct Locs','Pct Days','In Locs','In Days']
    writer.writerow(csv_fields)
    for row in row_list:
        writer.writerow(row)

    outFile.close()

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

##        # get deployment values from db
##        import dev_db_utils as dbutil
##        conn = dbutil.getDbConn(db='wtg_gdb')
##        # get tag_id
##        where = ''.join(['ptt = ', str(ptt), ' AND start_date = TIMESTAMP ', deploy_str])
##        params = {'filter': where}
##        sql = 'SELECT tag_id FROM wtgdata.device \
##                WHERE {filter};'.format(**params)
##        result = dbutil.dbSelect(conn, sql, params)
###        arcpy.AddMessage('why query fail?')
###        arcpy.AddMessage(ptt)
##        tag_id = result[0]
##
##        # get CountOf & Last Argos passes
##        where = ''.join(['tag_id = ', tag_id])
##        params = {'filter': where}
##        sql = 'SELECT count_pass, last_location \
##                FROM wtgdata.deployment \
##                WHERE {filter};'.format(**params)
##        result = dbutil.dbSelect(conn, sql, params)
##        count_pass = result[0][0]
##        last_pass = result[0][1]
##
##        # calc percentages
##        lastp_obj = datetime.strptime(last_pass,fmt)
##
##        delta = lastp_obj - deploy_obj
##        all_days = delta.total_seconds() / 86400