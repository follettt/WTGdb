#-------------------------------------------------------------------------------
# Name:        subset MK10 Depths.py
# Purpose:
#
# Author:      tomas.follett
#
# Created:      9/04/2013
# Updated:      4/02/2016
#-------------------------------------------------------------------------------
import csv, datetime, os
import wtg_utils as wtg
from os import path

def main(ptt, timeInc):

    inPath = "R:\\Data\\Tag_Data\\2015\\Jul_CA_Blue_Fin\\WC_Recovered\\838"
    inFile = inPath + "\\838-Archive.csv"
    outPath = inPath + "\\" + ptt + " Depth" + str(timeInc+1) + "s.csv"

    with open(outPath, 'ab') as outputFile:
        writer = csv.writer(outputFile, delimiter=',')
        a_fields = ['diveID',
                'ptt',
                'TimeValue',
                'FromLocation',
                'Depth',
                'Temp_Ext',
                'Temp_Int',
                'mX',
                'mY',
                'mZ',
                'aX',
                'aY',
                'aZ',
                'Light',
                #'mMag',
                #'mVer',
                #'mHor',
                #'mDip',
                #'Heading',
                #'Roll',
                #'Pitch',
                'Event']
        writer.writerow(a_fields)

        counter = 1

        with open(inFile, 'rb') as srcFile:
            # ***** Manually set end of file ****************
            i = 2440213
            srcDict = csv.DictReader(srcFile, fieldnames=None)
            while srcDict.line_num < i:
                for row in srcDict:
                    fromLoc = float(row["Date"])
                    timeVal = wtg.getDateFromSerial(fromLoc)
                    # subset logic
                    if timeVal.second in [0,15,30,45]:
                    #if timeVal.second == 0 or timeVal.second == 30:
                        if row["Depth"] <> '':
                            depth = int(float(row["Depth"])) * -1
                            writer.writerow([counter,
                                    ptt,
                                    timeVal,
                                    fromLoc,
                                    int(depth),
                                    row['External Temperature'],
                                    row['Depth Sensor Temperature'],
                                    row['int mX'],
                                    row['int mY'],
                                    row['int mZ'],
                                    row['int aX'],
                                    row['int aY'],
                                    row['int aZ'],
                                    row['Light Level'],
                                    #row['Magnetic Magnitude'],
                                    #row['Magnetic Vertical'],
                                    #row['Magnetic Horizontal'],
                                    #row['Magnetic Dip'],
                                    #row['Heading'],
                                    #row['Roll'],
                                    #row['Pitch'],
                                    row['Events']
                                    ])
                            counter +=1

        print "Done"

if __name__ == '__main__':

    ptt = "838"
    timeInc = 14    # 14 = 15s; 59 = 1 min; 299 = 5 min

    main(ptt, timeInc)
