# dev_ellipse_point.py
import arcpy
from arcpy import env
#from sys import exit

# local modules
#import dev_tables as tables
#import dev_db_utils as dbutil

inLayer = arcpy.GetParameterAsText(0)
sr = arcpy.SpatialReference(4326)

mxd = arcpy.mapping.MapDocument('CURRENT')
df = arcpy.mapping.ListDataFrames(mxd)[0]
mxd.activeView = df.name

env.workspace = 'in_memory\\'
env.addOutputsToMap = True
env.overwriteOutput = True

point_name = 'proxy_point'
point_file = arcpy.FeatureToPoint_management(inLayer, point_name)
# get new lat/lon for proxy row
arcpy.AddXY_management(point_file)

# load back to to GDB as proxy

"""
# Get data from new point
with arcpy.da.SearchCursor(point_name, "*", None, sr) as pCur:
    point = pCur.next()

fid, animal_id, tag_id, timeVal = point[2:6]
Lat, Lon = point[20:]
feature_type = 'proxy'

#arcpy.AddMessage(str(fid))

try:
    # Save to proxy table in GDB
    conn = dbutil.getDbConn('wtg_gdb')

    dev = (tag_id, animal_id, timeVal, feature_type)
    row = {'latitude': Lat,
           'longitude': Lon,
           'original_fid': fid,
           'source': 'On land ellipse proxy'}
    # instantiate object
    proxyObj = tables.Proxy(*dev, **row)
    feature_id = dbutil.dbTransact(conn,proxyObj.sql_insert(),proxyObj.param_dict())
    arcpy.AddMessage('FID = '+str(feature_id))

    if feature_id:
        conn.commit()
        arcpy.AddMessage('FID = '+str(feature_id))
    else:
        arcpy.AddMessage("didn't work")
except Exception as e:
    print 'error '+e.message
    conn.rollback()
"""
lyr = arcpy.MakeFeatureLayer_management(point_file, point_name)
arcpy.SetParameterAsText(1, lyr)



