#------------------------------------------------------------------------------
# Name:        Argos_Import
# Author:      tomas.follett
#
# Created:      02/26/2013
# Update:      10/07/2017
#------------------------------------------------------------------------------
import csv
import datetime
from dateutil import parser
from collections import OrderedDict
from os import path

# local modules
import dev_tables as tables
import dev_f_utils as util
import dev_db_utils as dbutil
import dev_finddupe_argos as dupes

# constants
INPATH = path.abspath('\\\\MMIDATA\\Public\\Data')
conn = dbutil.getDbConn('wtg_gdb')
rawFmt = "%Y/%m/%d %H:%M:%S"
pttFmt = "%Y-%m-%d %H:%M:%S"

#----------------------------------------------------------------------------
def addArgos(row, tag_id, animal_id, timevalue, gt, bd):
    """ Append a new row to Argos, then to Transmit """
    feature_id = 0
    feature_type = 'argos'

# Doesn't seem to matter if db receives datetime or string

    timeVal = util.date2Str(timevalue, rawFmt) if bd else timevalue
    try:
        dev = (tag_id, animal_id, timeVal, feature_type, gt)                    # instantiate Argos object
        argosObj = tables.Argos(*dev, **row)                                    # returns 0 if duplicate
        feature_id = dbutil.dbTransact(conn,argosObj.sql_insert(),argosObj.param_dict())
        if feature_id:
            transmit_id = addTransmit(feature_id, row, bd)

    except Exception as e:
        print 'addArgos Error '+ e.message
        conn.rollback()
    finally:
        dev = None
        argosObj = None
        conn.commit()

        updateDevice(tag_id, timevalue, bd)
    return feature_id

#----------------------------------------------------------------------------
def addTransmit(feature_id, row, bd):
    transmit_id = 0
    timeVal = util.date2Str(row['Msg Date'], rawFmt) if bd else row['Msg Date']
    try:
        feat = (timeVal, feature_id)
        transmitObj = tables.ArgosTx(*feat, **row)
        transmit_id = dbutil.dbTransact(conn, transmitObj.sql_insert(),transmitObj.param_dict())
    except Exception as e:
        print 'addTransmit error '+e.message
        conn.rollback()
    finally:
        feat = None
        transmitObj = None
        conn.commit()

    updatePttList(int(row['Platform ID No.']), row['Msg Date'],bd)
    return transmit_id
#----------------------------------------------------------------------------
def updateDevice(tag_id, last_date, bd):

    timeVal = util.date2Str(last_date, rawFmt) if bd else last_date

    try:
        dev = (tag_id, timeVal)
        deviceObj = tables.Device(*dev)
        dbutil.dbUpdate(conn, deviceObj.sql_update_last(),deviceObj.param_dict())

    except Exception as e:
        print 'updateDevice error '+e.message
        conn.rollback()
    finally:
        dev = None
        deviceObj = None
        conn.commit()

#----------------------------------------------------------------------------
def updatePttList(ptt, last_date, bd):

    timeVal = util.date2Str(last_date, rawFmt) if bd else last_date
    try:
        vals = (ptt, timeVal)
        pttObj = tables.PttList(*vals)
        dbutil.dbUpdate(conn, pttObj.sql_update_last(),pttObj.param_dict())
    except Exception as e:
        print 'updatePttList error '+e.message
        conn.rollback()
    finally:
        vals = None
        pttObj = None
        conn.commit()

