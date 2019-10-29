#-------------------------------------------------------------------------------
# Name:        argos_load
#
# Created:    6/21/2013
# Updated:    9/09/2013
# Input Parameters:
#   mode - 'update' = insert active tags into a Dict (and dormant...)
#        - 'bulk'   =
#        - 'test'   =
#   new_csv - T/F
#   days - # of days before today to review
# ------------------------------------------------
# Output parameters:
#   for appendCSV: (passes to utils.getActiveTags)
#   tag_src - 'active'  status = 'active'
#           - 'new_csv' rebuildcsv = 1
#           - 'new_db'  rebuilddb = 1
#   Appends ptt.csv's and returns tagDict
# ------------------
#   for appendDB:
#   startDate -
#   csv_src - 'raw'  = active mode, loop thru each date.csv file, starting from startDate
#           - 'tags' = bulk mode, iter thru each ptt.csv for each tag in tagDict
#
#-------------------------------------------------------------------------------
import wtg_db_utils as dbutil
import working_individual_csv as appendCSV
import working_argos_import as appendDB
import working_new_features as appendGDB
import working_trap_dupes as deleteDupe
import datetime
import csv
#-------------------------------------------------------------------------------
def insertDeploys():
  conn = dbutil.getDbConn('mmi_wtg')
  sql = dbutil.sqlDeployments.insertDeploys
  deploys = dbutil.dbSelect(conn, sql, ())

  return deploys
#-------------------------------------------------------------------------------
def main(mode, new_csv, days):
  newPasses = []
  outFile = 'R:\\Data\\Tag_Data\\FeatureList.csv'
  if mode == 'update':
    tagDict = appendCSV.main('active')              # update CSVs first
#    tagDict = dbutil.getActiveTags('active')       # skip the CSV update
    # set starting date for csv's
    startDate = datetime.datetime.today() - datetime.timedelta(days)
    newPasses = appendDB.main(tagDict, 'raw', startDate)
#    newPasses = range(121151,121321)               # range needs +1 for end!!
    if newPasses:
        deletions = deleteDupe.main(tagDict, newPasses)
        newFeatures = appendGDB.main(newPasses)
    else:
        print('Something done broke')

  elif mode == 'bulk':
    if new_csv: # only if overwrite csv's required
      tagDict = appendCSV.main('new_csv')
    else:
#      print 'updating CSVs first...'
      #tagDict = appendCSV.main('new_db')              # update CSVs first
      print 'updating database...'
      tagDict = dbutil.getActiveTags('new_db')         # skip the CSV update

    # start parsing CSV's
    print 'Appending CSV files to mmi_wtg...'
    # normal load
    newPasses = appendDB.main(tagDict, 'tags', None)
    # if interrupted
    #newPasses = range(115334,115675)              # range needs +1 for end!!

    print 'Trapping true duplicates for deletion...'
    deletions = deleteDupe.main(tagDict, newPasses)
    # remove deleted featureIDs from newPasses
    for fid in newPasses:
      if fid in deletions:
        newPasses.remove(fid)

    # write newPasses to log file for later use by new_features
    #with open(outFile, 'wb') as outputFile: # overwrite mode ???
    #  writer = csv.writer(outputFile)
    #  for fid in newPasses:
#===ERROR: "sequence expected" ?
    #    writer.writerow(fid,)

    # create features to populate sde.encounter
    newFeatures = appendGDB.main(newPasses)

  elif mode == 'test':
    tagDict = appendCSV.main((654))
    newPasses = appendDB.main(tagDict, 'tags', None)

  elif mode == 'deploy':
    newPasses = insertDeploys()
    newFeatures = appendGDB.main(newPasses)

  return newPasses

  # write list of new Encounters to log?
##  orphanCSV = 'R:\\Data\\Tag_Data\\Orphan_Data\\orphans.csv'
##  with open(orphanCSV, 'ab') as outFile:
##    writer = csv.writer(outFile,delimiter=',', quoting=csv.QUOTE_ALL)
##    #writer.writerow(util.CSV_schema.header)
##    for line in newPasses:
##      writer.writerow(line)

#-----------------------------------------------------------------------------
if __name__ == '__main__':

    #main('deploy', False, 0)

    #main(mode='test', new_csv=False, days=2)

    # append csv's and database with new data
    main(mode='update', new_csv=False, days=7)

    # load entire dataset to new <<name?>> database
    #main(mode='bulk', new_csv=False, days=2)

    # same but first re-create csv's
    #main(mode='bulk', new_csv=True, days=14)
