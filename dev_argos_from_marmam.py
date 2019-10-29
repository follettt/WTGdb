#------------------------------------------------------------------------------
# Name:        Argos_Import
# Author:      tomas.follett
#
# Created:      02/26/2013
# Update:      10/07/2017
#------------------------------------------------------------------------------
import csv
import datetime
from collections import OrderedDict
from os import path

# local modules
import dev_legacy_tables as tables
import wtg_utils as util
import dev_db_utils as dbutil

# constants
INPATH = path.abspath('\\\\MMIDATA\\Public\\Data')
conn = dbutil.getDbConn('wtg_gdb')
#----------------------------------------------------------------------------
def format_date(str_date, bd):
    # '%Y/%m/%d %H:%M:%S' RAW Argos date.csv format
    # '%m/%d/%Y %H:%M:%S' DB extract Argos.csv

    if bd:                                             # format of incoming string
        timevalue = datetime.datetime.strptime(str_date, "%d/%m/%y %H:%M:%S") #dd/mm/yy
    else:
        timevalue = datetime.datetime.strptime(str_date, '%m/%d/%Y %H:%M:%S')

    return timevalue
#----------------------------------------------------------------------------
def addArgos(row, tag_id, animal_id, timevalue, gt, bd):
    """ Append a new row to Argos then to Message and Transmit """
    feature_id = 0
    feature_type = 'argos'
    try:
        dev = (tag_id, animal_id, timevalue, feature_type, gt)                  # instantiate Argos object
        argosObj = tables.Argos(*dev, **row)                                    # returns 0 if duplicate
        feature_id = dbutil.dbTransact(conn,argosObj.sql_insert(),
                                                argosObj.param_dict())
        if feature_id:
            transmit_id = addTransmit(feature_id, row, bd)

    except Exception as e:
        print 'addArgos Error '+ e.message
        conn.rollback()
    finally:
        dev = None
        argosObj = None
        conn.commit()
    return feature_id

#----------------------------------------------------------------------------
def addTransmit(feature_id, row, bd):
    transmit_id = 0
    timevalue = format_date(row['ldatetime'], bd)
    try:
        feat = (timevalue, feature_id)
        transmitObj = tables.ArgosTx(*feat, **row)
        transmit_id = dbutil.dbTransact(conn, transmitObj.sql_insert(),
                                                transmitObj.param_dict())
    except Exception as e:
        print 'addTransmit error '+e.message
        conn.rollback()
    finally:
        feat = None
        transmitObj = None
        conn.commit()
    return transmit_id, timevalue
#----------------------------------------------------------------------------
def updateDevice(tag_id, timevalue, bd):
    result = None
    try:
        dev = (tag_id, timevalue)
        deviceObj = tables.Device(*dev)
        dbutil.dbUpdate(conn, deviceObj.sql_update_last(),
                                deviceObj.param_dict())
    except Exception as e:
        print 'updateDevice error '+e.message
        conn.rollback()
    finally:
        dev = None
        deviceObj = None
        conn.commit()

#----------------------------------------------------------------------------
def updatePttList(ptt, timevalue, bd):
    result = None
    try:
        vals = (ptt, timevalue)
        pttObj = tables.PttList(*vals)
        dbutil.dbUpdate(conn, pttObj.sql_update_last(),
                                pttObj.param_dict())
    except Exception as e:
        print 'updatePttList error '+e.message
        conn.rollback()
    finally:
        vals = None
        pttObj = None
        conn.commit()

#----------------------------------------------------------------------------
def newOrphan(row, source, gt):
    # Use rowField to keep fieldnames in the correct order
    # temp list to format row for append
    orphanList = []
    # open the correct orphan.csv
    outPath = path.dirname(source)
    with open(outPath+'\\Orphan_2017.csv', 'ab') as outFile:
        writer = csv.writer(outFile)
        # date.csv name is the first column
        orphanList.append(path.basename(source))
        if 'Format name' in row.keys():
            row.pop('Format name')
        for i in range(len(row)):
            # >-120 fieldname FUCKING Argos
            if i == 10 and gt:
                orphanList.append(row['> - 120 DB'])
            else:
                orphanList.append(row[util.CSV_schema.rowField[i]])
        writer.writerow(orphanList)
    return

#----------------------------------------------------------------------------
def getPassTime(inFileName, inPass, inPtt, inDate):
  """ reconstruct Pass TimeValue from transmit times """
  # from ptt and passDur, add msg dates to a dict then average them
  timeValue = ''
  try:
    with open(inFileName, 'rb') as temp:
        readList = [row for row in csv.DictReader(temp) if row['Platform ID No.']==inPtt
                                                  and row['pass']==inPass
                                                  and row['ldatetime'][:10]==inDate] # *** Seems like this could wrap into the next day
        time1 = format_date(readList[0]["ldatetime"])   # first
        time2 = format_date(readList[-1]["ldatetime"])  # last
        mid_time = time1 + (time2 - time1)/2
        # format passTime to eliminate fractional seconds
# ***** Does this even work on datetime object ????
        timeValue = format(mid_time, "%Y/%m/%d %H:%M:%S")
  except Exception as e:
      print 'getPassTime error: ' + str(e.message)
  finally:
      readList = None
      temp.close()
  return timeValue
#----------------------------------------------------------------------------
def parseRaw(tagDict, inFileName):
    """ parse input CSV into parent/child tables """

    csvName = path.basename(inFileName)
    # Trap argos raw files that occurred within these dates
    # date formatted dd/mm/yy instead of yyyy/mm/dd
    bd = False
