""" Newer version
From input Dive Events (line) FeatureLayer, make a new Event Table with day/night
and moon phase values, with 1-hour interpolation, which can then be referenced
to that tag's Route to make a new Event Layer.

*** For single tag layer only!!

The moon phase method returns a number describing the phase,
where the value is between 0 and 27
0 = New Moon
7 = First Quarter
14 = Full Moon
21 = Last Quarter
"""

import arcpy
from arcpy import env
import datetime
from os import path
from math import modf
from astral import Astral, Location


# Timezone handler
#from pytz import timezone, utc
#from pytz.exceptions import UnknownTimeZoneError

#from timezonefinder import TimezoneFinder
#tf = TimezoneFinder()
#tf.timezone_at(lng=longitude, lat=latitude)
#else tf.closest_timezone_at(lng=longitude, lat=latitude)
# returns string IE: 'America/Los_Angeles'

import traceback
import dev_f_utils as f

# Set Geoprocessing environments
env.addOutputsToMap = False
env.overwriteOutput = True

sr = arcpy.SpatialReference(4326)

# utility increments
datDay = datetime.timedelta(days=1)
datHr = datetime.timedelta(hours=1)
datSec = datetime.timedelta(seconds=1)
diel_name = {1:'Night', 2:'Dawn', 3:'Day', 4:'Dusk'}
datTZ = datetime.timedelta(hours=10)


in_table = arcpy.GetParameterAsText(0)

homeDir = path.dirname(in_table) # GDB FC input
if not homeDir:
    homeDir = env.workspace     # Map Layer input

diveDir = 'C:\\CurrentProjects\\Hump19HI\\GIS\\2019HI-Dives-1.gdb'

in_name = path.basename(in_table)
## route_name = diveDir+'\\Routes\\rt_'+in_name[3:]
try:

##    # create route in gdb
##    arcpy.CreateRoutes_lr(in_table, "ptt", route_name,
##                            "TWO_FIELDS", "FromLoc", "ToLoc")
###                            "TWO_FIELDS", "FromLocation", "ToLocation")

# Gather data from track

# v1  fields = ("FromLocation", "ToLocation", "ptt", "SHAPE@XY", "OBJECTID")
#    sql_clause = (None, 'ORDER BY "FromLocation" ASC')
# v2  fields = ("FromLoc", "ToLoc", "ptt", "SHAPE@XY", "OBJECTID")
#    sql_clause = (None, 'ORDER BY "ptt", "FromLoc" ASC')
    fields = ("from_loc", "to_loc", "ptt", "SHAPE@XY", "OBJECTID")
    sql_clause = (None, 'ORDER BY "ptt", "from_loc" ASC')
#            BTW "None" gets filled by the Layer's definition query!! ----------

    with arcpy.da.SearchCursor(in_table, fields, None, sr, None, sql_clause) as sCur:
        # first row
        row = sCur.next()
        # get ptt, begin & end dates
        ptt = row[2]
        startLoc = row[0]
        # make list of locations
        locs = [[row[4]-1,row[3]]] # [OID-1,(Lon,Lat)]
        for row in sCur:
            if not row == None:
                locs.append([row[4]-1,row[3]])
        endLoc = row[1]

    # Date range as datetime, converted to local time
    #*****Convert back on write!!! ***************
    startDate = f.DateSer(startLoc)-datTZ
    stopDate = f.DateSer(endLoc)-datTZ


    # copy to new table, adding diel fields
    evTemplate = 'C:\\CurrentProjects\\Calif 2016\\GIS\\ST27 Dives.gdb\\tr_events'
    table_name = 'ev_'+in_name[3:]
    eventTable = arcpy.CreateTable_management(diveDir, table_name, evTemplate)

    # field list
    f_names = ['ptt', 'fromlocation', 'tolocation', 'diel', 'moon', 'startdate', 'enddate']
    with arcpy.da.InsertCursor(eventTable, f_names) as iCur:
        rows = []

        # define diel events for first day
        loc = Location(('loc', '', locs[0][1][1], locs[0][1][0] , 'US/Pacific', 0)) # pass in as a tuple
        loc.solar_depression = 'civil'
        loc_day = startDate # as datetime
        sun = loc.sun(loc_day)
        moon = loc.moon_phase(loc_day)
        events = {1:sun['dawn'].replace(tzinfo=None),
                2:sun['sunrise'].replace(tzinfo=None),
                3:sun['sunset'].replace(tzinfo=None),
                4:sun['dusk'].replace(tzinfo=None)}
        diel_name = {1:'Night', 2:'Dawn', 3:'Day', 4:'Dusk'}
        per = 3 # first timevalue (deploy) will always be sometime before sunset, RIGHT?
        seg = 0
        cur_hour = startDate.hour # integer
        endDate = datetime.datetime.combine(startDate.date(), datetime.time(cur_hour+1))

        while loc_day < stopDate:
            while True:
