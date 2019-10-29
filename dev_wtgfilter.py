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
land_cover = 'R:\\Data\\GIS_base\\Coast\\NA_full.shp'
rowList = []

#-------------------------------------------------------------------------------
def speedLogic(maxSpeed, rowCount):
    global rowList
    i = 0
    cnt = 0
    param = str(maxSpeed)+' km/hr'                                              # text for filtered rows
    try:
        while i < rowCount-4:                                                   # until final 4 locs
            end = 20 if rowCount-i > 19 else rowCount-i                         # define length of subset
            rowSet = [row for row in rowList[i:i+end] if row[5] == 'OK']        # subset 'OK' from rowList
            #del row
            if len(rowSet) <= 4:
                i+=1
                break
            rowA,rowB,rowC,rowD = rowSet[0:4]                                   # next four from 'OK' subset
            spdB = f_utils.getPath([rowA, rowB])['Speed']
            if spdB >= maxSpeed:                                                # speedAB>max, back up one
                if i > 0:                                                       # confirm 1st location > deploy
                    i-=1
                    if i < 0:
                        print 'SpeedLogic: Negative i on backup 1'
                        return(0)
                    continue    # re-filter from previous point

                elif i == 0:
                    flagger(rowB, 'speed', param)
                    cnt+=1
                    continue                                                    # re-run filter from deploy
            else:
                spdC = f_utils.getPath([rowB, rowC])['Speed']
                if spdC >= maxSpeed:
                    lcB = rowB[3] if rowB[3] > 1 else None
                    lcC = rowC[3] if rowC[3] > 1 else None
                    if (lcB and lcC) or (not lcB and not lcC):                  # either both or none are UHQ
                        distB = f_utils.getPath([rowA,rowB,rowD])['Dist']
                        distC = f_utils.getPath([rowA,rowC,rowD])['Dist']
                        if distB >= distC:
                            flagger(rowB, 'speed', param)
                            cnt+=1
                            continue
                        elif distB < distC:
                            flagger(rowC, 'speed', param)
                            cnt+=1
                    elif lcC and not lcB:
                        flagger(rowB, 'speed', param)
                        cnt+=1
                        continue
                    elif lcB and not lcC:
                        flagger(rowC, 'speed', param)
                        cnt+=1
                i+=1
        #While loop
        if i <= rowCount-3:                                                     # loop exited: process EOF
            rowSet = [row for row in rowList[i:rowCount] if row[5] == 'OK']     # not getting last record???
            if len(rowSet) < 3:
                i+=1
            else:
                rowA,rowB,rowC = rowSet[-3:]
                spdB = f_utils.getPath([rowA, rowB])['Speed']
                spdC = f_utils.getPath([rowA, rowC])['Speed']
                if max(spdB,spdC) >= maxSpeed:                                  # one or both fail
                    lcB = rowB[3] if rowB[3] > 1 else None
                    lcC = rowC[3] if rowC[3] > 1 else None
                    if (lcB and lcC) or (not lcB and not lcC):                  # both or neither are HQ
                        if spdB > maxSpeed:
                            flagger(rowB, 'speed', param)
                            cnt+=1
                        if spdC > maxSpeed:
                            flagger(rowC, 'speed', param)
                            cnt+=1
                    elif lcC and not lcB:
                        flagger(rowB, 'speed', param)
                        cnt+=1
                    elif lcB and not lcC:
                        flagger(rowC, 'speed', param)
                        cnt+=1
                i+=1
        if i == rowCount-3:
            rowSet = [row for row in rowList[i:rowCount] if row[5] == 'OK']
            if len(rowSet) < 2:
                i+=1
            else:
                rowA,rowB = rowSet[-2:]
                spdB = f_utils.getPath([rowA, rowB])['Speed']
                if spdB > maxSpeed:
                    flagger(rowB, 'speed', param)
                    cnt+=1
                i+=1
        if i <= rowCount-2: # last row =========Still missing high speeds on final pair=========
            i+=1
        else:
            return(cnt)

    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        print(msgs)

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        print(pymsg)
        print(msgs)


    return(cnt)
