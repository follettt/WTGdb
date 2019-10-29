#-------------------------------------------------------------------------------
# Name:        wtg_db_utils.py
# Purpose:
#
# Author:      tomas.follett
#
# Created:     03/21/2013
# Updated:     10/07/2013

#-------------------------------------------------------------------------------
import datetime
from sys import exit
import psycopg2
#import arcpy
#----------------------------------------------------------------------------
def getDbConn(db='mmi_wtg'):
  conn = ''
  server = 'MMIDATA'
  db = db
  if db == 'mmi_wtg':
    usr = 'tomasf'
    pwd = 'tf'
  elif db == 'mmi_sde':
    usr = 'sde'
    pwd = 'sde'
  elif db == 'wtg_gdb':
    usr = 'tomasf'
    pwd = 'tf'
  try:
    conn = psycopg2.connect(host=server, port="5432", database=db,
                           user=usr, password=pwd)
  except Exception as e:
    print "Can't connect to " + db + ': ' + e.message
  return conn
#----------------------------------------------------------------------------
def getSDEConn(db='mmi_wtg'):

  pathName = 'R:\\Data\\GIS_Data'
  if db == 'mmi_sde':
    fileName = "mmi_sde.sde"
  elif db == 'mmi_wtg':
    fileName = "mmi_wtg.sde"
  conFile = pathName+'\\'+fileName
  return conFile

#------------------------------------------------------------------------------
def getTag_Summary(conn, dev_list):
    """tagDict for summary table
       Returns {ptt:
                [tag_class,
                start_date,
                stop_date,
                species_name,
                gen_sex,
                tag_id]
                }
        ...for a given list of tag_id's

    NEEDS Haplotype and Locality"""

    from collections import OrderedDict

    devices = tuple(dev_list)
    curs = conn.cursor()
    tagDict = OrderedDict()

    terms = {'f_list'   :'d.ptt, d.tag_class, d.start_date, d.stop_date, \
                            a.species_name, a.gen_sex, d.tag_id',
             'sql_from' : 'wtgdata.device d \
                                INNER JOIN wtgdata.animal a \
                                ON d.animal_id = a.animal_id',
             'sql_where':'d.tag_id IN %(tags)s',
             'sql_order':'d.tag_class, d.ptt'
             }
    param = {'tags': devices}
    sql = 'SELECT {f_list} FROM {sql_from} WHERE {sql_where} ORDER BY {sql_order};'.format(**terms)
    try:
        curs.execute(sql, param)
        if curs:
            for row in curs:
                tagDict[row[0]] = row[1:]
        else:
            print 'execute failed?'

    except Exception as e:
        print 'db_util.getTag_Summary error: ' + e.message
    finally:
        print 'getTagSummary success'
        return tagDict

#----------------------------------------------------------------------------
def getTags(conn, ptt_list, proj_id):

    """Returns {ptt:
                tag_id,
                animal_id,
                start_date,
                stop_date
                data_dir}  ...for a given list of ptt's
    """
    # pass in project_id
    terms = {'f_list'   :'d.ptt, d.tag_id, d.animal_id, d.start_date, d.stop_date, p.data_dir',
             'sql_from' : 'wtgdata.project p INNER JOIN wtgdata.device d ON \
                            p.project_id = d.project_id',
             'sql_where':'p.project_id = %(proj)s AND \
                            d.ptt IN %(pttList)s',
             'sql_order':'d.ptt'
             }
    param = {'pttList':ptt_list,'proj': proj_id}
    sql = 'SELECT {f_list} FROM {sql_from} WHERE {sql_where} ORDER BY {sql_order};'.format(**terms)
    curs = conn.cursor()
    tagDict = {}
    try:
        curs.execute(sql, param)
        for row in curs:
            if row[1]==506: #2008MX-00837 problem 512
                continue
            tagDict[row[0]] = row[1:]
    except Exception as e:
            print 'db_util.getTags error: ' + e.message
    finally:
            return tagDict