#----------------------------------------------------------------------------
def newOrphan(row, source, gt):
    yr = str(datetime.datetime.now().year)
    ptt = int(row["Platform ID No."])
    tag_dict = dbutil.getOrphanTags(conn, ptt)
    tags = sorted([tag for tag in tag_dict.keys()], reverse=True)
    for tag in tags[:1]:
        data = tag_dict[tag]
        if not data[2]:
            continue
        if data[2].year > int(yr)-1: #stop_date
            tx_time = util.str2Date(row["Msg Date"],rawFmt)
            sched = [int(h) for h in data[3].split(',')]
            if data[4]: #sched2_start
                if tx_time > data[4]:
                    sched = [int(h) for h in data[5].split(',')]
            if tx_time.hour in sched:
                print "Check  "+str(ptt)+" from "+data[0]
            else:
                if tx_time.minute < 20:
                    for hr in sched:
                        if tx_time.hour == hr+1:
                            print "Check  "+str(ptt)+" from "+data[0]
        else:
            continue

    # Use rowField to keep fieldnames in the correct order
    # temp list to format row for append
    orphanList = []
    # open the correct orphan.csv
    outPath = path.dirname(source)
    with open(outPath+'\\Orphan_2019.csv', 'ab') as outFile:
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
        readList = [r for r in csv.DictReader(temp) if r['Platform ID No.']==inPtt
                                                  and r['Pass']==inPass
                                                  and r['Msg Date'][:10]==inDate]
        time1 = util.str2Date(readList[0]["Msg Date"],rawFmt)   # first
        time2 = util.str2Date(readList[-1]["Msg Date"],rawFmt)  # last
        delta = time2 - time1
        # format passTime to eliminate fractional seconds
        timeValue = format(time1 + (delta / 2), rawFmt)
  except Exception as e:
      print 'getPassTime error: ' + str(e.message)
  finally:
      readList = None
  return timeValue
#----------------------------------------------------------------------------
def parseCSV(tagDict, inFileName):
    """ parse input CSV into parent/child tables """

    csvName = path.basename(inFileName)
    # Trap raw argos files that occurred within these BAD dates, when format was inadvertantly changed
    bd = False
    if csvName >= util.CSV_schema.bad_dates[0][0]:
        if csvName <= util.CSV_schema.bad_dates[0][1]:
            bd = True
    if csvName >= util.CSV_schema.bad_dates[1][0]:
        if csvName <= util.CSV_schema.bad_dates[1][1]:
            bd = True

    # list of FeatureID's that get added
    newPasses = []
    d_ptt = {v[0]:k for k,v in tagDict.items()}
    pttDict = OrderedDict(sorted(d_ptt.items())) #=integer                      # Sort into {ptt: tag_id}
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
            timeVal = None
            passDur = None
            for row in reader:
                if row['Platform ID No.'][0] =='#':
                    continue
                # TOPP Program number
##                if row['Prg No.'] != '4802':
##                    continue
                if  int(row['Platform ID No.']) not in pttDict.keys():          # Orphan Tag
                    tag_id = 0
                    newOrphan(row, inFileName, gt)
                    msgType = 'NEW'
                    #print "Orphan tag #" +row['Platform ID No.']
                    #updatePttList(ptt, row['Msg Date'],bd)
                    continue
                elif int(row['Platform ID No.']) != ptt:                        # New Tag
                    ptt = int(row['Platform ID No.'])
                    tag_id = pttDict[ptt]
                    pttStart =  tagDict.get(tag_id)[1] # datetime
                    pttStop   = tagDict.get(tag_id)[2] # datetime
                    animal_id = tagDict.get(tag_id)[4]
                    # loop vars
                    msgType = 'NEW'
                    # need to keep string date for later comparison
                    timeVal = row['Loc. date'] if row['Loc. date'] else row['Msg Date']
                    passDur = row['Pass']
                    sat = row['Sat.']
                    if not pttStart:
                        print 'Undeployed tag in tagDict'

                if util.str2Date(timeVal, rawFmt) < pttStart:                   # Trap: Earlier than tag's start date
                    ptt = 0                                                     # Force new ptt Variables for next row
                    continue

                elif util.str2Date(timeVal, rawFmt) > pttStop:
                    ptt = 0
                    continue

                if msgType == 'SAME':
                    if row['Loc. date']:
                        if row['Loc. date'] == timeVal:
                            if row['Pass'] != passDur:
                                msgType = 'NEW'
                                passDur = row['Pass']
                                sat = row['Sat.']
                            if row['Sat.'] != sat:
                                msgType = 'NEW'
                                sat = row['Sat.']
                        elif row['Loc. date'] != timeVal:                       # Definitely New pass
                            msgType = 'NEW'
                            timeVal = row['Loc. date']
                            passDur = row['Pass']
                            sat = row['Sat.']
                    else: #if not row['Loc. date']:
                        if row['Pass'] == '0':                                  # Single pass
                            msgType = 'NEW'
                            timeVal = row['Msg Date']
                            passDur = None # OR '0'
                            sat = row['Sat.']
                        elif row['Pass'] != '0':                                # Multi-Z pass
                            if row['Pass'] != passDur:                          # still in same pass
                                msgType = 'NEW'
                                timeVal = getPassTime(inFileName,row['Pass'],
                                                      str(ptt),
                                                      row['Msg Date'][:10])
                                passDur = row['Pass']
                                sat = row['Sat.']
                if msgType == 'SAME':                                           #Append: to Transmit
                    if featID:
                        transmitID = addTransmit(featID,row,bd)

                if msgType == 'NEW':                                            # Append: to Argos & Transmit
                    featID = addArgos(row,tag_id,animal_id,timeVal,gt,bd)
                    msgType = 'SAME'
                    if featID:
                        print 'Pass at: [{0}] added for {1}'.format(timeVal,ptt)
                        newPasses.append(featID)
    return newPasses

