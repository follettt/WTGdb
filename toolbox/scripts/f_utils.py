# f_utils.py
# Filter utilities
import arcpy
from Vincenty import calcVincentyInverse
import collections

sr = arcpy.SpatialReference(4326)
# ---------------------------------------------------------------------------
def findJoins(in_fc):
    joined = False
    flds = arcpy.ListFields(in_fc)
    if len(flds) > 23:
        joined = True

    return joined
# ---------------------------------------------------------------------------
def uniqName(in_name):
    out_name = arcpy.CreateUniqueName(in_name)
    while arcpy.Exists(out_name):
        out_name = arcpy.CreateUniqueName(out_name)

    return out_name

# ---------------------------------------------------------------------------
def getPath(inRows):
    """From an input list of 2 or 3 rows return the Dict('Path','Dist','Time','Speed')"""
    line = arcpy.Polyline(arcpy.Array([arcpy.Point(*row[0]) for row in inRows]),sr)
    # measure the whole line
    dist = line.getLength("GREAT_ELLIPTIC")/1000.0  #"GEODESIC"
    times = [row[2] for row in inRows]
    delta = times[-1]-times[0]
    time =  (delta.days*24)+(delta.seconds/3600.0) # convert both to hours
    speed = dist/time if time > 0 else 0.0
    Segment = {'Path':line, 'Dist':dist ,'Time':time, 'Speed':speed}
    return Segment

# ---------------------------------------------------------------------------
def getVincentyPath(inRows):
    """From an input list of 2+ rows return the Dict('Path','Dist','Time','Speed')"""
    # extract lat/lon pairs from input rows; row[0]=(X, Y, Z)
    ptArray = [arcpy.Point(*row[0]) for row in inRows]
    line = arcpy.Polyline(arcpy.Array(ptArray),sr)
    dist = 0
    # first point
    lat1 = ptArray[0].Y
    lon1 = ptArray[0].X
    # other points
    for point in ptArray[1:]:
        lat2 = point.Y
        lon2 = point.X
        # Vincenty returns a list [distance, azimuth1, azimuth2]
        dist = dist + calcVincentyInverse(lat1,lon1,lat2,lon2)[0]/1000.0
        lat1 = lat2
        lon1 = lon2
    # list of all timevalues
    times = [row[2] for row in inRows]
    # timediff object  between last and first point
    delta = times[-1]-times[0]
    # convert object values into hours
    time = (delta.days*24)+(delta.seconds/3600.0)
    # trap for indentical timevalue
    if time > 0:
        speed = dist/time
    else:
        speed = dist/0.01666667 # one minute

    # send results to a dict
    Segment = {'Path':line, 'Dist':dist ,'Time':time, 'Speed':speed}
    return Segment
# ---------------------------------------------------------------------------
def parameters_from_args(defaults_tuple=None, sys_args=None):
    """Provided a set of tuples for default values, return a list of mapped
       variables."""
    defaults = collections.OrderedDict(defaults_tuple)
    if defaults_tuple is not None:
        args = len(sys_args) - 1
        for i, key in enumerate(defaults.keys()):
            idx = i + 1
            if idx <= args:
                defaults[key] = sys_args[idx]
    return defaults
# ---------------------------------------------------------------------------
def validate_name(in_name):

    # get rid of invalid characters
    out_name = arcpy.ValidateTableName(in_name)
    # check for WTG "p_" format

    return out_name
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
def getStartStop(devID):
    from db_utils import getDbConn, sqlToolbox, dbSelect

    conn = getDbConn()
    param = {'device': devID}
    getStartDate = 'SELECT startdate, stopdate \
                    FROM working.measuringdevice \
                    WHERE (deviceid = %(device)s)'
    result = dbSelect(conn, getStartDate, param)
    # returns a list of tuples
    if result:
      start = result[0][0].strftime('%m/%d/%Y %H:%M:%S')
      end =  result[0][1].strftime('%m/%d/%Y %H:%M:%S')
    else:
      device = 0
    return(start, end)

# ---------------------------------------------------------------------------
def addLogFields(in_file):

    try:
        # Add new filter fields
        arcpy.AddField_management(in_file, "filtername","Text","","",24,"Filter Tool")
        arcpy.AddField_management(in_file, "filterparam","Text","","",128,"Tool Parameters")

    except Exception as e:
        print e.message
        arcpy.AddMessage(e.message)

    return()
# ---------------------------------------------------------------------------
class excelTime(object):

    # 10 mimutes
    increment = 0.00694444444444446