#----------------------------------------------------------------------------
def getDeployTags(conn, proj_id):
    """Returns dict {ptt: 0  (tag_id,
                          1  animal_id,
                          2  start_date,
                          3  stop_date,
                          4  tagtype_id,
                          5  serial,
                          6  data_dir,
                          7  report_file,
                          8  species)}

                          9, 10, 11

    --IE:--  [ptt, (0:9)] from an input project_id"""

    # pass project_id into query
    terms = {'f_list'   :'d.ptt,d.tag_id,d.animal_id,d.start_date,d.stop_date,  \
                            d.tagtype_id,d.serial,p.data_dir,c.report_file, \
                            a.species_name, \
                            c.schedule1, c.sched2_start, c.schedule2' ,
             'sql_from' : 'wtgdata.project p \
                            LEFT JOIN wtgdata.device d ON \
                                    p.project_id = d.project_id \
                            LEFT JOIN wtgdata.tag_config c ON \
                                    d.tag_id = c.tag_id \
                            LEFT JOIN wtgdata.animal a ON \
                                    d.animal_id = a.animal_id',
             'sql_where':'p.project_id = %(proj)s',
             'sql_order':'d.ptt'
             }
    param = {'proj':proj_id}
    sql = 'SELECT {f_list} \
            FROM {sql_from} \
            WHERE {sql_where} \
            ORDER BY {sql_order};'.format(**terms)
    curs = conn.cursor()
    tagDict = {}
    try:
        curs.execute(sql, param)
        for row in curs:
            tagDict[row[0]] = row[1:]
    except Exception as e:
        print 'db_util.getDeployTags error: ' + e.message
    finally:
        return tagDict

#----------------------------------------------------------------------------
def getActiveTags(source):
    """ return a dict {tag_id:
                        ptt,            0
                        start_date      1
                        stop_date       2
                        status          3
                        animal_id       4
                        project_id      5
                        proj_year       6
                        data_dir        7
                        }
    """
    conn = getDbConn('wtg_gdb')
    if source == 'active':
        where = "status IN ('Active')"#, 'Dormant')"
    elif source == 'new_csv':
        where = "rebuildcsv = 1"
    elif source == 'new_db':
        where = "d.project_id = '2010GoM' "
        #where = "rebuilddb = 1"
    elif isinstance(source, tuple): # list of tag_id's
        where = ''.join(['tag_id IN ', str(source)])
    elif source[0:3].isdigit:   # project
#All Tags:#        where = ''.join(["d.project_id = '", source,"'"])
        where = ''.join(["d.project_id = '", source,"' AND d.status = '", "Active", "'"])
    f_list = ','.join(['d.tag_id','d.ptt', 'd.start_date', 'd.stop_date', 'd.status',
                'd.animal_id', 'd.project_id', 'p.project_year', 'p.data_dir'])

    params = {'fields':f_list, 'filter':where}
    sql = 'SELECT {fields} FROM wtgdata.device d \
            INNER JOIN wtgdata.project p \
                ON d.project_id = p.project_id \
            WHERE {filter};'.format(**params)

    curs = conn.cursor()
    tagDict = {}
    try:
        curs.execute(sql,)
        #******************* what if it's successful, but empty????
        for row in curs: #  fill tagDict from cursor
            tagDict[row[0]] = row[1:]
    except Exception as e:
        print 'db_util.getActiveTags error: ' + e.message
    except psycopg2.Error, err:
        print err.pgerror
        print err.diag

    finally:
        return tagDict
#----------------------------------------------------------------------------
def getOrphanTags(conn, ptt):
    """Returns dict {tag_id: (
                          0  project_id
                          1  start_date,
                          2  stop_date,
                          3  sched1,
                          4  sched2_start,
                          5  sched2)

    --IE:--  [ptt, (0:9)] from an input project_id"""

    # pass ptt into query
    terms = {'f_list'   :'d.tag_id,d.project_id,d.start_date,d.stop_date,  \
                          c.schedule1, c.sched2_start, c.schedule2' ,
             'sql_from' : 'wtgdata.device d \
                          LEFT JOIN wtgdata.tag_config c ON \
                                    d.tag_id = c.tag_id',
             'sql_where':'d.ptt = %(ptt)s AND d.start_date IS NOT NULL',
             'sql_order':'d.tag_id'
             }
    param = {'ptt':ptt}
    sql = 'SELECT {f_list} \
            FROM {sql_from} \
            WHERE {sql_where} \
            ORDER BY {sql_order} DESC;'.format(**terms)
    curs = conn.cursor()
    tagDict = {}
    try:
        curs.execute(sql, param)
        for row in curs:
            tagDict[row[0]] = row[1:]
    except Exception as e:
        print 'db_util.getDeployTags error: ' + e.message
    finally:
        return tagDict

#----------------------------------------------------------------------------
def dbSelect(conn, sql, params):
  cur = conn.cursor()
  resultTuple = ()
