#-------------------------------------------------------------------------------
# Name:        wc_data.py
# Purpose:
#
# Author:      tomas.follett
#
# Created:     10/29/2013
# Updated:     10/31/2013
#-------------------------------------------------------------------------------
from datetime import datetime
import os
import csv
import wtg_utils as util
import wtg_db_utils as db_util
import wtg_working_tables as tables

conn = db_util.getDbConn('mmi_wtg')
#----------------------------------------------------------------------------
def newGPS(devID,indID,devName,cruiseID,inFileName):
  # reads a raw FastGPS.csv file
  newLocs = []
  featID = 0
  from datetime import datetime
  with open(inFileName, 'rb') as inFile:
    reader = csv.DictReader(inFile)
    for row in reader:
        #if row["Latitude"]:
        dayPart = util.parseDate(row["Day"], True)  # "17-Jul-2011"
        timePart = datetime.time(datetime.strptime(row["Time"],'%H:%M:%S'))
        timeVal = datetime.combine(dayPart,timePart)
        try:# instantiate an Encounter object
          encObj = tables.Encounter(devName+'-'+timeVal.strftime('%m/%d/%y'),
                                    timeVal,
                                    0.0, # FromLocation, converted by object
                                    indID,
                                    devID,
                                    8,  # LC, converted by object
                                    row["Latitude"],
                                    row["Longitude"],
                                    0,    # ArgosPass
                                    0,    # PhotoID
                                    1,    # GPS
                                    cruiseID)
          # attempt to insert to db.Encounter
          featID = db_util.dbTransact(conn,encObj.queryText(),encObj.insertSQL())
          if featID != 0:
            gpsObj = tables.GPS_Info(row["LocNumber"],
                                      row["Failures"],
                                      row["Satellites"],
                                      row["Bad Sats"],
                                      row["Residual"],
                                      row["Time Error"],
                                      featID)
            gpsID = db_util.dbTransact(conn,gpsObj.queryText(),gpsObj.insertSQL())
        except Exception as e:
          print 'newGPS error: ' + e.message
          conn.rollback()
        finally:
          encObj = None
          conn.commit()
          newLocs.append(featID)

  return newLocs

#----------------------------------------------------------------------------
def newStatusData(ptt,devID,inFileName):
  newData = []
  statDict = db_util.sqlMeasData.statusDict
  with open(inFileName, 'rb') as inFile:
    reader = csv.DictReader(inFile)
    for row in reader:
      timeVal = util.getDateFromSerial(float(row['Received']))
      param = {'device': devID, 'timeVal':timeVal}
      # getTransmits returns a list of tuples[(measID,txID),(measID,txID)]
      featList = db_util.dbSelect(conn, db_util.sqlMeasData.getTransmits, param)
      if len(featList)<1:
        print "getStatus error: no transmit found for "+timeVal.strftime('%Y-%m-%d %H:%M:%S')
      # if multiple transmits found, only use the last one
      measID, txID = featList[-1]
      for key in statDict.keys():
        if row[key]:
          try:
            measObj=tables.MeasuredData(statDict[key][0], # ParameterID
                                        row[key],         # DataValue
                                        statDict[key][1], # ValueDomain
                                        statDict[key][2], # DomainID
                                        None,             # Invalid
                                        devID,            # DeviceID
                                        'devicetransmit', # MeasureType
                                        txID,             # TypeID
                                        measID)           # MeasurementID
            measID = db_util.dbTransact(conn,measObj.queryText(),measObj.insertSQL())
          except Exception as e:
            print 'newStatusData error: ' + e.message
            conn.rollback()
          finally:
            measObj = None
            conn.commit()
          newData.append(measID)

  return newData
#----------------------------------------------------------------------------
def newBehaviorData(ptt,devID,inFileName):
  newData = []
  behDict = db_util.sqlMeasData.behavDict
  with open(inFileName, 'rb') as inFile:
    reader = csv.DictReader(inFile)
    for row in reader:
      beh = row['What']
      if beh == 'Message':
        # find the message time to match with DeviceTransmit
        # THIS IS THE WRONG TIMEVAL!!!
        # Maybe record the time of the behavior, don't link to a transmit
        timeVal = util.getDateFromSerial(float(row['Start']))
        param = {'device': devID, 'timeVal':timeVal}
        # getTransmits returns a list of tuples[(measID,txID),(measID,txID)]
        featList = db_util.dbSelect(conn, db_util.sqlMeasData.getTransmits, param)
        if len(featList)<1:
          print "getStatus error: no transmit found for "+timeVal.strftime('%Y-%m-%d %H:%M:%S')
        # if multiple transmits found, only use the last one
        measID, txID = featList[-1]
      elif beh == 'Dive':
        for key in behDict.keys():
          if row[key]:
            try:
              measObj=tables.MeasuredData(behDict[key][0], # ParameterID
                                        row[key],          # DataValue
                                        behDict[key][1],   # ValueDomain
                                        behDict[key][2],   # DomainID
                                        None,              # Invalid
                                        devID,             # DeviceID
                                        '',                # MeasureType
                                        None,              # TypeID
                                        measID)            # MeasurementID
              measID = db_util.dbTransact(conn,measObj.queryText(),measObj.insertSQL())
            except Exception as e:
              print 'newBehaviorData error: ' + e.message
              conn.rollback()
            finally:
              measObj = None
              conn.commit()
            newData.append(measuredID)
        else:
            pass

  return newData
