# residence-3.py

"""
***********************
 Multi tag / Multi Area  *
***********************
Interpolated locations were derived at <n-min> intervals between filtered
locations, assuming a linear track and a constant speed. These interpolated
locations provided evenly spaced time segments from which reasonable estimates
of residence times could be generated and were especially useful when tracklines
crossed <Area> boundaries. Residence time was calculated as the sum of all
<Time increment> segments from the interpolated tracks that were completely
within each area of interest. Percentage of time spent in these areas was
expressed as a proportion of the total track duration.
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
in_points = arcpy.GetParameterAsText(0)
track_name = arcpy.GetParameterAsText(1)
tag_field = arcpy.GetParameterAsText(2)
time_field = arcpy.GetParameterAsText(3)
#in_fields = arcpy.GetParameterAsText(3)
#field_list = in_fields.split(";")
sel_layer = arcpy.GetParameterAsText(4)
layer_list = sel_layer.split(";")
suffix = path.basename(sel_layer)
increment = arcpy.GetParameterAsText(5)
out_csv = arcpy.GetParameterAsText(6)

workspace = env.workspace     # Toolbox: get it from Map env
homeDir = path.dirname(workspace)
arcpy.AddMessage('Workspace = ' + workspace)
#out_path = out_csv  #path.join(homeDir, out_csv)

### port add'l fields to Columns tuple
##in_cols = []
##for field in arcpy.ListFields(in_points):
##    if field.name in field_list:
##        in_cols.append((field.name, field.type))

try:
    # clear selections!
    arcpy.SelectLayerByAttribute_management(in_points,'CLEAR_SELECTION')

    # get list of tags in input point layer
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
        # select current ptt
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

##        track_name = ''.join(['tr_', str(ptt).zfill(5)])
##        track_file = ''.join([workspace, '\\', track_name])
##        if not arcpy.Exists(track_name):
##            arcpy.AddMessage("Track not found, creating " + track_name)
##            # create track layer from selected ptt
##            import dev_make_path
##            track_file = dev_make_path.main(in_points)
##            track_name = path.basename(track_file)

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

            # re-select ptt
            sql = ''.join([tag_field, '=', str(ptt)])
            arcpy.SelectLayerByAttribute_management(track_name,'NEW_SELECTION', sql)
            # select segments that cross the area of interest
            arcpy.SelectLayerByLocation_management(track_name, "INTERSECT",
                                                    layer, None,'SUBSET_SELECTION')
            result = arcpy.GetCount_management(track_name)
            if int(result.getOutput(0)) == 0:
                arcpy.AddMessage("No selections in area for PTT: "+ str(ptt))
            else:
                # save selection to a temp polyline class
                _select = 'in_memory\\sel_segments'
                arcpy.Select_analysis(track_name, _select)
                # create route from selection
                route_name = 'in_memory\\rt_'+track_name[3:]
                arcpy.CreateRoutes_lr(track_name, "ptt", route_name,
#                                        "TWO_FIELDS", "FromLocation", "ToLocation")
                                        "TWO_FIELDS", "FromLoc", "ToLoc")
#                arcpy.AddMessage('Route created')

                # extract First & Last time reference from temp path
                sql_clause = (None, 'ORDER BY "Fromloc" ASC')
#                sql_clause = (None, 'ORDER BY "FromLocation" ASC')
                fields = ("FromLoc", "ToLoc", "ptt")
#                fields = ("FromLocation", "ToLocation", "ptt")
                with arcpy.da.SearchCursor(_select, fields, None, sr, None, sql_clause) as sCur:
                    row = sCur.next()
                    startPath = row[0]
                    for row in sCur:
                        if not row == None:
                            pass
                    endPath = row[1]

                #choose a starting time after the first location, rounded to the nearest increment
                inc = util.excelTime.xl_time[increment]
                startHour, startDay = modf(startPath) # excel datetime; fraction, integer
                xlHrs = sorted(util.excelTime.xl_Hr)
                i = 0
                for hr in xlHrs:
                    if hr < startHour:
                        i = xlHrs.index(hr)
                        continue
                if i < 22:
                    i += 1
                    start = startDay+xlHrs[i]
                else:
                    start = startDay+1

                # create a temporary event table
                table_name = ''.join(['ev_', str(ptt).zfill(5)])
                eventTable = arcpy.CreateTable_management('in_memory', table_name)
                evCols = [('ptt','TEXT'),('FromLoc','DOUBLE')]
                for f_name, f_type in evCols:
                    arcpy.AddField_management(eventTable, f_name, f_type)
                f_names = ['ptt', 'FromLoc']

                # populate event table
                fromLoc = start
                with arcpy.da.InsertCursor(eventTable, f_names) as iCur:
                    # First segment
                    iCur.insertRow([ptt, startPath])
                    while fromLoc < endPath:
                        iCur.insertRow([ptt, fromLoc])
                        fromLoc += inc
                    iCur.insertRow([ptt, endPath])
                arcpy.AddMessage('Event table created: ' + table_name)

                # Add events to route
                eventProperties = 'ptt POINT FromLoc'
                eventLayer = route_name+'_events'
                arcpy.MakeRouteEventLayer_lr(route_name, 'ptt', eventTable,
                                            eventProperties, eventLayer)
                # persist to GDB
                #area = path.basename(sel_layer)
                eventName = ''.join(['pt_', proj_id, '_', str(ptt).zfill(5), '_', layer])
                eventFC = arcpy.CopyFeatures_management(eventLayer, eventName)
                arcpy.AddMessage('Residence point layer saved to GDB: ' + eventName)

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
    outFile = open(out_csv, 'ab')
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