# trajectory.py
#
import arcpy
from arcpy import env
from os import path
import sys
import traceback
from Vincenty import calcVincentyInverse

import dev_f_utils as util

sr = arcpy.SpatialReference(4326)
#env.workspace = 'in_memory\\'
env.addOutputsToMap = True
env.overwriteOutput = True

##in_file = arcpy.GetParameterAsText(0)
##tag_field = arcpy.GetParameterAsText(1)
##time_field = arcpy.GetParameterAsText(2)
##in_fields = arcpy.GetParameterAsText(3)

def makeTrack(in_file, tag_field, time_field, in_fields, in_name=None):
    # different for script vs tool
    if type(in_fields).__name__ == 'str':
        field_list = in_fields.split(";")
    elif type(in_fields).__name__ == 'list':
        field_list = in_fields
    # port to Columns tuple
    in_cols = []
    for field in arcpy.ListFields(in_file):
        if field.name in field_list:
            in_cols.append((field.name, field.type))
    #
    homeDir = path.dirname(in_file)
    if not homeDir:
        # Toolbox: input = layer name only
        homeDir = env.workspace
        if not in_name:
            in_name = in_file
    else:
        in_name = path.basename(in_file)

    out_name = 'tr'+in_name[1:]
    temp_name = out_name
    # list of tuples instead of dict, retains field order
    pathCols = [
      ('name','TEXT'),
      ('start_date','DATE'),
      ('end_date','DATE'),
      ('from_loc','DOUBLE'),
      ('to_loc','DOUBLE'),
      ('distance_km','DOUBLE'),
      ('elapsed_hrs','DOUBLE'),
      ('speed_kmhr','DOUBLE')]
    pathCols += in_cols
    try:
        line_FC = arcpy.CreateFeatureclass_management(
        "in_memory",
        temp_name,
        "POLYLINE",
        None,
        "ENABLED",
        "DISABLED",
        sr)
        f_names = ['SHAPE@']
        for f_name, f_type in pathCols:
            arcpy.AddField_management(line_FC, f_name, f_type)
            f_names.append(f_name)
        # open an insert cursor on the new polyline FC
        with arcpy.da.InsertCursor(line_FC, f_names) as iCur:
           # list user fields
            f_names = ['SHAPE@XY', tag_field, time_field]
            for f_name, f_type in in_cols:
                f_names.append(str(f_name))
            f_count = len(f_names)
            sql_fields = "ORDER BY {0},{1}".format(tag_field, time_field)
            sql_clause = (None, sql_fields)
            with arcpy.da.SearchCursor(in_file, f_names, None, sr, False, sql_clause) as sCur:
                points = arcpy.Array()
                row = sCur.next()
                ptt = int(row[1])
                from_date = row[2]
                from_loc = util.SerDate(from_date)
                point = arcpy.Point(*row[0])
                point.M = from_loc
                points.add(point)
                curr_tag = ptt
                for row in sCur:
                    ptt = row[1]
                    if ptt != curr_tag:
                        ptt = int(row[1])
                        from_date = row[2]
                        from_loc = util.SerDate(from_date)
                        points.removeAll()
                        point = arcpy.Point(*row[0])
                        point.M = from_loc
                        points.add(point)
                        curr_tag = ptt
                    if type(row[0][0]).__name__ <> 'float':
                        continue
                    elif not row[0][0]:
                        continue
                    else:
                        point = arcpy.Point(*row[0])
                        point.M = from_loc
                        points.add(point)
                        segment = arcpy.Polyline(points, sr, False, False)
                        to_date = row[2]
                        to_loc = util.SerDate(to_date)
                        dist = calcVincentyInverse(
                            points[0].Y,
                            points[0].X,
                            points[1].Y,
                            points[1].X
                            ) [0] / 1000.0
                        delta = to_date - from_date
                        # convert to hours
                        elapsed = (delta.days*24)+(delta.seconds/3600.0)
                        # trap for indentical timevals
                        speed = dist/elapsed if elapsed > 0 else dist/0.0166667 # one minute
                        ins_row = [segment,ptt,from_date,to_date,
                                    from_loc,to_loc,dist,elapsed,speed]
                        # for each extra field in_cols, add that row index
                        for i in range(3, f_count):
                            ins_row.append(row[i])
                        iCur.insertRow(ins_row)
                        points.remove(0)
                        from_date = to_date
                        from_loc = to_loc

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
        arcpy.AddMessage('New Trajectory/Track '+out_name+ ' complete.' )
        # persist to gdb
        return(out_name)
#-------------------------------------------------------------------------------
def main(in_file, tag_field, time_field, in_fields):

    out_name = makeTrack(in_file, tag_field, time_field, in_fields)
    out_file = arcpy.CopyFeatures_management(line_FC, out_name)
    arcpy.SetParameterAsText(4, out_name)
    return(out_file)

#-------------------------------------------------------------------------------
if __name__ == '__main__':

    defaults_tuple = (
        ('in_file', 'C:\\Users\\tomas.follett\\Documents\\CurrentProjects\\    \
                            Calif 2017\\GIS\\2017CA_Hump_3.gdb\\f_04175'),
        ('tag_field', 'ptt'),
        ('time_field', 'timevalue'),
        ('in_fields', ['lc', 'device', 'individual']))

    defaults = util.parameters_from_args(defaults_tuple, sys.argv)
    #main(mode='script', **defaults)
    main(**defaults)