#-------------------------------------------------------------------------------
def dupe_pass(in_rows):
    import collections

    dupe = False
    # determine if any duplicate pass times
    dateList = [row[2] for row in in_rows]
    dupDate = [date for date, count in collections.Counter(dateList).items() if count > 1]
    dupeList = [row for row in in_rows if row[2] == dupDate]
    #del row
    if len(dupeList) > 1:
        dupe = True
        # keep higher quality one
        if dupeList[0][3] > dupeList[1][3]:
            flagger(dupeList[1], 'sat_dupe', '')
        elif dupeList[0][3] < dupeList[1][3]:
            flagger(dupeList[0], 'sat_dupe', '')
        else:
            dupe = False

    return(dupe)

#-------------------------------------------------------------------------------
def redundantLogic(redun, rowCount):
    global rowList
    i = 1
    cnt = 0
    param = str(redun/60)+' min.'
    try:
        while i < rowCount-1:
            endTime = rowList[i][2]+timedelta(seconds=redun+1)                  # window end-time
            end = 9 if rowCount-i > 8 else rowCount-i
            redunList = [row for row in rowList[i:i+end]
                         if row[2]<endTime
                            and row[5] == 'OK']
            if len(redunList) <= 1:
                i+=1                                                            # no matches within window
                continue
            elif len(redunList) > 1:                                            # make 2 new lists of matches according to LC
                HQ = [row for row in redunList if row[3]>0]
                LQ = [row for row in redunList if row[3]<1]
                if dupe_pass(LQ):                                               # trap duplicate pass times
                    i+=1
                    cnt+=1
                    continue
                if HQ: # >=1 HQ
                    if LQ: # >=1 LQ
                        for row in LQ:
                            flagger(row, 'redun', param)
                            i+=1
                            cnt+=1
                        continue
                    i+=1
                    continue
                i+=1
        #del row

    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        print(msgs)

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        print(pymsg)
        print(msgs)

    return(cnt)
#-------------------------------------------------------------------------------
def flagger(row, filt_name, filt_param):
    global rowList
    reset = ('OK', '')
    """ TODO: Flag 4 consecutive rows """

    # original row
    o_row = row[:5] + reset
    # filtered row
    f_row = row[:5] + (filt_name, filt_param)
    try:
        # find position of filtered row in rowList
        if rowList.index(o_row):
            index = rowList.index(o_row)
        else:
            arcpy.AddMessage('feature %s previously filtered' % o_row[2])
            return()
        # Replace row(tuple) in original rowList
        rowList[index] = f_row

    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        print(msgs)

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        print(pymsg)
        print(msgs)


    return()
#-------------------------------------------------------------------------------
def land_proxy(in_file):
    global rowList

    """ TODO: get NEAR() for land points to pass to ellipse code """

    # count points on land
    arcpy.SelectLayerByLocation_management(in_file,"INTERSECT", land_cover, None, "SUBSET_SELECTION")
    result = arcpy.GetCount_management(in_file)
    count_pts = int(result.getOutput(0))
    if count_pts > 0:
        sql_clause = (None, 'ORDER BY "feature_id" ASC')
        fields = ("feature_id", "ptt")
        landList = []
        # list of selected feature_id's
        with arcpy.da.SearchCursor(in_file, fields, None, sr, None, sql_clause) as sCur:
            landList = [row[0] for row in sCur]
        for row in rowList:
            if row[1] in landList:
                flagger(row, 'on_land', '')
    #else:
    #    count_pts = 0
    arcpy.SelectLayerByAttribute_management(in_file,'CLEAR_SELECTION')

    #del sCur
    return(count_pts)
#-------------------------------------------------------------------------------
def editFeature(in_file, logFile, filtList):
    strRem = ''
    try:
        if logFile=='true':
            # create/append log file
            strRem = ','.join(str(e[0]) for e in filtList)
            log_name = 'f'+in_file[1:]+'_log'
            where = '{0}({1})'.format('"feature_id" IN ', strRem)
            logFile = logFilter(in_file, log_name, where, filtList)

            # then delete filtered from in_file
            removed = [row[0] for row in filtList]
            with arcpy.da.UpdateCursor(in_file, "feature_id") as uCur:
                for row in uCur:
                    if row[0] in removed:
                        uCur.deleteRow()
        else:
            # add/update filter fields
            f_utils.addLogFields(in_file)
            logFields = ["feature_id","filtername","filterparam"]
            with arcpy.da.UpdateCursor(in_file, logFields) as uCur:
                for row in uCur:
                    rowD = [item for item in filtList if item[0] == row[0]]
                    if rowD: # rowD is a matrix [[12345,x,y]]
                        row[1:] = rowD[0][1:]
                    else:
                        row[1:] = ['OK', '']
                    uCur.updateRow(row)

    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        print(msgs)

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        print(pymsg)
        print(msgs)


    return()