#  text = cur.mogrify(sql, params)
#  print text
  try:
    cur.execute(sql, params)
  except psycopg2.Error, e:
    print 'db_util.dbSelect error: ' + e.pgerror
    conn.rollback()
  if cur.rowcount > 0:
    resultTuple = cur.fetchall() # a list of tuples
  else:
    print "No records returned"
  return resultTuple

#----------------------------------------------------------------------------
def dbUpdate(conn, sql, params):
  cur = conn.cursor()
  try:
    cur.execute(sql, params)
  except psycopg2.Error, e:
    print 'db_util.dbUpdate error: ' + e.pgerror
    conn.rollback()
  return

#----------------------------------------------------------------------------
def dbTransact(conn, sql, params):
  """Manage database transactions. """
  # ===!!! This is specific to Single Row INSERTS only !!!!===
  cur = conn.cursor()
  try:
    cur.execute(sql, params)
  except psycopg2.Error as e:
    print 'db_util.dbTransact error: ' + e.pgerror
    print 'suspending execution'
    # rollback makes subsequent inserts fail when referring to PK of failed row
    conn.rollback()
    exit()
  if cur.rowcount == 1:
    keyList = cur.fetchone()[0] # take 1st value from tuple returned
  #===== Hopefully, this doesn't screw up the single pass mode??? ==============
  elif cur.rowcount > 1:
    result = cur.fetchall()
    keyList = [f[0] for f in result]
  else:# duplicate Pass was Not inserted
    keyList = 0
  return keyList

#----------------------------------------------------------------------------
def dbDelete(conn, sql):

# =========TODO: convert to proper parameter passing!!!================
  cur = conn.cursor()
  result = 'Failed'
  try:
    cur.execute(sql, )
    result = cur.statusmessage
  except psycopg2.Error as e:
    print 'db_util.dbDelete error: ' + e.pgerror
  finally:
    cur.close()
  return result
#----------------------------------------------------------------------------
def par(x): # wrap input with old-style fornatting
    y = '%({})s'.format(x)
    return y
def joyn(x): # shorter join ', '.join()
    y = ', '.join(x)
    return y
#----------------------------------------------------------------------------
def getRawData(conn, tag_id):

    where = ''.join(['d.tag_id = ', str(tag_id)])
    #order = d.tag_name, a.TimeValue, a.satellite, t.TimeValue
    params = {'filter': where, }

    sql = 'SELECT a.feature_id, a.timevalue AS passTime, \
            t.transmit_id, t.timevalue AS txTime, t.raw_data \
            FROM wtgdata.device d \
            JOIN (wtgdata.transmit t JOIN geodata.argos a ON t.feature_id = a.feature_id) \
                ON d.tag_id = a.tag_id \
            WHERE {filter} '.format(**params) + \
            'ORDER BY d.tag_name, a.TimeValue, a.satellite, t.TimeValue;'

    cur = conn.cursor()
    resultTuple = ()
    try:
        cur.execute(sql)
    except psycopg2.Error, e:
        print 'db_util.dbSelect error: ' + e.pgerror
        conn.rollback()
    if cur.rowcount > 0:
        resultTuple = cur.fetchall() # a list of tuples
    else:
        print "No records returned"

    return resultTuple

#----------------------------------------------------------------------------
def getTelParam(conn, tag_id):

    where = ''.join(['d.tag_id = ', str(tag_id)])
    #order = d.tag_name, a.TimeValue, a.satellite, t.TimeValue
    params = {'filter': where, }

    sql = 'SELECT t.measure, t.processing \
            FROM wtgdata.device d \
            JOIN wtgdata.tagtype t \
                ON d.tagtype_id = t.tagtype_id \
            WHERE {filter} '.format(**params)

    cur = conn.cursor()
    resultTuple = ()
    try:
        cur.execute(sql)
    except psycopg2.Error, e:
        print 'db_util.dbSelect error: ' + e.pgerror
        conn.rollback()
    if cur.rowcount > 0:
        resultTuple = cur.fetchall() # a list of tuples
    else:
        print "No records returned"

    return resultTuple[0]