##    if csvName >= util.CSV_schema.bad_dates[0][0]:
##        if csvName <= util.CSV_schema.bad_dates[0][1]:
##            bd = True
##    if csvName >= util.CSV_schema.bad_dates[1][0]:
##        if csvName <= util.CSV_schema.bad_dates[1][1]:
##            bd = True

    newPasses = []
    d_ptt = {v[0]:k for k,v in tagDict.items()}
    pttDict = OrderedDict(sorted(d_ptt.items()))                                # Sort into {ptt: tag_id, ....}
    del d_ptt
    with open(inFileName, 'rb') as inFile:
        count = sum(1 for line in inFile)
        inFile.seek(0)  # reset file
        reader = csv.DictReader(inFile)
        while reader.line_num < count:
            # Trap for changed fieldname
            gt = True if util.CSV_schema.gt_names[1] in reader.fieldnames else False
            featID = None
            ptt = 0
            msgType = 'NEW'
            str_timeval = ''
            passDur = None
            for row in reader:
                # row vals are ALL string
                if int(row['ptt']) != ptt:   # Start New PTT
                    if ptt:                                                     # Skip ptt = 0
                        tag_id = pttDict[ptt]
#                        dbutil.updateDeployment(conn, tag_id)                   # Update ptt that just finished
#                        updatePttList(ptt, last_msg, bd)
#                        updateDevice(tag_id, last_msg, bd)
                    msgType = 'NEW'
                    # tag specific vars
                    ptt = int(row['ptt'])  #=integer
                    tag_id = pttDict[ptt]
                    pttStart =  tagDict.get(tag_id)[1] #=datetimes
                    pttStop   = tagDict.get(tag_id)[2]
                    animal_id = tagDict.get(tag_id)[4] #=integer
                    # loop vars
                    if row['hdatetime']:
                        str_timeval = row['hdatetime']
                    else:
                        str_timeval = row['ldatetime'] if row['ldatetime'] else 'N/A'
                    timevalue = format_date(str_timeval,bd)
                    passDur = row['pass']
                    sat = row['satellite']
                # Trap out of range date
                if timevalue < pttStart:
                    ptt = 0                                                     # Force new ptt Variables for next row
                    continue
        # ********* NOT TRAPPING stoptime ??
                elif timevalue > pttStop:
                    ptt = 0
                    continue
                # start parsing
                last_msg = format_date(row['ldatetime'],bd)
                if msgType == 'SAME':
                    if row['hdatetime']:
                        if row['hdatetime'] == str_timeval:
                            if row['pass'] != passDur:
                                msgType = 'NEW'
                                passDur = row['pass']
                                sat = row['satellite']
                            if row['satellite'] != sat:
                                msgType = 'NEW'
                                sat = row['satellite']
                        elif row['hdatetime'] != str_timeval:                   # Definitely New pass
                            msgType = 'NEW'
                            str_timeval = row['hdatetime']
                            timevalue = format_date(str_timeval,bd)
                            passDur = row['pass']
                            sat = row['satellite']
                    else:                       # row['hdatetime'] empty
                        if row['pass'] == '0':                                  # Single pass
                            msgType = 'NEW'
                            str_timeval = row['ldatetime']
                            timevalue = format_date(str_timeval,bd)
                            passDur = None # OR '0'
                            sat = row['satellite']
                        elif row['pass'] != '0':                                # Multi-Z pass
                            if row['pass'] != passDur:                          # still in same pass
                                msgType = 'NEW'
                                str_timeval = getPassTime(inFileName,row['pass'],
                                                      str(ptt),
                                                      row['ldatetime'][:10])
                                timevalue = format_date(str_timeval,bd)
                                passDur = row['pass']
                                sat = row['satellite']
                if msgType == 'SAME':                                           #Append: to Transmit
                    if featID:
                        transmitID, last_msg = addTransmit(featID, row, bd)

                if msgType == 'NEW':                                            # Append: to Argos & Transmit
                    featID = addArgos(row, tag_id, animal_id, timevalue, gt, bd)
                    msgType = 'SAME'
                    if featID:
                        print 'Pass at: [{0}] added for {1}'.format(str_timeval, ptt)
                        newPasses.append(featID)

    return newPasses

#----------------------------------------------------------------------------
def main(tagDict, proj):

    featList = []
    #
    if proj > '2003MX':
        csvName = 'getOldArgos'
    elif proj < '2004CA':
        csvName = 'Argos-Marmam'
    if proj == '1996MX':
        csvName = 'Argos-DAP'

    inFileName = '\\'.join([INPATH,'Argos_Raw','Archive',csvName+proj+'.csv'])
    if path.exists(inFileName):
        print 'Processing file: ' +inFileName
        # process Argos file and load passes to Database
        newPasses = parseRaw(tagDict, inFileName)
        if not newPasses:
            print 'No new passes found'
        else:
            featList.extend(newPasses)
    else:
        print inFileName +' does not exist?'
    # advance to next date
    #currDate += datetime.timedelta(1)

    return featList
#----------------------------------------------------------------------------
"""
******** Version is specific to OLD database extract
******** query getOldArgosPROJ OR Argos-MarmamPROJ
"""
if __name__ == '__main__':

    proj = '2012PNW'
    tagDict = dbutil.getActiveTags(proj)

    """ PREVENT ACCIDENTAL LOADING """
    pass
    main(tagDict, proj)

