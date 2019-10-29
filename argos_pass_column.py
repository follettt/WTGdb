


import csv
import datetime
from os import path

# local modules
import dev_tables as tables
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

def main(inFileName):
    csvName = path.basename(inFileName)
    with open(inFileName, 'rb') as inFile:
        count = sum(1 for line in inFile)
        inFile.seek(0)  # reset file
        reader = csv.DictReader(inFile)
        while reader.line_num < count:
            pttList = sorted(list(set(int(r['ptt']) for r in reader)))
            ptt - pttList[0]
            for row in reader:
                if int(row['ptt']) != ptt:  # start new ptt
                    ptt = int(row['ptt'])
                    str_passtime = row['hdatetime']
                    passvalue = format_date(str_timeval,bd)
                    str_msgtime = row['ldatetime']
                    first_msg = format_date(row['ldatetime'],bd)









if __name__ == '__main__':

    inFileName = '\\'.join([INPATH,'Argos_Raw','Archive','Argos-Marmam1993CA.csv'])
    if path.exists(inFileName):
        main(inFileName)
