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
import sys
import psycopg2
import arcpy
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

#----------------------------------------------------------------------------
def getDeployTags():
  """tagDict for deployments"""
  tagDict = {}
  sql = 'SELECT measuringdevice.deviceid, measuringdevice.ptt, \
              measuringdevice.name, measuringdevice.startdate, \
              measuringdevice.stopdate, measuringdevice.status, \
              measuringdevice.individual, \
              cruise.cruiseid, cruise.cruiseyear, cruise.description \
              FROM working.measuringdevice INNER JOIN \
                working.cruise ON measuringdevice.cruise = cruise.cruiseid \
              WHERE measuringdevice.rebuildcsv = 1;'

#----------------------------------------------------------------------------
def getActiveTags(source):
  """ return a dict {DeviceID:
                      0 ptt
                      1 Name
                      2 StartDate
                      3 StopDate
                      4 Status
                      5 IndividualID
                      6 CruiseID
                      7 CruiseYear
                      8 (cruise)Description
                      9 TagType
                     }"""
  conn = getDbConn('mmi_wtg')
  #-----------------------------------------------
  if source == 'active':
    filter = "measuringdevice.status = 'active'"#IN ('active', 'dormant')"
  elif source == 'new_csv':
    filter = "measuringdevice.rebuildcsv = 1"
  elif source == 'new_db':
    filter = "measuringdevice.rebuilddb = 1"
  elif isinstance(source, tuple):
    filter = "measuringdevice.deviceid IN " + str(source)

  sql = 'SELECT measuringdevice.deviceid, measuringdevice.ptt, \
                measuringdevice.device_name, measuringdevice.startdate, \
                measuringdevice.stopdate, measuringdevice.status, \
                measuringdevice.individual, cruise.cruiseid, cruise.cruiseyear, \
                cruise.description, measuringdevice.tagtype \
                FROM working.measuringdevice INNER JOIN \
                  working.cruise ON measuringdevice.cruise = cruise.cruiseid \
                WHERE '
  sql = sql + filter + ';'
  curs = conn.cursor()
  tagDict = {}  # empty dict
  try:
    curs.execute(sql,)
    for row in curs: #  fill tagDict from cursor
      tagDict[row[0]] = row[1:]
  except Exception as e:
    print 'db_util.getActiveTags error: ' + e.message
  finally:
    return tagDict
#  elif source == 'testing':
#    filter = "measuringdevice.status IN ('test', 'stored')"
#----------------------------------------------------------------------------
def dbSelect(conn, sql, params):
  cur = conn.cursor()
  resultTuple = ()
##  text = cur.mogrify(sql, params)
##  print text
  try:
    cur.execute(sql, params)
  except psycopg2.Error, e:
    print 'db_util.dbSelect error: '+ e.pgerror
    conn.rollback()
  if cur.rowcount > 0:
    resultTuple = cur.fetchall() # a list of tuples
  else:
    print "No records returned"
  return resultTuple

#----------------------------------------------------------------------------
def dbTransact(conn, sql, params):
  """Manage database transactions. """
  # ===!!! This is specific to single row INSERTS only !!!!===
  cur = conn.cursor()
  try:
    cur.execute(sql, params)
  except psycopg2.Error as e:
    print 'db_util.dbTransact error: ' + e.pgerror
    print 'suspending execution'
    # rollback makes subsequent inserts fail when referring to PK of failed row
    conn.rollback()
    sys.exit()
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
class sqlArgosImport(object):

# =========TODO: convert to proper parameter passing!!!================

  # Does this one get used somewhere?????
  #getNewEncounters = 'SELECT * FROM working.encounter \
  #                    WHERE (featureid IN ' #%(feats)s)

  getAllEncounters = 'SELECT featureid FROM working.encounter \
                      WHERE featureid > 0 \
                      ORDER BY featureid;'

  getTransmits = 'SELECT measurementid, deviceid FROM get_transmits \
                  WHERE (ptt = %(ptt)s) AND (timevalue = %(timeVal)s)\
                  ORDER BY measurementid;'

  truncateWtgStaging = 'TRUNCATE TABLE working.encounter_stage;'

  appendStaging = 'INSERT INTO working.encounter_stage(featureid, featurecode, \
                    timevalue, fromlocation, individual, device, \
                    latitude, longitude, lc, argospass, deploydevice, photoid, \
                    derived, gps, sample, take, cruise, occurrence, mm_filter) \
                    (SELECT featureid, featurecode, timevalue, \
                      fromlocation, individual, device, latitude, longitude, \
                      lc, argospass, deploydevice, photoid, derived, gps, sample, \
                      take, cruise, occurrence, mm_filter \
                     FROM working.encounter \
                     WHERE (latitude <> 0) AND (featureid IN %(feats)s) \
                     ORDER BY featureid) \
                   RETURNING featureid;'