#-------------------------------------------------------------------------------
def makeFeature(in_file, out_name, logFile, filtList):

    try:
        # Create new log file
        if logFile=='true':
            strRem = ','.join(str(e[0]) for e in filtList)                      # create csv string of fid's
            log_name = out_name+'_log'
            where = '{0}({1})'.format('"feature_id" IN ', strRem)
            logFile = logFilter(in_file, log_name, where, filtList)
            # Create new FC with 'OK' locations
            where = '{0}({1})'.format('"feature_id" NOT IN ',strRem)
            out_file = arcpy.Select_analysis(in_file, out_name, where)
        else:
            # Create new FC, add filter fields
            out_file = arcpy.Select_analysis(in_file, out_name)
            #out_file = arcpy.CopyFeatures_management(in_file, out_name)
            f_utils.addLogFields(out_file)
            logFields = ["feature_id","filtername","filterparam"]
            # Update filter fields
            with arcpy.da.UpdateCursor(out_file, logFields) as uCur:
                for row in uCur:
                    # find the matching feature_id in filtList
                    rowD = [item for item in filtList if item[0] == row[0]]
                    if rowD: # rowD => [[12345,x,y]]
                        row[1:] = rowD[0][1:]
                    else:
                        row[1:] = ['OK', '']
                    uCur.updateRow(row)

    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        print(msgs)

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        print(pymsg)
        print(msgs)

    return()
#-------------------------------------------------------------------------------
def logFilter(in_file, log_name, where, filtList):

    homeDir = env.workspace
    if not homeDir:
        homeDir = path.dirname(in_file)

    logFile = '\\'.join([homeDir, log_name])
    logFields = ["feature_id","filtername","filterparam"]
    try:    # create new file
        if not arcpy.Exists(logFile):
            logFile = arcpy.Select_analysis(in_file, log_name, where)
            # Add filter fields
            f_utils.addLogFields(logFile)
            # Update filter fields
            with arcpy.da.UpdateCursor(logFile, logFields) as uCur:
                 for row in uCur:  # match feature_id
                    # find the matching feature_id in filtList
                    rowD = [item for item in filtList if item[0] == row[0]]
                    if rowD: # rowD => [[12345,x,y]]
                        row[1:] = rowD[0][1:]
                    else:
                        row[1:] = ['OK', '']
                    uCur.updateRow(row)
        else:
            # Append existing logfile
            removed = [row[1] for row in filtList]
            # get fids from log_file
            with arcpy.da.SearchCursor(logFile, f_utils.fieldLists.pointFilter) as sCur:
                found = [row[1] for row in sCur if row[1] in removed]
            # build log rows from in_file and filtList
            addRows = []
            with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.pointFields) as sCur:
                for row in sCur:
                    if row[1] in removed:
                        if row[1] not in found:
                            # find fid in filtList
                            rowD = (item for item in filtList if item[1] == row[1]).next()
                            addRows.append(row + rowD[5:])
            with arcpy.da.InsertCursor(logFile, f_utils.fieldLists.pointFilter) as iCur:
                for row in addRows:
                    iCur.insertRow(row)

    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        print(msgs)

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        print(pymsg)
        print(msgs)

    return()
#-------------------------------------------------------------------------------
def main(in_file, maxSpeed, minRedun, land='true', logFile='false',
            newFile='true', explode='false'):

    from collections import OrderedDict
    global rowList
    multi = False
    speed = float(maxSpeed)
    strSpeed = maxSpeed.replace('.', '_')
    out_name = ''
    filtList = []
    filtMulti = []
    rowMulti = []

    # test for filterfields
    # if len(arcpy.ListFields(in_file, 'filtername')) > 0:

    try:
        sql_clause = (None, 'ORDER BY "ptt", "timevalue" ASC')
        with arcpy.da.SearchCursor(in_file,f_utils.fieldLists.filterFields,"",sr,False,sql_clause) as sCur:
            pttList = list(OrderedDict.fromkeys([row[4] for row in sCur]))
            multi = True if len(pttList) > 1 else False
            for ptt in pttList:
                sCur.reset()
