# MakePath.py
"""
TODO: add output track name as a param
"""
import arcpy
from arcpy import env
from os import path
import sys
import traceback
from Vincenty import calcVincentyInverse as v_dist
from datetime import timedelta
#import numpy
from numpy import sign

# local imports
import dev_f_utils as f_utils

# Global vars
sr = arcpy.SpatialReference(4326)
env.overwriteOutput = True

#-------------------------------------------------------------------------------
def calcSegment(points, delta):

    segment = arcpy.Polyline(points, sr, False, False)
    dist = v_dist(points[0].Y,points[0].X,points[1].Y,points[1].X)[0]/1000.0
    elapsed = (delta.days*24)+(delta.seconds/3600.0)    # convert to hours
    if elapsed <= 0:                                    # trap identical timevalues
        elapsed = 0.01666667
    speed = dist/elapsed

    return(segment,dist,elapsed,speed)


#-------------------------------------------------------------------------------
def main(in_file):

    homeDir = path.dirname(in_file) # Script: input = full path to GDB
    if not homeDir:
        homeDir = env.workspace     # Toolbox: input = layer name only
        in_name = in_file
    else:
        in_name = path.basename(in_file)
    out_name = 'tr'+in_name[1:]
    if arcpy.Exists(out_name):
        out_name = f_utils.uniqName(out_name)
    temp_name = path.basename(out_name)

    try:
        # pass in the name only
        line_FC = arcpy.CreateFeatureclass_management('in_memory', temp_name,
                'POLYLINE', '', 'DISABLED', 'DISABLED', sr)
        f_names = []                                                # Field list for insert cursor
        f_names.append("SHAPE@")                                    # First add shape
        for f_name, f_type in f_utils.fieldLists.routeCols:         # add fields
            arcpy.AddField_management(line_FC, f_name, f_type)
            f_names.append(f_name)
        # open an insert cursor on the in_memory\FC
        with arcpy.da.InsertCursor(line_FC, f_names) as iCur:
            sqlClause = (None, 'ORDER BY "ptt", "timevalue"')
            with arcpy.da.SearchCursor(in_file, f_utils.fieldLists.pathSource,
                                        None, sr, False, sql_clause=sqlClause
                                        ) as sCur:
#            if sCur:
                points = arcpy.Array()
                row = sCur.next()                                   # get first row
                from_id, from_date, ptt = row[1:4]                  # deployment point
                from_loc = f_utils.SerDate(from_date)
                points.add(arcpy.Point(*row[0]))                    # add first point to array
                for row in sCur:                                    # iterate over remaining rows
                    # trap new ptt
                    if row[3] <> ptt:
                        from_id, from_date, ptt = row[1:4]          # store deploy point
                        from_loc = f_utils.SerDate(from_date)
                        points = arcpy.Array()                      # flush array
                        points.add(arcpy.Point(*row[0]))            # deploy point to new array
                        continue
                    #
                    points.add(arcpy.Point(*row[0]))                # current row X,Y to array
                    to_id, to_date = row[1:3]
                    month = to_date.strftime('%m')
                    to_loc = f_utils.SerDate(to_date)
                    delta = to_date-from_date
                    cross = abs(points[0].X - points[1].X)          # crossing 180 longitude?
                    # standard segment
                    if cross < 300:
                        segment, dist, elapsed, speed = calcSegment(points, delta)
                        iCur.insertRow([segment, from_id, to_id, from_date, to_date,
                                        from_loc, to_loc, ptt, dist, elapsed, speed, month])
                        points.remove(0)                                # remove "from" point
                        from_id = to_id
                        from_date = to_date
                        from_loc = to_loc
                # continue row loop
                    else: # calculate for crossing dateline
                        crossDist = v_dist(points[0].Y,points[0].X,
                                           points[1].Y,points[1].X)[0]  # original distance
                        # new segment1                                  # sign returns 1.0 or -1.0
                        X = 180 * sign(points[0].X)                     # keep sign of lon1
                        Y = (points[0].Y+points[1].Y)/2                 # mean of lat1 & lat2(to keep straight line)
                        points.remove(1)                                # replace 2nd point in array
                        points.add(arcpy.Point(X, Y))
                        segDist = v_dist(points[0].Y,points[0].X,
                                         points[1].Y,points[1].X)[0]    # distance of new segment
                        # split to_date timestamp by proportion of distances from 180
                        factor = delta.seconds*(segDist/crossDist)
                        split = from_date + timedelta(seconds=factor)   # intermediate date
                        to_loc = f_utils.SerDate(split)
                        delta1 = split - from_date                      # new duration
                        segment, dist, elapsed, speed = calcSegment(points, delta1)
                        iCur.insertRow([segment, from_id, to_id, from_date, split,
                                         from_loc, to_loc, ptt, dist, elapsed, speed, month])
                        points = arcpy.Array()                          # flush array
                        from_loc = to_loc

                        # segment2
                        X = X * -1                                      # reverse of X1 sign
                        points.add(arcpy.Point(X, Y))                   # 1st point
                        points.add(arcpy.Point(*row[0]))                # 2nd point
                        delta2 = to_date - split                        # new duration
                        to_loc = f_utils.SerDate(row[2])
                        segment, dist, elapsed, speed = calcSegment(points, delta2)
                        iCur.insertRow([segment, from_id, to_id, split, to_date,
                                          from_loc, to_loc, ptt, dist, elapsed, speed, month])
                        points.remove(0)
                        from_id = to_id
                        from_date = row[2]
                        from_loc = to_loc
                    ## cast longitude to 0-360
                        ##fixLong = 360 + row[0][0]
                        ## points.add(arcpy.Point(fixLong, row[0][1]))
                    #  continue row loop

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
    ('in_file', 'C:\\CurrentProjects\\Hump18HI\\GIS\\2018HI Hump_3.gdb\\e_05736'),) # NEED that comma!
    defaults = f_utils.parameters_from_args(defaults_tuple, sys.argv)
#    main(mode='script', **defaults)
    main(**defaults)
#    main(in_file, track_name)