#----------------------------------------------------------------------------
class sqlToolbox(object):

  getSpecies = 'SELECT speciescode FROM working.species ORDER BY speciescode;'

  getCruises = 'SELECT DISTINCT cruise.code \
                FROM working.individual INNER JOIN working.cruise \
                    ON individual.initialcruise = cruise.cruiseid \
                WHERE (individual.species = %(code)s) \
                ORDER by cruise.code DESC;'

  getTags = 'SELECT measuringdevice.ptt \
             FROM working.measuringdevice INNER JOIN working.cruise \
                ON measuringdevice.cruise = cruise.cruiseid \
             WHERE (cruise.code = %(code)s) \
             ORDER BY measuringdevice.ptt;'

  getMeasDev = 'SELECT measuringdevice.ptt, individual.species, measuringdevice.device_type\
                FROM working.measuringdevice INNER JOIN working.cruise\
                    ON working.measuringdevice.cruise = working.cruise.cruiseid\
                INNER JOIN working.individual\
                    ON working.measuringdevice.individual = working.individual.individualid\
                WHERE (cruise.code = %(code)s)\
                ORDER BY individual.species,measuringdevice.ptt;'

  getDevice = 'SELECT deviceid \
               FROM working.measuringdevice INNER JOIN working.cruise \
               ON measuringdevice.cruise = cruise.cruiseid \
               WHERE (cruise.code = %(cruise)s) AND (measuringdevice.ptt = %(ptt)s);'

  getFeatures = 'SELECT featureid, featurecode, timevalue, fromlocation, \
                individual, device, latitude, longitude, lc, argospass, deploydevice, \
                photoid, derived, gps, sample, take, cruise, occurrence \
                FROM working.encounter \
                WHERE (device = %(device)s) \
                ORDER BY timevalue;'

  getStartDate = 'SELECT startdate, stopdate \
                    FROM working.measuringdevice \
                    WHERE (deviceid = %(device)s)'

#----------------------------------------------------------------------------
class sqlDuplicates(object):

  getPasses = 'SELECT encounter.featureid, encounter.featurecode, \
                encounter.timevalue, argospass.satellite, argospass.nbmes \
               FROM working.encounter INNER JOIN working.argospass \
               ON encounter.featureid = argospass.featureid \
               WHERE (encounter.device = %(devID)s) \
               AND (encounter.featureid IN %(featList)s) \
               ORDER BY encounter.featureid;'


# =========TODO: convert to proper parameter passing!!!================
  getMeasurements = 'SELECT measurement.measurementid \
                      FROM working.measurement \
                      WHERE measurement.featureid IN ' #%(feats)s)

  delArgosPass = 'DELETE FROM working.argospass \
                  WHERE featureid IN '

  delDevTransmit = 'DELETE FROM working.devicetransmit \
                    WHERE measurement IN '

  delMeasurement = 'DELETE FROM working.measurement \
                    WHERE featureid IN '

  delEncounter = 'DELETE FROM working.encounter \
                  WHERE encounter.featureid IN '

#----------------------------------------------------------------------------
class sqlDeployments(object):

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
class sqlMeasData(object):

  getTransmits = 'SELECT measurement.measurementid, devicetransmit.transmitid \
                  FROM working.devicetransmit \
                  INNER JOIN (working.encounter \
                    INNER JOIN working.measurement \
                      ON encounter.featureid = measurement.featureid) \
                    ON devicetransmit.measurement = measurement.measurementid \
                  WHERE (encounter.device = %(device)s) \
                  AND (devicetransmit.timevalue = %(timeVal)s);'

              # key:[CSVfield, paramID, domain, domID]
  statusDict = {"Transmits":[9,'counter',None],
                "BattVoltage":[10,"measunit","V"],
                "TransmitVoltage":[11,"measunit","V"],
                "TransmitCurrent":[12,"measunit","A"],
                "Temperature":[13,"measunit","dF"],
                "MaxDepth":[15,"measunit","m"],
                "ZeroDepthOffset":[16,'counter',None]
                }

  behavDict = {"Start":[28,'timestamp',None],
                "End":[29,'timestamp',None],
                "Shape":[32,'diveshape',None], #tba?
                "DepthMin":[33,"measunit","m"],
                "DepthMax":[34,"measunit","m"],
                "DurationMin":[35,"measunit","sec"],
                "DurationMax":[36,"measunit","sec"]
                }