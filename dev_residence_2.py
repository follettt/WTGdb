# residence.py

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
  """


import arcpy
from arcpy import env
from datetime import datetime
from os import path
from math import modf
import csv
import traceback

# Local Imports
import dev_f_utils as util
#import dev_trajectory as traj

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
    # prepare CSV
    outFile = open(out_path, 'ab')
    writer = csv.writer(outFile)
    writer.writerow(['Area','PTT','Sum Locs','Sum Days','In Locs','In Days','Pct Locs','Pct Days'])

    # clear any selections!
    arcpy.SelectLayerByAttribute_management(in_points,'CLEAR_SELECTION')

    # CLEAR THE CACHE!????******************************************************
    # list tags
    ptt_list = []
    fields = (tag_field)
    order = ''.join(['ORDER BY ', tag_field])
    sql = ('DISTINCT', order)
    with arcpy.da.SearchCursor(in_points, fields, None, sr, False, sql) as sCur:
        ptt_list = [row[0] for row in sCur]

    for ptt in ptt_list:
        # select tag
        sql = ''.join([tag_field, '=', str(ptt)])
        arcpy.SelectLayerByAttribute_management(in_points,'NEW_SELECTION', sql)
        arcpy.AddMessage('Processing ' + str(ptt))

        # count of all ptt locations
        result = arcpy.GetCount_management(in_points)
        count_all = int(result.getOutput(0))
        if count_all < 2:
            arcpy.AddMessage(str(ptt) + 'no locations found in area')
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

        # Look for existing track
#        track_name = ''.join(['tr_', in_points[1:]])
        track_name = ''.join(['tr_', str(ptt).zfill(5)])
        if not arcpy.Exists(track_name):
            arcpy.AddMessage("Track not found, creating " + track_name)
            # create in_memory track layer from selected ptt's points
#            tr_name = ''.join(['t_', str(ptt).zfill(5)])
#            track_name = traj.makeTrack(in_points, tag_field, time_field, in_cols, tr_name)
            import dev_make_path
            track_file = dev_make_path.main(in_points)
            #track_name = dev_make_path.main(in_points)

        # select points for count
        arcpy.SelectLayerByLocation_management(in_points, "INTERSECT", sel_layer, None,'SUBSET_SELECTION')
        result = arcpy.GetCount_management(in_points)
        count_pts = int(result.getOutput(0))
#        arcpy.AddMessage(count_pts)

        # select segments that cross the area of interest
        arcpy.SelectLayerByLocation_management(track_name, "INTERSECT", sel_layer)
        result = arcpy.GetCount_management(track_name)
        count_path = int(result.getOutput(0))

        if count_path > 0:
            # save selection to a temp polyline class
            _select = 'in_memory\\sel_segments'
            arcpy.Select_analysis(track_name, _select)
            # create route from selection
            route_name = 'in_memory\\rt_'+track_name[3:]
            # ASSUMES track created by trajectory.py !!
            arcpy.CreateRoutes_lr(track_name, "ptt", route_name,
                                    "TWO_FIELDS", "FromLoc", "ToLoc")
#            arcpy.CreateRoutes_lr(track_name, "name", route_name,
#                                    "TWO_FIELDS", "from_loc", "to_loc")
            arcpy.AddMessage('Route created')

            # extract First & Last time reference from temp points
            sql_clause = (None, 'ORDER BY "from_loc" ASC')
#            fields = ("from_loc", "to_loc", "name")
            fields = ("FromLoc", "ToLoc", "ptt")
            with arcpy.da.SearchCursor(_select, fields, None, sr, None, sql_clause) as sCur:
                row = sCur.next()
                startPath, endPath, ptt = row[0:4]
                for row in sCur:
                    if not row == None:
                        pass
                endPath = row[1]
 #           arcpy.AddMessage('FromLoc, ToLoc found')

            #choose time before the first location, rounded to the nearest hour
            startHour, startDay = modf(startPath)
            xlHrs = sorted(util.excelTime.xl_Hr)
            i = 0
            for hr in xlHrs:
                if hr < startHour:
                    i = xlHrs.index(hr)
                    continue
            start = startDay+xlHrs[i]

            # create a temporary event table
            table_name = ''.join(['ev_', str(ptt).zfill(5)])
            eventTable = arcpy.CreateTable_management('in_memory', table_name)
            evCols = [('ptt','TEXT'),('FromLoc','DOUBLE')]#            evCols = [('name','TEXT'),('from_loc','DOUBLE')]
            for f_name, f_type in evCols:
                arcpy.AddField_management(eventTable, f_name, f_type)
            f_names = ['ptt', 'FromLoc']#            f_names = ['name', 'from_loc']
            # populate event table
            fromLoc = start
            inc = util.excelTime.xl_time[increment]
            with arcpy.da.InsertCursor(eventTable, f_names) as iCur:
                while fromLoc < endPath:
                    iCur.insertRow([ptt, fromLoc])
                    fromLoc += inc
                iCur.insertRow([ptt, endPath])
#            arcpy.AddMessage('Event table created')

            # Add events to route
            eventProperties = 'ptt POINT FromLoc'#            eventProperties = 'name POINT from_loc'
            eventLayer = route_name+'_events'

#            arcpy.MakeRouteEventLayer_lr(route_name, 'name', eventTable,
            arcpy.MakeRouteEventLayer_lr(route_name, 'ptt', eventTable,
                                        eventProperties, eventLayer)
            # persist to GDB
            area = path.basename(sel_layer)
            eventName = ''.join(['pt_', str(ptt).zfill(5), '_', area])
            eventFC = arcpy.CopyFeatures_management(eventLayer, eventName)
#            arcpy.AddMessage('Residence point layer into GDB')

            # select events inside AOI
            arcpy.SelectLayerByLocation_management(eventName, "INTERSECT", sel_layer)
            # count selected events & convert into days
            result = arcpy.GetCount_management(eventName)
            count_interp = int(result.getOutput(0))
            hours = count_interp / inc_dict[increment]
            days = hours/24.0
            # If tag was 100% inside, adding up event hours can slightly exceeed all_time
            if all_days < days:
                days = all_days
            # calc percentages
            pct_locs = count_pts / float(count_all)
            pct_time = days / float(all_days)

            # write results to the CSV
            row = (area, ptt, count_all, all_days, count_pts, days, pct_locs, pct_time)
            writer.writerow(row)

        else:
            arcpy.AddMessage("No selections in area for PTT: "+ str(ptt))

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