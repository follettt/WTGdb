# f_Filters.py
#-------------------------------------------------------------------------------
import arcpy
from arcpy import env
from os import path
import sys
import traceback
from datetime import timedelta

# local imports
import dev_f_utils as f_utils

# Global vars
sr = arcpy.SpatialReference(4326)
i = 0
consecutive = 0
tail = 0

#-------------------------------------------------------------------------------
def speedLogic(rowList, maxSpeed):

    # index of current row in rowList
    global i, tail
    # text for flagger
    param = str(maxSpeed)+' km/hr'
    try:
        # choose length of subset
        if tail > 3:
            end = 20 if tail > 19 else tail
            # select next four rows not previously filtered
            rowSet = [row for row in rowList[i:i+end] if row[5] == 'OK']
            rowA,rowB,rowC,rowD = rowSet[0:4]
        elif tail == 3:
            rowA,rowB,rowC = rowList[i:i+3]
        elif tail == 2:
            rowA,rowB = rowList[i:i+2]
        else:
            return()

        # speed A-B
        spdB = f_utils.getPath([rowA, rowB])['Speed']
        if tail > 3: # Body of track
            # first segment exceeds speed
            if spdB >= maxSpeed:
                if i > 0:
                    # decrement i to re-filter from here
                    i-=1
                    tail +=1
                    return()
                # trap if 1st argos location
                elif i == 0:
                    flagger(rowList, i, 'speed', param)
                    return() # no increment

            # speed B-C
            spdC = f_utils.getPath([rowB, rowC])['Speed']
            if spdC >= maxSpeed:
                lcB = rowB[3] if rowB[3] > 1 else None
                lcC = rowC[3] if rowC[3] > 1 else None
                # either both or neither are UHQ
                if (lcB and lcC) or (not lcB and not lcC):
                    distB = f_utils.getPath([rowA,rowB,rowD])['Dist']
                    distC = f_utils.getPath([rowA,rowC,rowD])['Dist']
                    if distB >= distC:
                        flagger(rowList,rowList.index(rowB), 'speed', param)
                        return() # no increment
                    elif distB < distC:
                        flagger(rowList, rowList.index(rowC), 'speed', param)
                elif lcC and not lcB:
                    flagger(rowList, rowList.index(rowB), 'speed', param)
                    return() # no increment
                elif lcB and not lcC:
                    flagger(rowList, rowList.index(rowC), 'speed', param)

        elif tail == 3: # final three
            # speed A-C
            spdC = f_utils.getPath([rowA, rowC])['Speed']
            if max(spdB,spdC) >= maxSpeed:
                lcB = rowB[3] if rowB[3] > 1 else None
                lcC = rowC[3] if rowC[3] > 1 else None
                if (lcB and lcC) or (not lcB and not lcC):
                    if spdB > maxSpeed:
                        flagger(rowList, rowList.index(rowB), 'speed', param)
                        return() # no increment
                    if spdC > maxSpeed:
                        flagger(rowList, rowList.index(rowC), 'speed', param)
                elif lcC and not lcB:
                    flagger(rowList, rowList.index(rowB), 'speed', param)
                    return() # no increment
                elif lcB and not lcC:
                    flagger(rowList, rowList.index(rowC), 'speed', param)
        elif tail == 2:# EOF
            if spdB > maxSpeed:
                flagger(rowList, rowList.index(rowB), 'speed', param)
                return() # no increment

        # increment index
        i+=1
        tail-=1

    except Exception as e:
        print e.message
        arcpy.AddMessage(e.message)

    return()
#-------------------------------------------------------------------------------
def redundantLogic(rowList, redun):

    global tail
    # define time window end-time
    endTime = rowList[i][2]+timedelta(seconds=redun+1)
    # define length of subset
    end = 9 if tail > 8 else tail
    # new list of rows within time window, including current row
    redunList = [row for row in rowList[i:i+end]
                    if row[2]<endTime
                    and row[5] == 'OK']

    if len(redunList) > 1:
        # make 2 new lists of matches according to LC
        HQ = [row for row in redunList if row[3]>0]
        LQ = [row for row in redunList if row[3]<1]
        del row
        if HQ: # one or more High Quality
           if LQ: # flag all Low Quality from rowList
                for row in LQ:
                    flagger(rowList, rowList.index(row), 'redun', str(redun)+' min.')
    return()

#-------------------------------------------------------------------------------
def flagger(rowList, index, filt_name, filt_param):

    print ''.join(['i = ', str(index), ' - ', filt_name])
    # append filter info to tuple
    row = rowList[index][:5] + (filt_name, filt_param)
    # Replace row(tuple) in original rowList
    rowList[index] = row

    return()

#-------------------------------------------------------------------------------


#-------------------------------------------------------------------------------
def run_filters(in_file, filtList, maxSpeed, minRedun):

    from collections import OrderedDict
    global i, tail
    removed = []
    speed = float(maxSpeed)     # convert text speed to float
    redun = int(minRedun)*60    # integer seconds
    try:
        sql_clause = (None, 'ORDER BY "timevalue" ASC')
        with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.filterFields,
                                    "", sr, False, sql_clause) as sCur:
            #step thru cursor and extract ptt's
            pttList = list(OrderedDict.fromkeys([row[4] for row in sCur]))
            # loop through tags
            for ptt in pttList:
                sCur.reset()
                if ptt <> 5838:
                    continue
                # subset cursor to list by ptt, adding filter fields
                rowList = [row + ('OK', '') for row in sCur if row[4] == ptt]
                del row
                # manage EOF
                tail = len(rowList)-4
                # begin looping thru rows
                while i < len(rowList)-4:
                    redundantLogic(rowList, redun)
                    speedLogic(rowList, speed)

                # reset globals
                i=0
                consecutive=0

##        count = len(removed)
##
##        if count > 0:
##            with arcpy.da.SearchCursor(in_file, dev_f_utils.fieldLists.filterFields,
##                                        "", sr) as sCur:
##                for row in sCur:
##                    rowDict = {}
##                    if row[1] in removed:
##                        rowDict = {'fid': row[1],
##                                    'fname':'Maximum Speed',
##                                    'fparam': '> '+maxSpeed+' km/hr'
##                                    }
##                    else:
##        # Build a replacement row
##                        rowDict = {'fid': row[1], 'fname':'OK', 'fparam':''}
##                    filtList.append(rowDict)
##
##        else:
##            arcpy.AddMessage('No passes exceeded ' +maxSpeed+' km/hr')

    except Exception as e:
        print e.message
        arcpy.AddMessage(e.message)

    return()



#-------------------------------------------------------------------------------
def main(in_file, maxSpeed, minRedun):

    # list of filtered locs from each tool
    filtList = []
    run_filters(in_file, filtList, maxSpeed, minRedun)

    #out_file = f_Filters.filterOutputFields(in_file, filtList, '_S')
    #
    # Write details to filter table, reference filter_id in argos
    #

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    defaults_tuple = (
        ('in_file', 'C:\\CurrentProjects\\Hump18WA\\GIS\\2018WA_2.gdb\\raw_2018WA'),
        ('minRedun', '20'),
        ('maxSpeed', '14'),
        )

    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)

##def remover(removed, featID):
##    # called from speedLogic()
##    global consecutive
##
##    if len(removed) > 0:
##        if featID-1 == removed[-1]:
##            consecutive+=1
##        else:
##            consecutive = 0
##        if consecutive > 3:
##            arcpy.AddWarning('WARNING! 4 consecutive points were flagged: '+ str(removed[-5:-1]))
##    removed.append(featID)
##
##    return()