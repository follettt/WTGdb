# f_utils.py
# Filter utilities
import arcpy
import datetime

sr = arcpy.SpatialReference(4326)

# **KEEP** translate input unicode object to list of integers
#    lc_temp = findall('\-\d', str(lc_List))
#    lc_vals = [lc for lc in lc_List]

# ---------------------------------------------------------------------------
def uniqName(in_name):
    out_name = arcpy.CreateUniqueName(in_name)
    while arcpy.Exists(out_name):
        out_name = arcpy.CreateUniqueName(out_name)
    return out_name

# ---------------------------------------------------------------------------
def getPath(inRows):
    """From an input list of 2 or 3 rows return the Dict('Path','Dist','Time','Speed')"""
    # construct polyline from input point **********(array?)


    line = arcpy.Polyline(arcpy.Array([arcpy.Point(*row[0]) for row in inRows]),sr)
    # measure the whole line
    dist = line.getLength("GREAT_ELLIPTIC")/1000.0  #kilometers
    times = [row[2] for row in inRows]
    delta = times[-1]-times[0]
    time =  (delta.days*24)+(delta.seconds/3600.0) # convert both to hours
    speed = dist/time if time > 0 else dist/0.01666667
    Segment = {'Path':line, 'Dist':dist ,'Time':time, 'Speed':speed}
    return Segment

# ---------------------------------------------------------------------------
def getVincentyPath(inRows):
    """From an input list of 2+ rows return the Dict('Path','Dist','Time','Speed')"""
    from Vincenty import calcVincentyInverse
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
    from collections import OrderedDict
    defaults = OrderedDict(defaults_tuple)
    if defaults_tuple is not None:
        args = len(sys_args) - 1
        # iterate index, value from input list
        for i, key in enumerate(defaults.keys()):
            idx = i + 1
            if idx <= args:
                defaults[key] = sys_args[idx]
    return defaults
# ---------------------------------------------------------------------------
def addLogFields(in_file):

    try:
        # detect if already there?

        # Add new filter fields
        arcpy.AddField_management(in_file, "filtername","Text","","",24,"Filter Tool")
        arcpy.AddField_management(in_file, "filterparam","Text","","",128,"Tool Parameters")

    except Exception as e:
        print e.message
        arcpy.AddMessage(e.message)

    return()
# ---------------------------------------------------------------------------
class excelTime(object):

    xl_time =  {'1 hour': 0.0416666666667,
               '10 min': 0.0069444444446,
               '20 min': 0.0138888888889,
               '30 min': 0.0208333333333}


    excel_sec = 0.0000115740740740741
    excel_min = 0.000694444444444444

    # 1 hour
    excel_hr = 0.0416666666666667

    # 30 seconds
    increment30s = 0.000347222222222222

    # 10 mimutes
    increment = 0.00694444444444446

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


#------------------------------------------------------------------------------
def SerDate(inDate):
  """Return a serial time from a datetime"""
  #Basetime is NORMALLY 1/1/1900 12:00 am
  basetime = datetime.datetime(1899,12,30,0,0,0)
  delta =  inDate - basetime
  julian = (delta.seconds / 86400.0) + delta.days
  return julian

def DateSer(inFloat):
  """Return a datetime from a serial time"""
  basetime = datetime.datetime(1899,12,30,0,0,0)
  inDays = int(inFloat) # extract the days portion
  inFract = inFloat - inDays
  inSecs = int(round(inFract * 86400.0))
  assert 0 <= inSecs <= 86400
  if inSecs == 86400:
      inSecs = 0
      inDays += 1
  outDate = basetime + datetime.timedelta(days=inDays) \
            + datetime.timedelta(seconds=inSecs)
  return outDate

def str2Date(inString,fmt):
    """ Return a datatime object from a string"""
    date_val = datetime.datetime.strptime(inString, fmt)
    return date_val

def date2Str(inDate,fmt):
    """ Return a datatime object from a string"""
    date_str = inString.strftime(fmt)
    return date_str


# ---------------------------------------------------------------------------
class symbolLayers(object):

    f_month_point =  'C:\\CurrentProjects\\Hump18HI\\GIS\\HI-Mig-EndPoint.lyr'
    tr_month_track = 'C:\\CurrentProjects\\Hump18HI\\GIS\\HI-Mig-Track.lyr'