#----------------------------------------------------------------------------
def updateDeployment(conn, tag_id):
    """

    """
    #where = ''.join(['tag_id = ', str(tag_id)])
    #params = {'filter':where}
    set_dict = {}
    try:
        conn = getDbConn(db='wtg_gdb')
        where = ''.join(['tag_id = ', str(tag_id)])
        params = {'filter': where}
        # Count, Last, First Argos passes
        sql = 'SELECT COUNT(loc_class), MAX(timevalue) AS last, MIN(timevalue) AS first \
                FROM geodata.argos \
                WHERE {filter};'.format(**params)
        result = dbSelect(conn, sql, params)
        set_dict['count_pass'] = result[0][0]
        set_dict['last_pass'] = str(result[0][1])
        set_dict['first_pass'] = str(result[0][2])
        # messages
        where = ''.join(['a.tag_id = ', str(tag_id)])
        params = {'filter': where}
        # Count messages
        sql = 'SELECT Count(t.timevalue) \
                FROM geodata.argos a \
                INNER JOIN wtgdata.transmit t ON (a.feature_id = t.feature_id) \
                WHERE {filter};'.format(**params)
        result = dbSelect(conn, sql, params)
        set_dict['count_transmit'] = result[0][0]
        # Count, First, Last raw locations
        where = ''.join(['tag_id = ', str(tag_id), ' AND latitude IS NOT NULL'])
        params = {'filter': where}
        sql = 'SELECT COUNT(loc_class), MAX(timevalue) AS last, MIN(timevalue) AS first \
                FROM geodata.argos \
                WHERE {filter};'.format(**params)
        result = dbSelect(conn, sql, params)
        set_dict['count_location'] = result[0][0]
        set_dict['last_location'] = str(result[0][1])
        set_dict['first_location'] = str(result[0][2])
        # Count days with >= 1 location
        params = {'filter':where, 'part':"'doy'"}
        sql = 'SELECT COUNT(PassDay) FROM \
                (SELECT tag_id, date_part({part},timevalue) AS PassDay, \
                COUNT(tag_id) AS CountDay \
                FROM geodata.argos WHERE {filter} \
                GROUP BY tag_id, date_part({part},timevalue) \
                ) AS sub;'.format(**params)
        result = dbSelect(conn, sql, params)
        set_dict['count_days_w_loc'] = result[0][0]
        # make parameters
# ***********************Use ZIP? **********************************************

        num_list = ["{} = {}".format(k,v) for k,v in set_dict.iteritems() if type(v) is long]
        dat_list = ["{} = '{}'".format(k,v) for k,v in set_dict.iteritems() if type(v) is str]
        s_list = num_list + dat_list
        s_str = ', '.join(s for s in s_list)
        # update query
        where = ''.join(['tag_id = ', str(tag_id)])
        params = {'sets': s_str, 'filter': where}
        sql = 'UPDATE wtgdata.deployment SET {sets} WHERE {filter} RETURNING deploy_id;'.format(**params)
        result = dbUpdate(conn, sql, params)
# ALSO: update device::Status = Dormant, Extinct based on time elapsed
# Dormant after 1 week, Extinct after 3 weeks



    except Exception as e:
        print 'updateDeployment error '+e.message
        conn.rollback()
    finally:
       conn.commit()

#----------------------------------------------------------------------------
def updateFilter():

    """ Write filter results back to geodata.argos::wtg_filter
    """




#----------------------------------------------------------------------------
class sqlArgosImport(object):

# =========TODO: convert to proper parameter passing!!!================

  # Does this one get used somewhere?????
  #getNewEncounters = 'SELECT * FROM working.encounter \
  #                    WHERE (featureid IN ' #%(feats)s)

  updateLastTx = '' #UPDATE query

  getAllEncounters = 'SELECT featureid FROM working.encounter \
                      WHERE featureid > 0 \
                      ORDER BY featureid;'

  getTransmits = 'SELECT measurementid, deviceid FROM get_transmits \
                  WHERE (ptt = %(ptt)s) AND (timevalue = %(timeVal)s)\
                  ORDER BY measurementid;'

  truncateWtgStaging = 'TRUNCATE TABLE working.encounter_stage;'
    # Added ptt 2/12/16
  appendStaging = 'INSERT INTO working.encounter_stage(featureid, featurecode, \
                    timevalue, fromlocation, individual, device, \
                    latitude, longitude, lc, argospass, deploydevice, photoid, \
                    derived, gps, sample, take, cruise, occurrence, mm_filter, ptt) \
                    (SELECT featureid, featurecode, timevalue, \
                      fromlocation, individual, device, latitude, longitude, \
                      lc, argospass, deploydevice, photoid, derived, gps, sample, \
                      take, cruise, occurrence, mm_filter, ptt \
                     FROM working.encounter \
                     WHERE (latitude <> 0) AND (featureid IN %(feats)s) \
                     ORDER BY featureid) \
                   RETURNING featureid;'
    # Added ptt 2/12/16
  f_names = ["featureid", "ptt", "featurecode", "timevalue", "fromlocation",
              "individual", "device", "latitude", "longitude", "lc", "argospass" ,
              "deploydevice", "photoid", "derived", "gps", "sample", "take",
              "cruise", "occurrence", "mm_filter", "shape"]
    # Added ptt 2/12/16
  dbf_names = ["featureid", "ptt", "featurecode", "timevalue", "fromlocation",
                "individual", "device", "latitude", "longitude", "lc", "argospass",
                "deploydevice", "photoid", "derived", "gps", "sample", "take",
                "cruise", "occurrence", "mm_filter"]