#                row = (ptt, startDate, endDate, diel_name[per], moon, startDate, endDate)
                row = (ptt, startDate+datTZ, endDate+datTZ, diel_name[per], moon, startDate+datTZ, endDate+datTZ)
                rows.append(row)
                iCur.insertRow(row)
                startDate = endDate+datSec
                if startDate.hour == 0:
                    break                                                           # if we cross midnight, skip to next days events
                else:
                    endDate += datHr
                cur_hour = endDate.hour
                # loop
                while cur_hour == events[per].hour:                                 # next event will occur during this hour
#                    row = (ptt, startDate, endDate, diel_name[per], moon, startDate, endDate)
                    row = (ptt, startDate+datTZ, endDate+datTZ, diel_name[per], moon, startDate+datTZ, endDate+datTZ)
                    rows.append(row)
                    iCur.insertRow(row)
                    startDate = endDate+datSec
##                    if startDate > datetime.datetime(2016, 8, 4, 18):
##                        pass
                    if endDate == events[per]:                                      # event row has already been written
                    # 3
                        endDate = datetime.datetime.combine(startDate.date(), datetime.time(cur_hour+1)) # next whole hour
                        per = per+1 if per<4 else 1 # advance periond
                        nextDate = events[per] if per>1 else loc.dawn(loc_day+datDay).replace(tzinfo=None)
                    else:
                    # 1-EndDate is still whole hour
                        endDate = events[per]                                       # coming up on next event
                        nextDate = endDate+datTZ # initialize (well past endDate)
                    if nextDate <= endDate:
                    # 4 use nextDate instead of endDate
#                        row = (ptt, startDate, nextDate, diel_name[per], moon, startDate, nextDate)
                        row = (ptt, startDate+datTZ, nextDate+datTZ, diel_name[per], moon, startDate+datTZ, nextDate+datTZ)
                        rows.append(row)
                        iCur.insertRow(row)
                        startDate = nextDate+datSec
                        # No need? endDate = datetime.datetime.combine(startDate.date(), datetime.time(cur_hour+1))
                        per = per+1 if per<4 else 1
                    else:
                    # 2 - nextDate is > endDate
                        cur_hour = endDate.hour

                    # loop

            # advance day
            loc_day += datDay
            seg+= 1
            loc = Location(('loc', '', locs[seg][1][1], locs[seg][1][0] , 'US/Pacific', 0)) # pass in as a tuple
            loc.solar_depression = 'civil'
            sun = loc.sun(loc_day)
            moon = loc.moon_phase(loc_day)
            events = {1:sun['dawn'].replace(tzinfo=None),
                    2:sun['sunrise'].replace(tzinfo=None),
                    3:sun['sunset'].replace(tzinfo=None),
                    4:sun['dusk'].replace(tzinfo=None)}
            endDate += datHr

    """ Now Add events to route
        *****  Do this for dives table too!
                don't need the interpolation, just match to dives?

    """

    #out_layer = arcpy.SetParameterAsText(eventTable)

### Code from residence=======================================
##    # Add events to route
##    eventProperties = 'ptt LINE FromLocation ToLocation'
##    eventLayer = in_name+'_Events'
##    arcpy.MakeRouteEventLayer_lr(route_name,  'ptt', eventTable,
##                                eventProperties, eventLayer)
##    # persist to GDB
##    eventName = 'pt_'+in_table[3:]+'_'+'_Events'
##    eventFC = arcpy.CopyFeatures_management(eventLayer, eventName)
##
##    # add layer to map
##    mxd = arcpy.mapping.MapDocument("CURRENT")
##    env.addOutputsToMap = True
##    lyr = arcpy.MakeFeatureLayer_management(eventFC, eventName)
##    arcpy.SetParameterAsText(1, lyr)
##
##    # select events inside AOI
##    arcpy.SelectLayerByLocation_management(eventName, "INTERSECT", sel_layer)
##
##    # count locs ****WRONG count, should be locations not tracks!!
##    result = arcpy.GetCount_management(in_table)
##    count = int(result.getOutput(0))
##    arcpy.AddMessage(in_table + ' Inside:')
##    locs = count
##
##    # count hours
##    result = arcpy.GetCount_management(eventName)
##    count = int(result.getOutput(0))
##    # ***** in 10-min. increments
##    hours = count/6.0
##    days = str(hours/24.0)
##    arcpy.AddMessage('Hrs: '+ str(hours))
##    # Send results to a CSV
##    with open('C:\\CurrentProjects\\Calif 2016\\GIS\\5790 Events.csv', 'ab') as outFile:
##        import csv
##        writer = csv.writer(outFile)
##        for loc in rows:
##            writer.writerow(loc)




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