# ---------------------------------------------------------------------------
class fieldLists(object):

    # point featureclass constructed in dev_query_tags, via v_select_points view
    pointFields = ["SHAPE@XY",
                "feature_id",
                "timevalue",
                "animal_name",
                "species_name",
                "ptt",
                "tag_name",
                "tag_class",
                "feature_type",
                "tag_id",
                "animal_id",
                "quality",
                "latitude",
                "longitude",
                "project_id"]

    pointFilter = ["SHAPE@XY",
                "feature_id",
                "timevalue",
                "animal_name",
                "species_name",
                "ptt",
                "tag_name",
                "tag_class",
                "feature_type",
                "tag_id",
                "animal_id",
                "quality",
                "latitude",
                "longitude",
                "project_id",
                "filtername",
                "filterparam"]

    # used in wtgfilter.main SearchCursor
    filterFields = ["SHAPE@XY",         # 0
                    "feature_id",       # 1
                    "timevalue",        # 2
                    "quality",          # 3
                    "ptt"]              # 4

#                    "filtername",       # 5
#                    "filterparam"]      # 6

    # used in make_path, fields from point in_file
    pathSource = ["SHAPE@XY",
                "feature_id",
                "timevalue",
                "ptt"]

    # used in make_path, fields to build track featureclass
    pathCols = [('FromPoint','LONG'),
              ('ToPoint','LONG'),
              ('StartDate','DATE'),
              ('EndDate','DATE'),
              ('ptt','INTEGER'),
              ('Distance_km','DOUBLE'),
              ('Elapsed_hrs','DOUBLE'),
              ('Speed_kmhr','DOUBLE')]

    # used in make_path, fields to build track featureclass
    routeCols = [('FromPoint','LONG'),
              ('ToPoint','LONG'),
              ('StartDate','DATE'),
              ('EndDate','DATE'),
              ('FromLoc', 'DOUBLE'),
              ('ToLoc', 'DOUBLE'),
              ('ptt','INTEGER'),
              ('Distance_km','DOUBLE'),
              ('Elapsed_hrs','DOUBLE'),
              ('Speed_kmhr','DOUBLE'),
              ('month', 'INTEGER')]




    pathFields = ["FromPoint",
                "ToPoint",
                "StartDate",
                "EndDate",
                "ptt",
                "Distance_km",
                "Elapsed_hrs",
                "Speed_kmhr",
                "Shape_Length",
                "SHAPE@"]

# was used in old filter
    logFields =     ["feature_id",
                    "ptt",
                    "timevalue",
                    "latitude",
                    "longitude",
                    "lc",
                    "Shape@XY",
                    "filtername",
                    "filterparam"]

    addLogField = {"filtername": 24,
                   "filterparam": 128}

# for updateDeployment?
    deployFields = ["animal_id",
                    "tag_id",
                    "deploy_date",
                    "first_pass",
                    "last_pass",
                    "sum_passes",
                    "sum_pass_days",
                    "sum_dep_pass",
                    "first_location",
                    "last_location",
                    "sum_locations",
                    "sum_location_days",
                    "sum_dep_loc",
                    "sum_msgs",
                    "project_id",
                    "adb_detach",
                    "adb_recover"]

    csv_header = ["Platform ID No.","Prg No.","Loc. quality","Loc. date",
              "Pass","Sat.","Frequency","Msg Date","Comp.","Msg","> - 120 DB",
              "Best level","Long. 1","Lat. sol. 1","Long. 2","Lat. sol. 2",
              "Loc. idx","Nopc","Error radius","Semi-major axis",
              "Semi-minor axis","Ellipse orientation","GDOP",
              "SENSOR #01","SENSOR #02","SENSOR #03","SENSOR #04",
              "SENSOR #05","SENSOR #06","SENSOR #07","SENSOR #08",
              "SENSOR #09","SENSOR #10","SENSOR #11","SENSOR #12",
              "SENSOR #13","SENSOR #14","SENSOR #15","SENSOR #16",
              "SENSOR #17","SENSOR #18","SENSOR #19","SENSOR #20",
              "SENSOR #21","SENSOR #22","SENSOR #23","SENSOR #24",
              "SENSOR #25","SENSOR #26","SENSOR #27","SENSOR #28",
              "SENSOR #29","SENSOR #30","SENSOR #31","SENSOR #32"]

    rawArgos_csv = ["SeasonID","CruiseID","Name","MM_TagID","DeviceID",
                    "IndividualID","ptt","sensors","lcount","satellite",
                    "loc_class","LC","hdatetime","freq_h","msgs","sub120",
                    "best_sig","freq_f","iq","lat1","lon1","lat2","lon2",
                    "ldatetime","duplicates","data","val1","val2"]

