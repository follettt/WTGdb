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
def getTypeLists(types):

    # translate selected types into a useful list

    # types by names
    str_List = [k for k in f_utils.domDicts.typeDict.keys() if k not in types]
    # types by column numbers
    int_List = sorted([v for k,v in f_utils.domDicts.typeDict.items() if k not in types])

    return str_List, int_List

#-------------------------------------------------------------------------------
def filterType(in_file, filtList, type_List):

    try:
        # translate to output lists
        str_List, int_List = getTypeLists(type_List)
        arcpy.AddMessage('Beginning Type Filter, flagging '+  str(str_List))

        with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.filterType, "", sr) as sCur:
            for row in sCur:
                # clear dict
                rowDict = {}
                # list encounter types
                rowTypes = [i for i in range(3,9) if row[i] == 1]
                if len(rowTypes) == 1: # row is single type
                    if rowTypes[0] in int_List:
                        rowDict = {'fid': row[0], 'lc': row[2], 'fname':'Location Type', 'fparam':'Excluded: '+ str(str_List)[1:-1]}
                    else:
                        rowDict = {'fid': row[0], 'lc': row[2], 'fname':'OK', 'fparam':''}
                else: # row has multiple types
                    flags = [t for t in rowTypes if t in int_List]
                    if len(flags) == len(rowTypes):
                        rowDict = {'fid': row[0], 'lc': row[2], 'fname':'Location Type', 'fparam':'Excluded: '+ str(str_List)[1:-1]}
                    else:
                        rowDict = {'fid': row[0], 'lc': row[2], 'fname':'OK', 'fparam':''}
                filtList.append(rowDict)

    except Exception as e:
        print e.message
        arcpy.AddMessage(e.message)

    arcpy.AddMessage('Finished with Location Type Filter')

    return()

#-------------------------------------------------------------------------------
def main(in_file, type_List, newFields):

    # Init. list of filtered locs
    filtList = []

    # run filter logic
    if type_List != f_utils.filter_defaults.default_types:
        filterType(in_file, filtList, type_List)
        import f_Filters
        if newFields == 'true':
            out_file = f_Filters.filterOutputFields(in_file, filtList, '_T')
        else:
           out_file = f_Filters.filterOutputLog(in_file, filtList, '_T')
    else:
        arcpy.AddMessage('No features were removed for Location Type')

    #return(out_file)

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    defaults_tuple = (
        ('in_file', 'C:\\Users\\tomas.follett\\Documents\\CurrentProjects\\Calif 2014\\GIS\\Blue_SPOT5.gdb\\p_05644'),
        ('type_List', ["Tag Deployed", "Biopsy Sample", "Argos Pass"]),
        ('newFields', u'false')
        )
# [u"'Tag Deployed'", u"'Biopsy Sample'", u"'FastLoc GPS'"]
    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)

