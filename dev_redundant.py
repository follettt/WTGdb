# f_Filters.py
#-------------------------------------------------------------------------------
import arcpy
from arcpy import env
from os import path
import sys
import traceback

# local imports
import dev_f_utils

# Global vars
sr = arcpy.SpatialReference(4326)

#-------------------------------------------------------------------------------
def filterRedundant(in_file, filtList, minTime, mult_tool=False):
    from datetime import timedelta
    from collections import OrderedDict

    arcpy.AddMessage('Beginning Orbit Redundant filter')
    # convert string to integer seconds
    intTime = int(minTime)*60

# ****** NEW 2017 multiple ptt's
    sql_clause = (None, 'ORDER BY "ptt", "timevalue" ASC')
    c3 = ''#'"argospass" = 1'

    if mult_tool:
        # define where clause, in case any rows were already filtered
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
        removed = []
        with arcpy.da.SearchCursor(in_file, dev_f_utils.fieldLists.filterFields,
                                    where_clause, sr, False, sql_clause) as sCur:
            #step thru cursor and extract ptt's
            ptt_list = list(OrderedDict.fromkeys([int(row[4]) for row in sCur]))
            for ptt in ptt_list:
                print 'Curent ptt: '+str(ptt)
                # return to BOF
                sCur.reset()
                # port cursor to a list for current ptt
                cur1 = [row for row in sCur if row[4]==ptt]
                i = 0
                while i < len(cur1)-1:
                    # define time window end-time
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
            if mult_tool: # filtList is already populated
                for rowD in filtList:
                    if rowD['fid'] in removed:
                        # modify rows not already filtered
                        if rowD['fname'] == 'OK':
                            rowD['fname'] = 'Orbit Redundant'
                            rowD['fparam'] = '< '+minTime+' min.'
                   # else: already 'OK'
            else:
                with arcpy.da.SearchCursor(in_file, dev_f_utils.fieldLists.filterFields, "", sr) as sCur:
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

    # list of filtered locs from previous tool used in multi-tool env
    filtList = []
    #newFields='true'
#   examine gdb filter table for filtered features
##    db_filter = ''
##    where_clause = ''
##    sql_clause = ''
##    with arcpy.da.SearchCursor(db_filter, f_utils.fieldLists.filterFields,
##                                    where_clause, sr, False, sql_clause) as sCur:
##        pass

    if minTime > '0':
        filterRedundant(in_file, filtList, minTime)
        import dev_filters
        if newFields == 'true':
            out_file = dev_filters.filterOutputFields(in_file, filtList, '_R')
        else:
            out_file = dev_filters.filterOutputLog(in_file, filtList, '_R')
    else:
        arcpy.AddMessage('No features were removed for Orbit Redundant')

    arcpy.AddMessage('Finished with Location Type Filtering')

    return(out_file)


#-------------------------------------------------------------------------------
if __name__ == '__main__':

    defaults_tuple = (
        ('in_file', 'C:\\CurrentProjects\\Humps All\\GIS\\Hump15AK_new.gdb\\p_00827'),
        ('minTime', '20'),
        ('newFields', 'true')
        )

    defaults = dev_f_utils.parameters_from_args(defaults_tuple, sys.argv) # argv = name of file
    #main(mode='script', **defaults)
    main(**defaults)