#----------------------------------------------------------------------------
def main(tagDict, csv_src, start_date, end_date):

    featList = []
    if csv_src == 'tags':
        # bulk mode
        #iterate thru each ptt in tagDict
        for tag_id, devVals in sorted(tagDict.items()):
            devDict = {tag_id: devVals}   # mini dict for This ptt
            ptt = str(devDict[tag_id][0]) # string
            inFileName = '\\'.join((INPATH,'Tag_Data',
                                str(devDict[tag_id][6]),    # Year
                                devDict[tag_id][7],'CSV',   # Data Dir\\CSV
                                ptt+'.csv'))
            if path.exists(inFileName):
                print 'Beginning processing: ' + ptt
                newPasses = parseCSV(devDict, inFileName)
                featList.extend(newPasses)
                # ****** Update Deployment table for this tag
                #dbutil.updateDeployment(conn, tag_id)
                print ptt + '...Done'
            else:
                # ptt.csv not found, skip tag
                print 'File not found: '+p_csv
                continue

    elif csv_src == 'raw':
        # active mode
        #iterate thru each date.csv file
        currDate = start_date
        while currDate <= end_date:
            # construct input filenames from currDate
            inFileName = '\\'.join((INPATH,'Argos_Raw',
                                    'Data'+currDate.strftime('%Y'),
                                    currDate.strftime('%y%m%d')+'.csv'))
            if path.exists(inFileName):
                print 'Processing file: ' +inFileName
                # process Argos file and load passes to Database
                newPasses = parseCSV(tagDict, inFileName)
                if not newPasses:
                    print 'No new passes found'
                else:
                    featList.extend(newPasses)
                    # ****** Update Deployment table for all PTTs
                    #for tag_id in tagDict.keys():
                        #dbutil.updateDeployment(conn, tag_id)
            else:
                print inFileName +' does not exist. Trying next date...'
            # advance to next date
            currDate += datetime.timedelta(1)
    return featList
#----------------------------------------------------------------------------

if __name__ == '__main__':

#    reload(tables)
#    reload(dbutil)
    #source = 'active'
    proj = '2019WA'

#    tags = (615,)
    tagDict = dbutil.getActiveTags(proj)

# ******** CHOOSE the FORM ***********
#    csv_src = 'tags'
    csv_src = 'raw'
# ************************************
    #start_date = min([d[1][1] for d in tagDict.items()])
    start_date = datetime.datetime(2019,10,28)
#***************************************************************
# Look at line 74 re: updates

    #end_date    = max([d[1][2] for d in tagDict.items()])
    #if end_date == datetime.datetime(2099,1,1,0,0):
    end_date = datetime.datetime.today()

    """ PREVENT ACCIDENTAL LOADING """
    pass
    main(tagDict, csv_src, start_date, end_date)

#----------------------------------------------------------------------------
##    start_date = datetime.datetime.strptime('2017-9-14','%Y-%m-%d')
##    end_date = datetime.datetime.strptime('2019-1-01','%Y-%m-%d')