#----------------------------------------------------------------------------
def newHistosData(ptt,devID,inFileName):
  pass

#----------------------------------------------------------------------------
def main(tag_src):
  """ """
  inPath = os.path.abspath("R:\\Data\\Tag_Data")

  tagDict = db_util.getActiveTags(tag_src)
  for devID, vals in sorted(tagDict.items()):
    recover = False
    ptt = str(vals[0])
    devName = vals[1]
    indID = vals[5],
    cruiseID = vals[6],
    yr = str(vals[7])
    cruiseName = vals[8]
    tagType = vals[9]

    if tagType in (41,42,45):
      # ptt-FastGPS.csv for Recovered tags
      filePath = inPath+'\\'+yr+'\\'+cruiseName+'\\WC Recovered\\'+ptt+'\\'
      inFileName = filePath+ptt+'-FastGPS.csv'
      if os.path.exists(inFileName):
        recover = True
        RecGpsList = newGPS(devID,indID,devName,cruiseID,inFileName)
      else:
        print 'Recovered tag FastGPS not found for '+ptt

    if tagType in (38,39,40,41,42,43,44,45,46):
      # ptt-Status.csv
##      filePath = inPath+'\\'+yr+'\\'+cruiseName+'\\WC_Tx_Solved\\'+ptt+'\\'
##      inFileName = filePath+ptt+'-Status.csv'
##      #if os.path.exists(inFileName):
##      #  mdList = newStatusData(ptt,devID,inFileName)
##      #else:
##      #  print 'Status not found for '+ptt
##
      # Transmitted ptt-FastGPS.csv
      if not recover:
        filePath = inPath+'\\'+yr+'\\'+cruiseName+'\\WC_Tx_Solved\\'+ptt+'\\'
        inFileName = filePath+ptt+'-FastGPS.csv'
        if os.path.exists(inFileName):
          txGpsList = newGPS(devID,indID,devName,cruiseID,inFileName)
        else:
          print 'Transmit FastGPS not found for '+ptt
        pass
      # ptt-Behavior.csv
      #inFileName = filePath+ptt+'-Behavior.csv'
      #if os.path.exists(inFileName):
      #  mdList = newBehaviorData(ptt,devID,inFileName)
      #else:
      #  print 'Behavior not found for '+ptt

      # ptt-Histos.csv
      #inFileName = filePath+ptt+'-Histos.csv'
      #if os.path.exists(inFileName):
      #  mdList = newHistosData(ptt,devID,inFileName)
      #else:
      #  print 'Histos not found for '+ptt



    if tagType in (30,31,32,33,35,36,37):
      # ST-15
      pass
    if tagType in (24,25,26):
      # ST-21
      pass
    # and 47 is ST-27


if __name__ == '__main__':

    main('new_db')

##def newMeasuredData(devID, measID, txID ,statDict, val):
##
##  """ Append a new row to MeasuremedData """
##  # measID = 0
##  measList = []
##  try:
##    # parID, dataVal, valDom, domID, inv, devID, measID
##    measList.append(statDict[0])          # ParameterID
##    measList.append(val)                    # DataValue
##    measList.append(statDict[1])          # ValueDomain
##    measList.append(statDict[2])          # DomainID
##    measList.append(None)                   # Invalid
##    measList.append(devID)                  # DeviceID
##    measList.append('devicetransmit')       # MeasureType
##    measList.append(txID)                   # TypeID
##    measList.append(measID)                 # MeasurementID
##    measObj = tables.MeasuredData  (*measList)
##    #print 'Appending MeasuredData for Measurement # ' + str(measID)
##    measID = db_util.dbTransact(conn, measObj.queryText(), measObj.insertSQL())
##  except Exception as e:
##    print 'newMeasuredData error: ' + e.message
##  finally:
##    measList = None
##    measObj = None
##    conn.commit()
##  return measID
###----------------------------------------------------------------------------
##def newGPSEncounter(tagDict,timeVal,lat,lon):
##  """ Append a new row to Encounter """
##  featID = 0
##  encList = []
##  # key from devDict
##  devID = tagDict.keys()[0]
##  tagName = tagDict.get(devID)[1]
##  indivID = tagDict.get(devID)[5]
##  cruiseID = tagDict.get(devID)[6]
##  #list to make the Encounter object
##  encList.append(tagName+'-'+timeVal.strftime('%m/%d/%y'))
##  encList.append(timeVal)
##  encList.append(0.0)     # FromLoc created by object
##  encList.append(indivID)
##  encList.append(devID)
##  encList.append(8)
##  encList.append(lat)
##  encList.append(lon)
##  encList.append(1)
##  encList.append(0)
##  encList.append(cruiseID)
##  try:    # instantiate an Encounter
##    encObj = tables.Encounter(*encList)
##    # attempt to insert to db.Encounter
##    featID = db_util.dbTransact(conn, encObj.queryText(), encObj.insertSQL())
##  except Exception as e:
##    print 'newGPSEncounter error: ' + e.message
##    conn.rollback()
##  finally:
##    encList = None
##    encObj = None
##    conn.commit()
##  return featID
