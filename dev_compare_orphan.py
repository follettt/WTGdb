import datetime
import csv
import os
import dev_db_utils as dbutil
import dev_f_utils as util
#from collections import OrderedDict

#-------------------------------------------------------------------------------
outPath = os.path.abspath("R:\\Data\\Tag_Data\\")
outFile = ''
conn = dbutil.getDbConn('wtg_gdb')

"""
Go through daily files and compare to devices
"""

#==================================================================

def comparanator(orphan_file, yr):
    fmt = "%m/%d/%Y %H:%M:%S"
#    fmt = "%m/%d/%Y %H:%M" #:%S"
#    fmt = "%Y/%m/%d %H:%M:%S"
    ptt = 0
    with open(orphan_file) as Orphans:
        reader = csv.DictReader(Orphans)
        for row in reader:
            if int(row["Platform ID No."]) != ptt:
                ptt = int(row["Platform ID No."])
                tagDict = dbutil.getOrphanTags(conn, ptt)
                tags = sorted([tag for tag in tagDict.keys()], reverse=True)
            for tag in tags:
                data = tagDict[tag]
                if not data[2]:
                    continue
                if data[2].year > int(yr)-1: #stop_date

                    tx_time = util.str2Date(row["Msg Date"],fmt)
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
    return



#-------------------------------------------------------------------------------

def main():
    yr = '2019'
    orphan_file = ''.join(['R:\\Data\\Argos_Raw\\Data',yr,'\\Orphan_',yr,'.csv'])
    #orphan_file = 'R:\\Data\\Argos_Raw\\Data2019\\Orphan_2019.csv'
    comparanator(orphan_file, yr)

if __name__ == '__main__':


    main()
