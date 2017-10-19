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

#-------------------------------------------------------------------------------
def filterRedundant(in_file, filtList, minTime, multi=False):
    from datetime import timedelta

    arcpy.AddMessage('Beginning Orbit Redundant filter')
    # convert string to integer seconds
    intTime = int(minTime)*60

    sql_clause = (None, 'ORDER BY "timevalue" ASC')
    c3 = '"argospass" = 1'
    if multi:
        # define where clause, if any rows were already filtered
        flagged = sorted([f['fid'] for f in filtList if f['fname'] != 'OK'])
        if len(flagged) >0:
            c1 = '"featureid" NOT IN '
            if len(flagged) ==1:
                c2 = '('+str(flagged[0])+')'
            else:
                c2 = str(tuple(flagged))
            where_clause = "{0}{1} AND {2}".format(c1,c2,c3)
        else:
            where_clause = c3
    else:
        where_clause = c3

    try:
        with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.filterFields,
                                    where_clause, sr, False, sql_clause) as sCur:
            # port to a list
            cur1 = [row for row in sCur]
        del sCur
        i = 0
        removed = []
        while i < len(cur1)-1:
            # set time window end-time
            endTime = cur1[i][2]+timedelta(seconds=intTime+1)
            # new list of rows within window, including current row
            cur2 = [row for row in cur1[i:i+10] if row[2]<endTime]
            if len(cur2) == 1:
            # no matches within window
                i+=1
                continue
            else: # 1+ matches within window
                # make 2 lists of matches, by LC
                HQ = [row for row in cur2 if row[3]>0]
                LQ = [row for row in cur2 if row[3]<1]
                if HQ: # one or more High Quality
                   if LQ:
                        # remove all Low Quality from cur1
                        for row in LQ:
                            cur1.remove(row)
                            removed.append(row[1])
                        # go back and re-run current row
                        continue
                # continue with next row
                i+=1
                del row

        if len(removed) > 0:
            if multi: # filtList is already populated
                for rowD in filtList:
                    if rowD['fid'] in removed:
                        # modify rows not already filtered
                        if rowD['fname'] == 'OK':
                            rowD['fname'] = 'Orbit Redundant'
                            rowD['fparam'] = '< '+minTime+' min.'
                   # else: already 'OK'
            else:
                with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.filterFields, "", sr) as sCur:
                    for row in sCur:
                        rowDict = {}
                        if row[1] in removed:
                            rowDict = {'fid': row[1],
                                        'fname':'Orbit Redundant',
                                        'fparam': '< '+minTime+' min.'}
                        else:
                            rowDict = {'fid': row[1], 'fname':'OK', 'fparam':''}
                        filtList.append(rowDict)

        else:
            arcpy.AddMessage('No Orbit Redundant passes detected')

    except Exception as e:
        print e.message
        arcpy.AddMessage(e.message)

    arcpy.AddMessage('Finished with Orbit Redundant')

    return(filtList)

#-------------------------------------------------------------------------------
def main(in_file, minTime, newFields):

    # list of filtered locs from each tool
    filtList = []

    if minTime > '0':
        filterRedundant(in_file, filtList, minTime)
        import f_Filters
        if newFields == 'true':
            out_file = f_Filters.filterOutputFields(in_file, filtList, '_R')
        else:
            out_file = f_Filters.filterOutputLog(in_file, filtList, '_R')
    else:
        arcpy.AddMessage('No features were removed for Orbit Redundant')

    arcpy.AddMessage('Finished with Location Type Filtering')
    return(out_file)

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    defaults_tuple = (
        ('in_file', 'C:\\Users\\tomas.follett\\Documents\\CurrentProjects\\WTG_Local.gdb\\p_05644'),
        ('minTime', '20'),
        ('newFields', 'true')
        )

    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)

