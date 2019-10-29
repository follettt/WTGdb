#-------------------------------------------------------------------------------
# Name:        individual_csv.py
# Purpose:     UPDATE ptt.CSV
#
# Author:      tomas.follett
#
# Created:      2/27/2013
# Updated:      9/09/2013
# Copyright:   (c) tomas.follett 2013
#-------------------------------------------------------------------------------
import csv
import datetime
import os
import dev_f_utils as f_util
import dev_db_utils as dbutil

# TODO: get from config
# Globals:
inPath = os.path.abspath("R:\\Data\\Argos_Raw\\Data")
outPath = os.path.abspath("R:\\Data\\Tag_Data")

date_fmt1 = '%Y/%m/%d %H:%M:%S'
date_fmt2 = '%Y-%m-%d %H:%M:%S'
##----------------------------------------------------------------------------
def getSeen(outFile, deploy):
  """ Gather the last 512 rows of data from the device's existing CSV """
  # *** If More than 256 new rows it will duplicate (ie: drifting MK-10's)
  # the number can be increased here and at line 118 (subtract 1)
  seen = []
  ##fileType = 0
  start = ''
  with open(outFile, 'rb') as srcFile: # rb = read
    # count the rows
    srcLen = len(list(csv.reader(srcFile)))
    # return to BOF after len()
    srcFile.seek(0)
    # set starting row
    if srcLen > 512:
      # reset counter
      srcLen = srcLen-512
    # empty file
    elif srcLen < 2:
      # return to calling function
      return deploy, seen
    # "Short" file, all rows into seen
    elif srcLen < 512:
        srcLen = 1
    srcDict = csv.DictReader(srcFile)
    for row in srcDict:
      # fast forward to start row
      if srcDict.line_num < srcLen:
        continue
      # append list of candidate duplicates
      seen.append([row["Pass"],row["Sat."],row["Msg Date"]])
      # use date for
      start = row["Msg Date"]

#******************   FIX THESE    ****************************************
    #startDate = f_util.parseDate(start, False) # datetime
    startDate = datetime.datetime.strptime(start, date_fmt2)
#**********************************************************

  return startDate, seen
#----------------------------------------------------------------------------
def addRows(outFile, currDate, endDate, ptt, seen):
  """ Get all unique new rows from an Argos CSV, and append them
      to the tag's PTT.csv Argos file. If it doesn't exist, create it """
  # dayfirst parameter for parseDate
  df = False
  # FIX? ==== sometimes fails here:
  #"TypeError: coercing to Unicode: need string or buffer, file found"

  with open(outFile, 'ab') as outputFile:
    # Init writer
    writer = csv.DictWriter(outputFile, f_util.fieldLists.csv_header,'', 'ignore')
    # open each daily CSV to extract rows
    while currDate <= endDate:
      pttFilter = []
      # construct input filename with formatted date string,
      inFileName = inPath+currDate.strftime('%Y')+ \
                     '\\'+currDate.strftime('%y%m%d')+'.csv'
      if not os.path.exists(inFileName):
        # skip to next date file
        currDate += datetime.timedelta(1)
        continue
      else:
        # trap for newer >-120 fieldname after 04/09/2013
        #if os.path.basename(inFileName) > f_util.CSV_schema.new_gt_date:
          #gt = True

##        # set dayfirst for files with wrong date format
##        file = os.path.basename(inFileName)
##        if file >= f_util.CSV_schema.bad_dates[0][0] and \
##                    file <= f_util.CSV_schema.bad_dates[0][1]:
##          df = True
##        elif file >= f_util.CSV_schema.bad_dates[1][0] and \
##                      file <= f_util.CSV_schema.bad_dates[1][1]:
##          df = True
##        else:
##          df = False

        with open(inFileName, 'rb') as inFile:
          # fetch only the rows that match this ptt
          # uses fieldnames as found in input csv, rather than CSV_schema
          # for compatability with older csv's
          pttFilter = [row for row in csv.DictReader(inFile)
                       if row["Platform ID No."] == ptt]
          for row in pttFilter:
            # verify/fix Msg Date format in row
