import arcpy
from arcpy import env
from datetime import datetime
from datetime import timedelta

from dev_f_utils import fieldLists
import dev_db_utils as dbutil
import dev_tables as tables

#in_track = 'C:\\CurrentProjects\\Hump19HI\\GIS\\2019HI-Updater.gdb\\tr_00847'
in_track = arcpy.GetParameterAsText(0)
in_point = arcpy.GetParameter(1)
sr = arcpy.SpatialReference(4326)

#mxd = arcpy.mapping.MapDocument('CURRENT')
#df = arcpy.mapping.ListDataFrames(mxd)[0]
#mxd.activeView = df.name

#env.workspace = 'in_memory\\'
env.addOutputsToMap = True
env.overwriteOutput = True

temp_points = 'seg_vertex'
# Obtain values from line segment
fields = [f[0] for f in fieldLists.pathCols]
with arcpy.da.SearchCursor(in_track, fields) as sCur:
# if one segment, around land
# if two segments, excursion around land
    segment = sCur.next()
    fromPt = segment[0]
    start_time = segment[3]
    dist = segment[5]
    duration = segment[6]*3600.0

# create new point fc from vertices of segment
arcpy.FeatureVerticesToPoints_management(in_track, temp_points,"BOTH_ENDS") # "START"


# measure from new point to start vertex
arcpy.Near_analysis(temp_points,in_point, None, None, None, "GEODESIC")
with arcpy.da.SearchCursor(temp_points,"NEAR_DIST") as sCur:
    new_dist = sCur.next()[0]/1000.0
#    check speed(s)


# calculate new timevalue
factor = duration*(new_dist/dist)
timeval = start_time + timedelta(seconds=factor)

# get animal_id and tag_id from encounter
conn = dbutil.getDbConn('wtg_gdb')
sql = 'SELECT animal_id, tag_id from geodata.argos WHERE feature_id = %(fromPt)s'
params =  {'fromPt': fromPt}
feat_row = dbutil.dbSelect(conn, sql, params)
animID, tagID = feat_row[0][:]

# build point for new proxy row
with arcpy.da.SearchCursor(in_point,"shape_m") as sCur:
    row = sCur.next()#[0]
proxy1 = arcpy.Point(*row[0])
vals = (tagID, animID, timeval, '')
row = {"source":'rubber band',"latitude":proxy1.Y, "longitude":proxy1.X}
proxyObj = tables.Proxy(*vals, **row)
feature_id = dbutil.dbTransact(conn,proxyObj.sql_insert(),proxyObj.param_dict())
conn.commit()
arcpy.AddMessage(feature_id)




#a_point = arcpy.SetParameter(2)