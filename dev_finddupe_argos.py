"""Return a list of duplicate featureid's to delete from argos
  and write them to a log file"""
# Occasionally, when a given pass is downloaded, the act of downloading is DURING
# the pass and CLS doesn't send the complete pass + messages. When downloaded
# subsequently, there can be additional messages within the same pass, with a
# different location etc.
import datetime
import psycopg2
import csv
import os
from os import path
import dev_db_utils as dbutil
from collections import OrderedDict

#-------------------------------------------------------------------------------
outPath = os.path.abspath("R:\\Data\\Tag_Data\\")
outFile = ''
conn = dbutil.getDbConn('wtg_gdb')

#==================================================================

def getDuplicates(tagDict, data_dir):

    # Obtain argos passes
    featIDs = []
    skipID = []
    logger = []
    for ptt, vals in sorted(tagDict.items()):  # sorted on DevID
        device = str(vals[0])  # int
        yr = datetime.datetime.strftime(vals[2],"%Y")
        outFile = path.join(outPath,yr,data_dir,'2019 Duplicates.csv')
#        outFile = path.join(outPath,'Archive',yr,'2019 Duplicates.csv')
        print "Processing duplicates for PTT: " + str(ptt)
        # Select all feats for device into a dict
        param = {'devID': device, }
        featList = dbutil.dbSelect(conn, dbutil.sqlDuplicates.getPasses, param)
        for tup in featList:
            featID = tup[0]
            if featID in skipID:
                # if the previous featID WAS the duplicate, then skip it
                skipID.remove(featID)
                continue
            # var's from this pass
            timeVal = tup[1]
            sat = tup[2]
            nbMes = tup[3]
            timeStart = timeVal + datetime.timedelta(minutes=-6)
            timeStop = timeVal + datetime.timedelta(minutes=6)
            # List of passes from the same Satellite within a 12 minute window
            # *** USUALLY only one match
            dupeList = (row for row in featList if (
                        row[2]==sat and
                        row[1]>timeStart and
                        row[1]<timeStop and
                        row[0]<>featID)
                        )
            # Compare nbMes between match(es) and current pass
            # ** Normally, if there are additional msgs it is the later version of the pass
            for row in dupeList:
                if row[3] > nbMes:            # This one has more msgs
                    featIDs.append(featID)    # Mark the original for deletion
                    skipID.append(row[0])
                    logger.append([featID,ptt,timeVal.strftime('%Y-%m-%d %H:%M:%S'),sat,nbMes])
                elif row[3] < nbMes:
                    featIDs.append(row[0])    # mark the match for deletion
                    skipID.append(row[0])
                    logger.append([row[0],ptt,row[1].strftime('%Y-%m-%d %H:%M:%S'),row[2],row[3]])
                # Compare pass time
                elif row[3] == nbMes:
                    if row[1] < timeVal:        # This one is earlier
                        featIDs.append(row[0])  # Mark the match for deletion
                        skipID.append(row[0])
                        logger.append([row[0],ptt,row[1].strftime('%Y-%m-%d %H:%M:%S'),row[2],row[3]])
                    else:
                        featIDs.append(featID)  # mark the original for deletion
                        skipID.append(row[0])
                        logger.append([featID,ptt,timeVal.strftime('%Y-%m-%d %H:%M:%S'),sat,nbMes])

        print str(ptt) + '...Done'
    #write deletions to log
    with open(outFile, 'ab') as outputFile:
        writer = csv.writer(outputFile)
        writer.writerow(["FeatureID","Tag","TimeValue","Sat.","NbMsgs"])
        for f in logger:
            writer.writerow(f)
    return featIDs


#-------------------------------------------------------------------------------

def main():
    proj = '2019HI'
    data_dir = 'Mar_HI_Hump'
    tagDict = dbutil.getDeployTags(conn,proj)
    featList = getDuplicates(tagDict,data_dir)

    return featList


if __name__ == '__main__':


    main()
