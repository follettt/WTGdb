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

def filterOutputFields(in_file, filtList, fExt):

    homeDir = path.dirname(in_file) # GDB FC input
    if not homeDir:
        homeDir = env.workspace     # Map Layer input
    out_name = in_file+fExt
    if arcpy.Exists(out_name):
        out_name = f_utils.uniqName(out_name)
    out_name = path.basename(out_name)

    try:
        # create new FC
        # Use these if running from python!!
##        out_full = homeDir+'\\'+out_name
##        out_file = arcpy.Select_analysis(in_file, out_full)
        out_file = arcpy.Select_analysis(in_file, out_name)
        # Add new filter columns to in_file
        f_utils.addLogFields(out_file)
        # Write results to new FC
        with arcpy.da.UpdateCursor(out_file, f_utils.fieldLists.logFields) as uCur:
             for row in uCur:
                # inline for each featureID that is in
                rowD = (item for item in filtList if item['fid'] == row[0]).next()
                row[20] = rowD['fname']
                row[21] = rowD['fparam']
                uCur.updateRow(row)


    except arcpy.ExecuteError:
        # Get the tool error messages
        msgs = arcpy.GetMessages(2)
        # Return tool error messages for use with a script tool
        arcpy.AddError(msgs)
        # Print tool error messages for use in Python/PythonWin
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


    return(out_file)

# ---------------------------------------------------------------------------

def filterOutputLog(in_file, filtList, fExt):

    homeDir = path.dirname(in_file) # GDB FC input
    if not homeDir:
        homeDir = env.workspace     # Map Layer input
    out_name = in_file+fExt
    if arcpy.Exists(out_name):
        out_name = f_utils.uniqName(out_name)
    # this will cause the Select to fail when run from python!!
    out_name = path.basename(out_name)
    logName = out_name+'_log'

    removed = sorted([f['fid'] for f in filtList if f['fname'] != 'OK'])
    try:
        # define SQL for Select
        if len(removed) <1:
            arcpy.AddMessage('Nothing removed, exiting f_Filters')
            return()
        elif len(removed) >1:
            where = '"featureid" NOT IN ' + str(tuple(removed))
            log_clause = '"featureid" IN ' + str(tuple(removed))
        elif len(removed) ==1:
            where = '"featureid" NOT IN (' + str(removed[0])+ ')'
            log_clause = '"featureid" IN (' + str(removed[0])+ ')'

        # Create new FC with good locations
        out_file = arcpy.Select_analysis(in_file, out_name, where)

        # Create new log file with input as template
        logFile = arcpy.Select_analysis(in_file, logName, log_clause)
        # Add filter fields
        f_utils.addLogFields(logFile)

        # Write deletions to Log
        with arcpy.da.UpdateCursor(logFile, f_utils.fieldLists.logFields) as uCur:
             for row in uCur:
                rowD = (item for item in filtList if item['fid'] == row[0]).next()
                row[20] = rowD['fname']
                row[21] = rowD['fparam']
                uCur.updateRow(row)

        arcpy.AddMessage('A total of '+str(len(removed))+' features were removed')

    except arcpy.ExecuteError:
        # Get the tool error messages
        msgs = arcpy.GetMessages(2)
        # Return tool error messages for use with a script tool
        arcpy.AddError(msgs)
        # Print tool error messages for use in Python/PythonWin
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

    return(out_file)
#-------------------------------------------------------------------------------
def pop_filtList(in_file, filtList):
    # if filtList doesn't get filled by one of the filters, do it here
    try:
        with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.filterType, "", sr) as sCur:
            for row in sCur:
                rowDict = {'fid': row[0], 'lc': row[2], 'fname':'OK', 'fparam':''}
                filtList.append(rowDict)
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        print(pymsg)
        print(msgs)

#-------------------------------------------------------------------------------
def main(in_file, newFields, type_list=None, lc_list=None, minTime=None, maxSpeed=None):

    multi = False
    filtList = []
    fExt = '_'

    # run selected filters, populating and/or modifying [filtList] with each filter
    # These take the place of the main() in each filter
    # **********************************************************
    if type_list != f_utils.filter_defaults.default_types:
        if type_list != None:
            arcpy.AddMessage('Type Filter invoked with '+ str(type_list))
            import f_LocType
            result = f_LocType.filterType(in_file, filtList, type_list)
            fExt = fExt+'T'
            if not multi: multi = True

    if lc_list != f_utils.filter_defaults.default_class:
        if lc_list != None:
            if len(filtList) == 0:
                pop_filtList(in_file, filtList)
            arcpy.AddMessage('Class Filter invoked with '+ str(lc_list))
            import f_LocClass
            result = f_LocClass.filterLC(in_file, filtList, lc_list, multi)
            fExt = fExt+'L'
            if not multi: multi = True

    if minTime > '0':
        if len(filtList) == 0:
            pop_filtList(in_file, filtList)
        arcpy.AddMessage('Redundancy filter invoked with '+ minTime+ 'min')
        import f_Redundant
        result = f_Redundant.filterRedundant(in_file, filtList, minTime, multi)
        fExt = fExt+'R'
        if not multi: multi = True

    if maxSpeed > '0':
        if len(filtList) == 0:
            pop_filtList(in_file, filtList)
        arcpy.AddMessage('Speed filter invoked with '+ maxSpeed+ 'km/hr')
        import f_Speed
        result = f_Speed.filterSpeed(in_file, filtList, maxSpeed, multi)
        fExt = fExt+'S'

    if len(filtList) > 0: # if not log file, will never be 0!
        if newFields == 'true':
            out_file = filterOutputFields(in_file, filtList, fExt)
        else:
            out_file = filterOutputLog(in_file, filtList, fExt)
    else:
        arcpy.AddMessage('No features were removed')
        arcpy.AddMessage('Finished with all filters')
        sys.exit()

    return(out_file)

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    defaults_tuple = (
        ('in_file', 'C:\\Users\\tomas.follett\\Documents\\CurrentProjects\\Calif 2015\\GIS\\Blue 2015.gdb\\p_05640'),
        ('newFields', u'false'),
        ('type_list', ["Tag Deployed", "Biopsy Sample", "Argos Pass"]),
        ('lc_list', ["G","3","2","1","0","A","B2","B1"]),
        ('minTime', '20'),
        ('maxSpeed', '12')
        )
#,"B1" "Biopsy Sample",
    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)