class CSV_schema(object):

  # files with dd/mm/yy date format
  bad_dates = [('090926.csv','091124.csv'),('110722.csv','120229.csv')]
  # Argos changed the field name  "&gt; - 120 DB" to "> - 120 DB"
  new_gt_date = '130409.csv'
  gt_names = ["&gt; - 120 DB","> - 120 DB"]

  # list of columns
  header = ["Platform ID No.","Prg No.","Loc. quality","Loc. date",
              "Pass","Sat.","Frequency","Msg Date","Comp.","Msg","&gt; - 120 DB",
              "Best level","Long. 1","Lat. sol. 1","Long. 2","Lat. sol. 2",
              "Loc. idx","Nopc","Error radius","Semi-major axis",
              "Semi-minor axis","Ellipse orientation","GDOP",
              "SENSOR #01","SENSOR #02","SENSOR #03","SENSOR #04",
              "SENSOR #05","SENSOR #06","SENSOR #07","SENSOR #08",
              "SENSOR #09","SENSOR #10","SENSOR #11","SENSOR #12",
              "SENSOR #13","SENSOR #14","SENSOR #15","SENSOR #16",
              "SENSOR #17","SENSOR #18","SENSOR #19","SENSOR #20",
              "SENSOR #21","SENSOR #22","SENSOR #23","SENSOR #24",
              "SENSOR #25","SENSOR #26","SENSOR #27","SENSOR #28",
              "SENSOR #29","SENSOR #30","SENSOR #31","SENSOR #32"]

  fix120_header = ["Platform ID No.","Prg No.","Loc. quality","Loc. date",
              "Pass","Sat.","Frequency","Msg Date","Comp.","Msg","> - 120 DB",
              "Best level","Long. 1","Lat. sol. 1","Long. 2","Lat. sol. 2",
              "Loc. idx","Nopc","Error radius","Semi-major axis",
              "Semi-minor axis","Ellipse orientation","GDOP",
              "SENSOR #01","SENSOR #02","SENSOR #03","SENSOR #04",
              "SENSOR #05","SENSOR #06","SENSOR #07","SENSOR #08",
              "SENSOR #09","SENSOR #10","SENSOR #11","SENSOR #12",
              "SENSOR #13","SENSOR #14","SENSOR #15","SENSOR #16",
              "SENSOR #17","SENSOR #18","SENSOR #19","SENSOR #20",
              "SENSOR #21","SENSOR #22","SENSOR #23","SENSOR #24",
              "SENSOR #25","SENSOR #26","SENSOR #27","SENSOR #28",
              "SENSOR #29","SENSOR #30","SENSOR #31","SENSOR #32"]

  # dict version
  rowField = {0:"Platform ID No.", 1:"Prg No.", 2:"Loc. quality",
            3:"Loc. date", 4:"Pass", 5:"Sat.", 6:"Frequency", 7:"Msg Date",
            8:"Comp.", 9:"Msg", 10:"&gt; - 120 DB", 11:"Best level",
            12:"Long. 1", 13:"Lat. sol. 1", 14:"Long. 2", 15:"Lat. sol. 2",
            16:"Loc. idx", 17:"Nopc", 18:"Error radius",
            19:"Semi-major axis", 20:"Semi-minor axis",
            21:"Ellipse orientation", 22:"GDOP",
            23:"SENSOR #01", 24:"SENSOR #02", 25:"SENSOR #03",
            26:"SENSOR #04", 27:"SENSOR #05", 28:"SENSOR #06",
            29:"SENSOR #07", 30:"SENSOR #08", 31:"SENSOR #09",
            32:"SENSOR #10", 33:"SENSOR #11", 34:"SENSOR #12",
            35:"SENSOR #13", 36:"SENSOR #14", 37:"SENSOR #15",
            38:"SENSOR #16", 39:"SENSOR #17", 40:"SENSOR #18",
            41:"SENSOR #19", 42:"SENSOR #20", 43:"SENSOR #21",
            44:"SENSOR #22", 45:"SENSOR #23", 46:"SENSOR #24",
            47:"SENSOR #25", 48:"SENSOR #26", 49:"SENSOR #27",
            50:"SENSOR #28", 51:"SENSOR #29", 52:"SENSOR #30",
            53:"SENSOR #31", 54:"SENSOR #32"}

#----------------------------------------------------------------------------

#  arcpy.SplitLine_management(temp_layer, output_name)
#    arcpy.AddField_management(output_name, 'DistKM', 'FLOAT')
#    arcpy.CalculateField_management(output_name,'DistKM','!shape.geodesicLength@kilometers!','PYTHON_9.3')