#
#                if ptt <> 4177:
#                    continue
#
                # subset cursor to a list by ptt, append "clean" filter values
                for row in sCur:
                    if row[4] == ptt:
                # modify quality to <= -10 to trigger adhoc filter
                # ================================================
                        if row[3] < -9: # IE: worse than 'Z'
                            rowList.extend([row + ('adhoc', '<Add Reason>')])
                        else:
                            rowList.extend([row + ('OK', '')])
#                ALL ROWS rowList.extend([row + ('OK', '') for row in sCur if row[4] == ptt])
                rowCount = len(rowList)

#                if rowCount < 3:
#                    arcpy.AddMessage('Not enough passes to filter ' + str(ptt))
                    # clean out rowList
#                    del rowList[:]
#                    continue
#                else:
                arcpy.AddMessage('start filtering ' + str(ptt))
                code = '_' # for building out_name
                if land == 'true':
                    # subset selection by ptt
                    where = ''.join(['"ptt" = ', str(ptt)])
                    arcpy.SelectLayerByAttribute_management(in_file,'NEW_SELECTION', where)
                    cnt = land_proxy(in_file)
                    arcpy.AddMessage('%s locations on land' %cnt)
                    code = code+'L' if cnt else code

                if minRedun:
                    redun = int(minRedun)*60                                # int: seconds
                    cnt = redundantLogic(redun, rowCount)
                    arcpy.AddMessage('%s redundant locations' %cnt)
                    code = code+'R' if cnt else code
                # finally, speed
                cnt = speedLogic(speed, rowCount)
                arcpy.AddMessage('%s locations exceeded speed' %cnt)
                code = code+'S_'

                # output results
                out_name = ''.join(['f_', str(ptt).zfill(5), code, strSpeed])
                # subset list of filtered data
                filtered = [[row[1],row[5],row[6]] for row in rowList if row[5] != 'OK']
                #if len(filtList)==0:
                if len(filtered) == 0:
                    arcpy.AddMessage('PTT %s, No locations were filtered' % ptt)
                    del rowList[:]
                    del filtList[:]
# Still need to makeFeature if explode
                    continue
                filtList.extend(filtered)
                if multi:
                    if explode == 'true': # make indivdual files
                        arcpy.SelectLayerByAttribute_management(in_file,"NEW_SELECTION", where)
                        makeFeature(in_file, out_name, logFile, filtList)
                        arcpy.AddMessage('FeatureClass %s, created' %out_name)
                    else:   # continue thru pttList
                        rowMulti.extend(rowList)
                        filtMulti.extend(filtList)
                    del rowList [:]
                    del filtList [:]

        # continue ptt loop
        if multi:
            if explode == 'false':
        # ****** get actual name from input
                out_name = ''.join(['f_tags', code, str(maxSpeed)])
                rowList.extend(rowMulti)
                filtList.extend(filtMulti)

        if len(filtList) == 0:
            if len(filtMulti) == 0:
                arcpy.AddMessage('Nothing filtered...')
                #return()
        else:
            if newFile == 'true':
                makeFeature(in_file, out_name, logFile, filtList)
            else: # edit in_file
                editFeature(in_file, logFile, filtList)

    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        print(msgs)

    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        print(pymsg)
        print(msgs)

    finally:
        pass

    return(out_name)
#-------------------------------------------------------------------------------
if __name__ == '__main__':

    defaults_tuple = (
        ('in_file', 'C:\\CurrentProjects\\Hump18HI\\GIS\\Humps All 2018 Filter.gdb\\raw_1995HI'),
        ('maxSpeed', '14'),
        ('minRedun', '20'),
        ('land',   'true'),
        ('logFile','true'),
        ('newFile','true'),
        ('explode','false')
        )
#        ('in_file', 'raw_1995HI'),
#        false  true
    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)

"""
=========== To debug within ArcMap, defaults_tuple MUST match input exactly ========
"""

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