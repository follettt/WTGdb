# MakePath.py

import arcpy
from arcpy import env
from os import path
import sys
import traceback
from Vincenty import calcVincentyInverse

# local imports
import f_utils

# Global vars
sr = arcpy.SpatialReference(4326)
env.overwriteOutput = True

def main(in_file):
    # Script: input = full path to GDB
    homeDir = path.dirname(in_file)
    if not homeDir:
        # Toolbox: input = layer name only
        homeDir = env.workspace
        in_name = in_file
    else:
        in_name = path.basename(in_file)
    out_name = 'tr'+in_name[1:]
    if arcpy.Exists(out_name):
        out_name = f_utils.uniqName(out_name)
    temp_name = path.basename(out_name)

    template = ""
    has_m = 'DISABLED' #'ENABLED'
    has_z = 'DISABLED'
    geometry_type = 'POLYLINE'

    try:
        # pass in the name only
        line_FC = arcpy.CreateFeatureclass_management('in_memory', temp_name,
                geometry_type, template, has_m, has_z, sr)
        # template doesn't work? Field list for insert cursor
        f_names = []
        # First add shape
        f_names.append("SHAPE@")
        # add fields from library
        for f_name, f_type in f_utils.fieldLists.pathCols:
            arcpy.AddField_management(line_FC, f_name, f_type)
            f_names.append(f_name)
        # open an insert cursor on in_memory\FC
        with arcpy.da.InsertCursor(line_FC, f_names) as iCur:
            # open a search cursor on input layer
            sqlClause = (None, 'ORDER BY "individual", "timevalue"')
            with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.pathSource,
                                        None, sr, False, sql_clause=sqlClause) as sCur:
                points = arcpy.Array()
                 # get first row
                row = sCur.next()
                # store deploy values
                from_id, from_date, from_loc, indID, devID, ptt = row[1:7]
                # add first point to array
                points.add(arcpy.Point(*row[0]))
                # iterate over remaining rows
                for row in sCur:
                # trap for grouped tags
                    if row[4] <> indID:
                        # store deploy values
                        from_id, from_date, from_loc, indID, devID, ptt = row[1:7]
                        # flush array
                        points = arcpy.Array()
                        # add first point to new array
                        points.add(arcpy.Point(*row[0]))
                        continue
                    # add next point
                    points.add(arcpy.Point(*row[0]))
                    # construct a path using the two points in the array
                    segment = arcpy.Polyline(points, sr, False, False)
                    # update values for new row
                    to_id, to_date, to_loc = row[1:4]
                    dist = calcVincentyInverse(points[0].Y,points[0].X,points[1].Y,points[1].X)[0]/1000.0
                    delta = to_date - from_date
                    # convert to hours
                    elapsed = (delta.days*24)+(delta.seconds/3600.0)
                    # trap for indentical timevals
                    if elapsed <= 0:
                        elapsed = 0.01666667
                    speed = dist/elapsed # speed = dist/elapsed if elapsed > 0 else 0.0
                    # add path to feature class
                    iCur.insertRow([segment, from_id, to_id,
                                            from_date, to_date, from_loc, to_loc,
                                            indID, devID, ptt, dist, elapsed, speed])
                    # remove "from" point
                    points.remove(0)
                    from_id   = to_id
                    from_date = to_date
                    from_loc  = to_loc

     # Return geoprocessing specific errors
    except arcpy.ExecuteError:
        msgs = arcpy.GetMessages(2)
        arcpy.AddError(msgs)
        print msgs
    except:
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        # Concatenate information together concerning the error into a message string
        pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
        msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        # Return python error messages for use in script tool or Python Window
        arcpy.AddError(pymsg)
        arcpy.AddError(msgs)
        # Print Python error messages for use in Python / Python Window
        print pymsg + "\n"
        print msgs
    finally:
        arcpy.AddMessage('Finished with Path Creation')

    # persist to gdb
    out_file = arcpy.CopyFeatures_management(line_FC, out_name)
    return(out_file)

if __name__ == '__main__':

    defaults_tuple = (
        ('in_file', 'C:\\Users\\tomas.follett\\Documents\\CurrentProjects\\Calif 2014\\GIS\\Blue_2014.gdb\\p_10827')
        )
    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)


                   # trap crossing dateline
##                    if row[0][0] < 0: # cast longitude to 0-360
##                        fixLong = 360 + row[0][0]
##                        points.add(arcpy.Point(fixLong, row[0][1]))
##                    else:
