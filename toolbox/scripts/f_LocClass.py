#-------------------------------------------------------------------------------
# f_LCFilter.py
#-------------------------------------------------------------------------------
import arcpy
from arcpy import env

# local imports
import f_utils

# Global vars
sr = arcpy.SpatialReference(4326)
env.overwriteOutput = True

#-------------------------------------------------------------------------------
def getLcLists(classes):

    str_List = [k for k in f_utils.domDicts.lcDict.keys() if k not in classes]
    int_List = sorted([v for k,v in f_utils.domDicts.lcDict.items() if k not in classes])
    return str_List, int_List

#-------------------------------------------------------------------------------
def filterLC(in_file, filtList, lc_List, multi=False):

    # Filter LC by items NOT selected by user within the tool

    # translate to output lists
    str_List, int_List = getLcLists(lc_List)
    arcpy.AddMessage('Beginning LC Filter, flagging '+ str(str_List))

    try:
        if multi: # filtList is already populated
            for rowD in filtList:
                if rowD['lc'] in int_List:
                    # modify rows not already filtered
                    if rowD['fname'] == 'OK':
                        rowD['fname'] = 'Location Class'
                        rowD['fparam'] = 'Excluded: '+str(str_List)[1:-1]

        else:
            with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.filterFields, "", sr) as sCur:
                for row in sCur:
                    # clear dict
                    rowDict = {}
                    if row[1] in int_List:
                        rowDict = {'fid': row[1],
                                    'lc': row[3],
                                    'fname':'Location Class',
                                    'fparam': 'Excluded: '+str(str_List)[1:-1]}
                    else:
                        rowDict = {'fid': row[1], 'fname':'OK', 'fparam':''}
                    filtList.append(rowDict)

    except Exception as e:
        print e.message
        arcpy.AddMessage(e.message)

    arcpy.AddMessage('Finished with Location Class Filter')
    return()

#-------------------------------------------------------------------------------
def main(in_file, lc_List, newFields):

    # Init. list of filtered locs
    filtList = []

    # run filter logic
    if lc_list != f_utils.filter_defaults.default_class:
        if lc_list != None:
            filterLC(in_file, filtList, lc_List, newFields)
            import f_Filters
            if newFields == 'true':
                out_file = f_Filters.filterOutputFields(in_file, filtList, '_L')
            else:
                out_file = f_Filters.filterOutputLog(in_file, filtList, '_L')
    else:
        arcpy.AddMessage('No features were removed for Location Class')

    return(out_file)

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    defaults_tuple = (
        ('in_file', 'C:\\Users\\tomas.follett\\Documents\\CurrentProjects\\Calif 2014\\GIS\\Blue_SPOT5.gdb\\p_05644'),
        ('lc_List', ["3","2","1","0","A","B2","B1"]),
        ('newFields', 'true')
        )

    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)

