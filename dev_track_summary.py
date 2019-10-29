# track_summary.py
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
in_track  = arcpy.GetParameterAsText(0) # Use tracks
out_csv = arcpy.GetParameterAsText(1)

#in_track = 'C:\\CurrentProjects\\Hump18WA\\GIS\\2018WA_2.gdb\\tr_2018PNW'
#out_csv = 'C:\\CurrentProjects\\Hump18WA\\GIS\\TestSummary.csv'

# Workspace ************* MAKE ME A UTIL! **************
homeDir = path.dirname(in_track) # GDB FC input
if not homeDir:
    workspace = env.workspace      # Map Layer input
    # strip gdb from homeDir
    homeDir = path.dirname(workspace)
out_path = path.join(homeDir, out_csv)

# global
sr = arcpy.SpatialReference(4326)
conn = dbutil.getDbConn(db='wtg_gdb')
fmt = '%m/%d/%Y %H:%M:%S'

try:
    # prepare CSV
    with open(out_path, 'ab') as outFile:
        writer = csv.writer(outFile)
        writer.writerow(['Species', 'PTT', 'Sex', 'Tag Type', 'Deployed', 'Last Tx',
                        'Days Tx', 'Tx > Locs', 'Pass Count', 'Transmit Count',
                        'Raw Count', 'Filter Count', '% Retained', 'First Loc',
                        'Last Loc', 'Filter Days', 'Distance'])

# ********* Tool only!   Clear selections **********************************
        arcpy.SelectLayerByAttribute_management(in_track,'CLEAR_SELECTION')
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
                if ptt == 4177:
                    pass
#
                # startdate = min datetime for ptt
                deploy = min([t[1] for t in dateList if t[0]==ptt])
                # obtain tag_id's from pttList
                where = ''.join(["ptt = ", str(ptt), " AND start_date = '", deploy, "'"])
                params = {'filter': where}
                sql = 'SELECT tag_id FROM wtgdata.device \
                        WHERE {filter};'.format(**params)
                result = dbutil.dbSelect(conn, sql, params)
                if result:
                    device = result[0][0]
                    tagDict[ptt] = device
                else:
                    arcpy.AddMessage(str(ptt)+ ' was not found in device table')

            tagList = tuple(tagDict.values())
            # OrderedDict sorted by tagtype, ptt
            pttDict = dbutil.getTag_Summary(conn, tagList)
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

        # get info from database
        setDict = OrderedDict()
        for ptt, vals in pttDict.items():
            tag_id = vals[5]

            # passes
            where = ''.join(['tag_id = ', str(tag_id)])
            params = {'filter': where}
            # Count, Last, First Argos passes
            sql = 'SELECT COUNT(loc_class), MAX(timevalue) AS last, MIN(timevalue) AS first \
                    FROM geodata.argos \
                    WHERE {filter};'.format(**params)
            result = dbutil.dbSelect(conn, sql, params)
            setDict['count_pass'] = result[0][0]
            setDict['last_pass'] = str(result[0][1])
            setDict['first_pass'] = str(result[0][2])
            # transmits
            where = ''.join(['a.tag_id = ', str(tag_id)])
            params = {'filter': where}
            # Count messages
            sql = 'SELECT Count(t.timevalue) \
                    FROM geodata.argos a \
                    INNER JOIN wtgdata.transmit t ON (a.feature_id = t.feature_id) \
                    WHERE {filter};'.format(**params)
            result = dbutil.dbSelect(conn, sql, params)
            setDict['count_transmit'] = result[0][0]

            # raw locations
            where = ''.join(['tag_id = ', str(tag_id), ' AND latitude IS NOT NULL'])
            params = {'filter': where}
            sql = 'SELECT COUNT(loc_class), MAX(timevalue) AS last, MIN(timevalue) AS first \
                    FROM geodata.argos \
                    WHERE {filter};'.format(**params)
            result = dbutil.dbSelect(conn, sql, params)
            setDict['count_location'] = result[0][0]
            setDict['last_location'] = str(result[0][1])
            setDict['first_location'] = str(result[0][2])
            # Count days with >=1 locations
            params = {'filter':where, 'part':"'doy'"}
            sql = 'SELECT COUNT(PassDay) FROM \
                    (SELECT tag_id, date_part({part},timevalue) AS PassDay, \
                    COUNT(tag_id) AS CountDay \
                    FROM geodata.argos WHERE {filter} \
                    GROUP BY tag_id, date_part({part},timevalue) \
                    ) AS sub;'.format(**params)
            result = dbutil.dbSelect(conn, sql, params)
            setDict['count_days_w_loc'] = result[0][0]
#            arcpy.AddMessage(ptt)
#            arcpy.AddMessage(setDict.items())

            #pttDict   {ptt: [device_type, start_date, stop_date, species, geneticsex]}
            #setDict   {count_pass: int, count_transmit: int, last_transmit: datetime,
            #               count_raw: int, days_w_loc: int}
            # trackDict {ptt: (count_filt, first_filt, last_filt, dist_km)}

            # track duration
            deploy = pttDict[ptt][1]
            last_filt = trackDict[ptt][2]
            delta = last_filt-deploy
            dur_filt = delta.total_seconds()/86400.0 # float

            # transmit duration
            #last_tx = setDict['last_pass']
            last_tx = datetime.datetime.strptime(setDict['last_pass'],
                                                  '%Y-%m-%d %H:%M:%S')
            if last_tx:
                delta = last_tx-deploy
                days_tx = delta.total_seconds()/86400.0 # float
            else:
                days_tx = 0
            # difference
            diff_tx = days_tx-dur_filt # float
            # copy dates to strings
            start = deploy.strftime(fmt)
#            stop = pttDict[ptt][2].strftime(fmt)
            stop = last_tx.strftime(fmt)
            first = trackDict[ptt][1].strftime(fmt)
            last = last_filt.strftime(fmt)
            # percent retained
            count_filt = trackDict[ptt][0]
            percent = float(count_filt) / setDict['count_location']
            ptt_row = (pttDict[ptt][3],   # species
                        ptt,
                        pttDict[ptt][4],   # sex
                        pttDict[ptt][0],   # tag_type
                        start,
                        stop,
                        days_tx,
                        diff_tx,
                        setDict['count_pass'],
                        setDict['count_transmit'],
                        setDict['count_location'],
                        count_filt,
                        percent,
                        first,
                        last,
                        dur_filt,
                        trackDict[ptt][3]) # distance

            writer.writerow(ptt_row)

#    outFile.close()
    # Loop ptt continue -------------------------------------------




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