#one hour increment = 0.041666667


    # 24 hours of the day
    xl_Hr = [0.041666667,
            0.083333333,
            0.125,
            0.166666667,
            0.208333333,
            0.25,
            0.291666667,
            0.333333333,
            0.375,
            0.416666667,
            0.458333333,
            0.5,
            0.541666667,
            0.583333333,
            0.625,
            0.666666667,
            0.708333333,
            0.75,
            0.791666667,
            0.833333333,
            0.875,
            0.916666667,
            0.958333333]


# ---------------------------------------------------------------------------
class filter_defaults(object):

    default_types = ['Tag Deployed', 'Biopsy Sample', 'Argos Pass']

    default_class = ['G', '3', '2', '1', '0', 'A', 'B2', 'B1']

# ---------------------------------------------------------------------------
class fieldLists(object):

    eventCols = [('Individual','LONG'),
                ('FromLocation','DOUBLE')]


    filterType = ["featureid",          # 0
                    "timevalue",        # 1
                    "lc",               # 2
                    "argospass" ,       # 3
                    "deploydevice",     # 4
                    "photoid",          # 5
                    "derived",          # 6
                    "gps",              # 7
                    "sample",           # 8
                    "take"]             # 9

    filterFields = ["SHAPE@XY",         # 0
                    "featureid",        # 1
                    "timevalue",        # 2
                    "lc"]               # 3

    pathSource = ["SHAPE@XY",
                "featureid",
                "timevalue",
                "fromlocation",
                "individual",
                "device",
                "ptt"]                  #Added 2/12/16

    pathCols = [('FromPoint','LONG'),
              ('ToPoint','LONG'),
              ('StartDate','DATE'),
              ('EndDate','DATE'),
              ('FromLocation','DOUBLE'),
              ('ToLocation','DOUBLE'),
              ('Individual','LONG'),
              ('Device','LONG'),
              ('ptt','INTEGER'),        #Added 2/12/16
              ('Distance_km','DOUBLE'),
              ('Elapsed_hrs','DOUBLE'),
              ('Speed_kmhr','DOUBLE')]



    pointFields = ["featureid",     # 0
                "ptt",              # 1     Added 2/12/16
                "featurecode",      # 2
                "timevalue",        # 3
                "fromlocation",     # 4
                "individual",       # 5
                "device",           # 6
                "latitude",         # 7
                "longitude",        # 8
                "lc",               # 9
                "argospass" ,       # 10
                "deploydevice",     # 11
                "photoid",          # 12
                "derived",          # 13
                "gps",              # 14
                "sample",           # 15
                "take",             # 16
                "cruise",           # 17
                "occurrence",       # 18
                "mm_filter",        # 19
                "SHAPE@"]           # 20

    pathFields = ["FromPoint",
                "ToPoint",
                "StartDate",
                "EndDate",
                "FromLocation",
                "ToLocation",
                "Individual",
                "Device",
                "Distance_km",
                "Elapsed_hrs",
                "Speed_kmhr",
                "SHAPE@"]

    logFields = ["featureid",
                "featurecode",
                "timevalue",
                "fromlocation",
                "individual",
                "device",
                "latitude",
                "longitude",
                "lc",
                "argospass" ,
                "deploydevice",
                "photoid",
                "derived",
                "gps",
                "sample",
                "take",
                "cruise",
                "occurrence",
                "mm_filter",
                "SHAPE@",
                "filtername",
                "filterparam"]

    addLogField = {"filtername": 24,
                "filterparam": 128}

# ---------------------------------------------------------------------------
class domDicts(object):

    lcBuffer = {0: 10,
                1: 3.5,
                2: 1.5,
                3: 1.0}

    lcDict = {  'D': -4,    # Derived
                'B1':-3,
                'B2':-2,
                'A': -1,
                '0':  0,
                '1':  1,
                '2':  2,
                '3':  3,
                'G':  8}

    typeDict = {'Argos Pass':    3,
                'Tag Deployed':  4,
                'Photo ID':      5,
                'Derived':       6,
                'FastLoc GPS':   7,
                'Biopsy Sample': 8,
                'Stranding':     9}

##    typeDict = {'Argos Pass':    9,
##                'Tag Deployed': 10,
##                'Photo ID':     11,
##                'Derived':      12,
##                'FastLoc GPS':  13,
##                'Biopsy Sample':14,
##                'Stranding':    15}


# --------------------------------------------------------------------------
##  arcpy.SplitLine_management(temp_layer, output_name)
##    arcpy.AddField_management(output_name, 'DistKM', 'FLOAT')
##    arcpy.CalculateField_management(output_name,'DistKM','!shape.geodesicLength@kilometers!','PYTHON_9.3')

##while result.status < 4:
##    time.sleep(0.2)


# **KEEP** translate input unicode object to list of integers
#    lc_temp = findall('\-\d', str(lc_List))
#    lc_vals = [lc for lc in lc_List]

# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
