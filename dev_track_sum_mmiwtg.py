# track_summary.py FOR pre-2008 mmiwtg
# adapted FROM updateDeployment(conn, tag_id):

"""
NOTE: Tags with no locations won't show up in this table!
"""
import arcpy
from arcpy import env
from os import path
import sys
import csv
import datetime
import dev_db_utils as dbutil
import traceback
from collections import OrderedDict

# GetParameterAsText
#in_track  = arcpy.GetParameterAsText(0) # Use tracks
#out_csv = arcpy.GetParameterAsText(1)

in_track = 'C:\\CurrentProjects\\Hump18HI\\GIS\\Humps All 2018 Filter.gdb\\tr_1999HI_14'
out_csv = 'C:\\CurrentProjects\\Hump18HI\\GIS\\TestSummary.csv'

# Workspace ************* MAKE ME A UTIL! **************
homeDir = path.dirname(in_track) # GDB FC input
if not homeDir:
    workspace = env.workspace      # Map Layer input
    # strip gdb from homeDir
    homeDir = path.dirname(workspace)
out_path = path.join(homeDir, out_csv)

# global
sr = arcpy.SpatialReference(4326)
conn = dbutil.getDbConn(db='mmi_wtg')
con2 = dbutil.getDbConn(db='wtg_gdb')

fmt = '%m/%d/%Y %H:%M:%S'

try:
    # prepare CSV
    with open(out_path, 'ab') as outFile:
        writer = csv.writer(outFile)
        writer.writerow(['Species', 'PTT', 'Sex', 'Tag Type', 'Filter Days', 'Distance'])

# ********* Tool only!   Clear selections **********************************
  #      arcpy.SelectLayerByAttribute_management(in_track,'CLEAR_SELECTION')
# **************************************************************************

        # make dict of {ptt:tag_id, ...} from tracks
        tagDict = {}
        fields = ("ptt", "StartDate", "EndDate", "Distance_km")
        sql = (None, 'ORDER BY "ptt", "StartDate" ASC')
        with arcpy.da.SearchCursor(in_track, fields, None, sr, False, sql) as sCur:
            pttList = sorted(list(set([row[0] for row in sCur])))
            sCur.reset()
            dateList = [(row[0], row[1].strftime(fmt)) for row in sCur]
            # get start_dates for each ptt
            for ptt in pttList:
#
#                if ptt == 4177:
#                   pass
#
                # startdate = min datetime for ptt
                deploy = min([t[1] for t in dateList if t[0]==ptt])
                # obtain tag_id's from pttList
                where = ''.join(["ptt = ", str(ptt), " AND start_date = '", deploy, "'"])
                params = {'filter': where}
                sql = 'SELECT tag_id FROM wtgdata.device \
                        WHERE {filter};'.format(**params)
                result = dbutil.dbSelect(con2, sql, params)
                if result:
                    device = result[0][0]
                    tagDict[ptt] = device
                else:
                    arcpy.AddMessage(str(ptt)+ ' was not found in device table')

            tagList = tuple(tagDict.values())
            # OrderedDict sorted by tagtype, ptt
            pttDict = dbutil.getTag_Summary(con2, tagList)
            del dateList, pttList, tagList
            # create dict of track values
            trackDict = OrderedDict()
            for ptt in pttDict.keys():
                _cnt = 0
                _dist = 0.0
                _start = None
                sCur.reset()
                # subset track by ptt
                track = [row for row in sCur if row[0] == ptt]
                _start = track[0][2] # first enddate is first location After deploy
                for row in track:
                    _dist += row[3] # add up distances
                    _cnt += 1
                    # loop to end
                _stop = row[2]
                # create track dict
                trackDict[ptt] = (_cnt, _start, _stop, _dist)
                cnt_filt = _cnt
                ptt_row = (pttDict[ptt][3],   # species
                        ptt,
                        pttDict[ptt][4],   # sex
                        pttDict[ptt][0],   # tag_type
                        trackDict[ptt][0], # filt count
                        trackDict[ptt][3]) # distance

                writer.writerow(ptt_row)

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

"""
Other residence snippets:

        # get deployment values from db
        import dev_db_utils as dbutil
        conn = dbutil.getDbConn(db='wtg_gdb')
        # get tag_id
        where = ''.join(['ptt = ', str(ptt), ' AND start_date = TIMESTAMP ', deploy_str])
        params = {'filter': where}
        sql = 'SELECT tag_id FROM wtgdata.device \
                WHERE {filter};'.format(**params)
        result = dbutil.dbSelect(conn, sql, params)
#        arcpy.AddMessage('why query fail?')
#        arcpy.AddMessage(ptt)
        tag_id = result[0]

        # get CountOf & Last Argos passes
        where = ''.join(['tag_id = ', tag_id])
        params = {'filter': where}
        sql = 'SELECT count_pass, last_location \
                FROM wtgdata.deployment \
                WHERE {filter};'.format(**params)
        result = dbutil.dbSelect(conn, sql, params)
        count_pass = result[0][0]
        last_pass = result[0][1]

        # calc percentages
        lastp_obj = datetime.strptime(last_pass,fmt)

        delta = lastp_obj - deploy_obj
        all_days = delta.total_seconds() / 86400

"""