#----------------------------------------------------------------------------
class sqlToolbox(object):
# not wtg-gdb!
  getSpecies = 'SELECT speciescode FROM working.species ORDER BY speciescode;'
# not wtg-gdb!
  getCruises = 'SELECT DISTINCT cruise.code \
                FROM working.individual INNER JOIN working.cruise \
                    ON individual.initialcruise = cruise.cruiseid \
                WHERE (individual.species = %(code)s) \
                ORDER by cruise.code DESC;'
# not wtg-gdb!
  getTags = 'SELECT measuringdevice.ptt \
             FROM working.measuringdevice INNER JOIN working.cruise \
                ON measuringdevice.cruise = cruise.cruiseid \
             WHERE (cruise.code = %(code)s) \
             ORDER BY measuringdevice.ptt;'
# not wtg-gdb!
  getDevice = 'SELECT deviceid \
               FROM working.measuringdevice INNER JOIN working.cruise \
               ON measuringdevice.cruise = cruise.cruiseid \
               WHERE (cruise.code = %(cruise)s) AND (measuringdevice.ptt = %(ptt)s);'
# not wtg-gdb!
  getFeatures = 'SELECT featureid, featurecode, timevalue, fromlocation, \
                individual, device, latitude, longitude, lc, argospass, deploydevice, \
                photoid, derived, gps, sample, take, cruise, occurrence, mm_filter \
                FROM working.encounter \
                WHERE (device = %(device)s) \
                ORDER BY timevalue;'

#----------------------------------------------------------------------------
class sqlDeployments(object):
# not wtg-gdb!
  insertDeploys = 'INSERT INTO working.encounter(featureid, featurecode, \
                      pointtype, timevalue, fromlocation, individual, device, \
                      latitude, longitude, lc, deploydevice, photoid, sample, \
                      cruise, occurrence) \
                    (SELECT featureid, featurecode, \
                      pointtype, timevalue, fromlocation, individual, device, \
                      latitude, longitude, lc, deploydevice, photoid, sample, \
                      cruise, occurrence \
                      FROM working.encounter_deploys) \
                    RETURNING featureid;'

#----------------------------------------------------------------------------
class sqlDuplicates(object):
# could incorporate passdur as well
  getPasses = 'SELECT feature_id, timevalue, satellite, nb_mes, passdur \
               FROM geodata.argos \
               WHERE (tag_id = %(devID)s) \
               ORDER BY feature_id;'


#----------------------------------------------------------------------------
class sqlMeasData(object):
# not wtg-gdb!
  getTransmits = 'SELECT measurement.measurementid, devicetransmit.transmitid \
                  FROM working.devicetransmit \
                  INNER JOIN (working.encounter \
                    INNER JOIN working.measurement \
                      ON encounter.featureid = measurement.featureid) \
                    ON devicetransmit.measurement = measurement.measurementid \
                  WHERE (encounter.device = %(device)s) \
                  AND (devicetransmit.timevalue = %(timeVal)s);'
# not wtg-gdb!
              # key:[CSVfield, paramID, domain, domID]
  statusDict = {"Transmits":[9,'counter',None],
                "BattVoltage":[10,"measunit","V"],
                "TransmitVoltage":[11,"measunit","V"],
                "TransmitCurrent":[12,"measunit","A"],
                "Temperature":[13,"measunit","dF"],
                "MaxDepth":[15,"measunit","m"],
                "ZeroDepthOffset":[16,'counter',None]
                }
# not wtg-gdb!
  behavDict = {"Start":[28,'timestamp',None],
                "End":[29,'timestamp',None],
                "Shape":[32,'diveshape',None], #tba?
                "DepthMin":[33,"measunit","m"],
                "DepthMax":[34,"measunit","m"],
                "DurationMin":[35,"measunit","sec"],
                "DurationMax":[36,"measunit","sec"]
                }