#**********************************************************
            #row["Msg Date"] = f_util.formatStrDate(row["Msg Date"], df)
            row["Msg Date"] = datetime.datetime.strptime(row["Msg Date"], date_fmt1)
#**********************************************************
            if [row["Pass"],row["Sat."],row["Msg Date"]] in seen:
              # duplicate row, skip it
              continue
            else:
              if not row["Loc. date"] == '':
                # verify/fix Loc. Date format in row
#**********************************************************
                #row["Loc. date"] = f_util.formatStrDate(row["Loc. date"], df)
                row["Loc. date"] = datetime.datetime.strptime(row["Loc. date"], date_fmt1)
#**********************************************************
              # send it to outFile
 #             print "writing " + str(ptt) + ": message " + row["Msg Date"]
              writer.writerow(row)
              # update duplicate row list
              seen.append([row["Pass"],row["Sat."],row["Msg Date"]])
              # remove first row from seen
              if len(seen) > 511: seen.remove(seen[0])
##              if len(seen) > 511: seen.remove(seen[0])
          # end for row in pttFilter
        ## end with inFile
        # advance to next date
        currDate += datetime.timedelta(1)
      ## end if exists
    ## end while currDate <= endDate
  ## close outputFile
  print "Done with " + ptt
  return

#------------------------------------------------------------------------------
def main(tag_src):
  """ iterate through tags and add rows from raw argos date.csv files"""
  # pull tags according to purpose: active: status IN active, dormant
  #                                 new_csv: rebuildcsv = 1
  #                                 new_db: rebuilddb = 1
  #                                 list: specific active ptt's
  tagDict = dbutil.getActiveTags(tag_src)

  # iter thru tags to update each ptt.csv
  for device, vals in sorted(tagDict.items()):  # sorted on DeviceID
    ptt = str(vals[0])  # int
    deploy = vals[1]    # datetime
#    endDate = vals[2]   # datetime
    status = vals[3]    # str
    cruise = vals[5]    # str
    yr = str(vals[6])   # int
    datadir = vals[7]

    endDate = datetime.datetime.today()
    # refine end Dates according to status
    if status == "dormant":
      endDate = datetime.datetime.today()
    elif status == 'active':
    # add 1 day to grab everything possible
        ##if endDate == datetime.datetime(2099, 01, 01, 0, 0, 0):
      endDate = datetime.datetime.today() + datetime.timedelta(1)
    elif status == 'recover':
      # exclude recovered GPS tags
      pass
    elif status == 'extinct':
      # add three extra days to ensure all final transmits are found
      endDate = endDate + datetime.timedelta(3)

    # CSV-filename for this tag
    outFileName = outPath+'\\'+yr+'\\'+datadir+'\\CSV\\'+ptt+'.csv'
    seen = []

    if os.path.exists(outFileName):
      # 'active' and 'test' tags
      if not tag_src == 'new_csv':
        # find new start date and seen list
        startDate, seen = getSeen(outFileName, deploy)
        # append ptt.csv with any new rows
        print 'Appending: ' + ptt + '.csv'
        addRows(outFileName, startDate, endDate, ptt, seen)

      # *******Problem with new_csv = True
      else: # exists, but overwrite
        print 'Delete the old one first'
        pass
    else:# no outFileName, create new ptt.csv
      with open(outFileName, 'wb') as outFile:
        writer = csv.writer(outFile, delimiter=',', quoting=csv.QUOTE_ALL)
        writer.writerow(f_util.fieldLists.csv_header)
      # close outFile here, re-open to append ptt.csv with all founds rows
      addRows(outFileName, deploy, endDate, ptt, seen)
      # no changes to tagDict
  # end for
  return tagDict

if __name__ == '__main__':

    tag_src = '2019WA'
#    tag_src = (928,925)
    main(tag_src)


