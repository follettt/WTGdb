# f_Filters.py
#-------------------------------------------------------------------------------
import arcpy
from arcpy import env
from os import path
import sys
import traceback

# local imports
import f_utils

# Global vars
sr = arcpy.SpatialReference(4326)
i = 0
consecutive = 0


#-------------------------------------------------------------------------------
def speedLogic(cur1, removed, last, maxSpeed):
    # called from filterSpeed()
    global i
    # Vincenty Ellipsoid implemented 2/25/15

    try:
        # End of track
        if last:
            tail = len(cur1)-i
            if tail==1:
                pass
            elif tail==2:
                rowA,rowB = cur1[i:i+tail]
                spdB = f_utils.getVincentyPath([rowA, rowB])['Speed']
                if spdB > maxSpeed:
                    del cur1[i+1]
                    remover(removed,rowB[1])
                    return()
            elif tail==3:
                rowA,rowB,rowC = cur1[i:i+tail]
                spdB = f_utils.getVincentyPath([rowA, rowB])['Speed']
                spdC = f_utils.getVincentyPath([rowA, rowC])['Speed']
                if max(spdB,spdC) >= maxSpeed:
                    lcB = rowB[3] if rowB[3] > 1 else None
                    lcC = rowC[3] if rowC[3] > 1 else None
                    if (lcB and lcC) or (not lcB and not lcC):
                        if spdB > maxSpeed:
                            del cur1[i+1] # rowB
                            remover(removed,rowB[1])
                            return()
                        if spdC > maxSpeed:
                            del cur1[i+2] # rowC
                            remover(removed,rowC[1])
                    elif lcC and not lcB:
                        del cur1[i+1] # rowB
                        remover(removed,rowB[1])
                        return()
                    elif lcB and not lcC:
                        del cur1[i+2] # rowC
                        remover(removed,rowC[1])
        # Body of track
        else: # get the next four rows
            rowA,rowB,rowC,rowD = cur1[i:i+4]
            spdB = f_utils.getVincentyPath([rowA, rowB])['Speed']
            spdC = f_utils.getVincentyPath([rowB, rowC])['Speed']
            if spdB >= maxSpeed:
                # first post-deploy location bad?
                if i == 0:
                    del cur1[i+1] # rowB
                    remover(removed,rowB[1])
                    # don't advance i
                    return()
                # all other locations
                elif i > 0:
                    # back up one and refilter
                    i-=1
                    return()
            if spdC >= maxSpeed:
                lcB = rowB[3] if rowB[3] > 1 else None
                lcC = rowC[3] if rowC[3] > 1 else None
                # both, or neither UHQ
                if (lcB and lcC) or (not lcB and not lcC):
                    # compute distances
                    distB = f_utils.getVincentyPath([rowA,rowB,rowD])['Dist']
                    distC = f_utils.getVincentyPath([rowA,rowC,rowD])['Dist']
                    if distB >= distC:
                        del cur1[i+1] # rowB
                        remover(removed,rowB[1])
                        # don't advance i
                        return()
                    elif distB < distC:
                        del cur1[i+2] # rowC
                        remover(removed,rowC[1])
                elif lcC and not lcB:
                    del cur1[i+1] # rowB
                    remover(removed,rowB[1])
                    # don't advance i
                    return()
                elif lcB and not lcC:
                    del cur1[i+2] # rowC
                    remover(removed,rowC[1])
        i+=1

    except Exception as e:
        print e.message
        arcpy.AddMessage(e.message)

    return()
#-------------------------------------------------------------------------------
def remover(removed, featID):
    # called from speedLogic()
    global consecutive

    if len(removed) > 0:
        if featID-1 == removed[-1]:
            consecutive+=1
        else:
            consecutive = 0
        if consecutive > 3:
            arcpy.AddWarning('WARNING! 4 consecutive points were flagged: '+ str(removed[-5:-1]))
    removed.append(featID)

    return()

#-------------------------------------------------------------------------------
def filterSpeed(in_file, filtList, maxSpeed, multi=False):

    global i
    last = False
    removed = []
    count = 0
    # convert text speed to float
    speed = float(maxSpeed)
    arcpy.AddMessage('Starting f_Speed')
    try:
        sql_clause = (None, 'ORDER BY "timevalue" ASC')
        with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.filterFields,
                                    "", sr, False, sql_clause) as sCur:
            # port cursor to list
            cur1 = [row for row in sCur]
        del sCur
        # rows until final three
        while i < len(cur1)-4:
           speedLogic(cur1, removed, last, speed)
        # last rows, 3 or less
        last = True
        while i < len(cur1):
            speedLogic(cur1, removed, last, speed)
        # reset globals
        i=0
        consecutive=0

        count = len(removed)
        if count > 0:
            if multi:
                # run as part of f_Filters
                for rowD in filtList:
                    if rowD['fid'] in removed:
                        # modify rows not already filtered
                        if rowD['fname'] == 'OK':
                            rowD['fname'] = 'Maximum Speed'
                            rowD['fparam'] = '> '+maxSpeed+' km/hr'
                   # else: already 'OK'
            else:
                # run as single tool
                with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.filterFields,
                                            "", sr) as sCur:
                    for row in sCur:
                        rowDict = {}
                        if row[1] in removed:
                            rowDict = {'fid': row[1],
                                        'fname':'Maximum Speed',
                                        'fparam': '> '+maxSpeed+' km/hr'
                                        }
                        else:
                            rowDict = {'fid': row[1], 'fname':'OK', 'fparam':''}
                        filtList.append(rowDict)

        else:
            arcpy.AddMessage('No passes exceeded ' +maxSpeed+' km/hr')

    except Exception as e:
        print e.message
        arcpy.AddMessage(e.message)

    arcpy.AddMessage('Finished with f_Speed')
    return()

#-------------------------------------------------------------------------------
def main(in_file, maxSpeed, newFields):

    # list of filtered locs from each tool
    filtList = []

    if maxSpeed > '0':
        filterSpeed(in_file, filtList, maxSpeed)
        import f_Filters
        if newFields == 'true':
            out_file = f_Filters.filterOutputFields(in_file, filtList, '_S')
        else:
            out_file = f_Filters.filterOutputLog(in_file, filtList, '_S')
    else:
        arcpy.AddMessage('Max speed not selected')

    return(out_file)

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    defaults_tuple = (
        ('in_file', 'C:\\Users\\tomas.follett\\Documents\\CurrentProjects\\Calif 2015\\GIS\\Blue 2015.gdb\\p_00825'),
        ('maxSpeed', u'12'),
        ('newFields', u'true')
        )

    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)

