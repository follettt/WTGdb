#-------------------------------------------------------------------------------
# Name:        wtg_TrapDuplicates

# Author:      tomas.follett
#
# Created:     09/09/2013
# Updated:     09/24/2013

# This affects the "working" schema
#-------------------------------------------------------------------------------
import datetime
import sys
import os
import csv
import wtg_db_utils as dbutil

outPath = os.path.abspath("R:\\Data\\Tag_Data\\")
outFile = ''
conn = dbutil.getDbConn('mmi_wtg')
#==================================================================

def getDuplicates(tagDict, newFeats):
  """Return a list of duplicate featureid's to delete from encounter
      and write them to a log file"""

  featIDs = []
  skipID = []
  logger = []
  for device, vals in sorted(tagDict.items()):  # sorted on DevID
    ptt = str(vals[0])  # int
    yr = str(vals[7])   # int
    cruise = vals[8]    # str
    outFile = outPath +'\\'+yr+'\\'+cruise+'\\DuplicatesDeleted.csv'
    print "Processing duplicates for PTT: " + ptt
    param = {'devID': device, 'featList': tuple(newFeats)}
    featList = dbutil.dbSelect(conn, dbutil.sqlDuplicates.getPasses, param)

    # iter over features to find dupes
    for tup in featList:
      featID = tup[0]
      if featID in skipID:
        skipID.remove(featID)
        continue                # if lastID was the duplicate skip it
      tag = tup[1][:-9]
      timeVal = tup[2]
      sat = tup[3]
      nbMes = tup[4]
      timeStart = timeVal + datetime.timedelta(minutes=-6)
      timeStop = timeVal + datetime.timedelta(minutes=6)
      dupeList = (row for row in featList if (
                    row[3]==sat and
                    row[2]>timeStart and
                    row[2]<timeStop and
                    row[0]<>featID))

      for row in dupeList:
        if row[4] > nbMes:
          featIDs.append(featID)    # mark the original for deletion
          skipID.append(row[0])
          logger.append([featID,tag,timeVal.strftime('%Y-%m-%d %H:%M:%S'),sat,nbMes])

        elif row[4] < nbMes:
          featIDs.append(row[0])    # mark the match for deletion
          skipID.append(row[0])
          logger.append([row[0],row[1],row[2].strftime('%Y-%m-%d %H:%M:%S'),row[2],row[3]])

        elif row[4] == nbMes:
          if row[2] < timeVal:
            featIDs.append(row[0])  # mark the match for deletion
            skipID.append(row[0])
            logger.append([row[0],row[1],row[2].strftime('%Y-%m-%d %H:%M:%S'),row[3],row[4]])
          else:
            featIDs.append(featID)  # mark the original for deletion
            skipID.append(row[0])
            logger.append([featID,tag,timeVal.strftime('%Y-%m-%d %H:%M:%S'),sat,nbMes])
    print ptt + '...Done'
  #write deletions to log
  with open(outFile, 'ab') as outputFile:
    writer = csv.writer(outputFile)
    writer.writerow(["FeatureID","TagName","TimeValue","Sat.","NbMsgs"])
    for f in logger:
      writer.writerow(f)
  return featIDs

def delDuplicates(features):
  # ======== Hangs on single FeatureID b/c of parenthesis in tuple
  # =========TODO: convert to proper parameter passing!!!================
  # 1 fetch MeasurementID's
  sql = dbutil.sqlDuplicates.getMeasurements
  if len(features)==1:
    param = '('+str(features[0])+')'
  else:
    param = tuple(features)
  sql = sql + str(param) + ';'
  result = dbutil.dbSelect(conn, sql, ())
  measList = [f[0] for f in result]

  if len(measList) > 0:
    # 2 DEL from DeviceTransmit
    sql = dbutil.sqlDuplicates.delDevTransmit
    if len(features)==1:
      param = '('+str(measList[0])+')'
    else:
      param = tuple(measList)
    sql = sql + str(param) + ';'
    result = dbutil.dbDelete(conn, sql)
    if result == 'Failed':
      print 'Delete from DeviceTransmit failed'
      conn.rollback()
      sys.exit
    else:
      print result
      conn.commit()

    # 3 DEL from Measurement
    sql = dbutil.sqlDuplicates.delMeasurement
    if len(features)==1:
      param = '('+str(features[0])+')'
    else:
      param = tuple(features)
    sql = sql + str(param) + ';'
    result = dbutil.dbDelete(conn, sql)
    if result == 'Failed':
      print 'Delete from Measurement failed'
      conn.rollback()
      sys.exit
    else:
      print result
      conn.commit()

  else:
    print 'No Measurements found'

  # 4 DEL from ArgosPass
  sql = dbutil.sqlDuplicates.delArgosPass
  if len(features)==1:
    param = '('+str(features[0])+')'
  else:
    param = tuple(features)
  sql = sql + str(param) + ';'
  result = dbutil.dbDelete(conn, sql)
  if result == 'Failed':
    print 'Delete from ArgosPass failed'
    conn.rollback()
    sys.exit
  else:
    print result
    conn.commit()

# 5 DEL duplicate encounters
  sql = dbutil.sqlDuplicates.delEncounter
  if len(features)==1:
    param = '('+str(features[0])+')'
  else:
    param = tuple(features)
  sql = sql + str(param) + ';'
  result = dbutil.dbDelete(conn, sql)
  if result == 'Failed':
    print 'Delete from Encounter failed'
    conn.rollback()
    sys.exit
  else:
    print result
    conn.commit()

  print '...Done with deletions'
def main(tagDict, newFeats):

  featList = getDuplicates(tagDict, newFeats)
  if featList:
    delDuplicates(featList)
    return featList
  else:
    print "No duplicates found"
    return newFeats

if __name__ == '__main__':

    main(inDict, inFeats)


