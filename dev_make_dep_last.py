# make_deploy_last.py

import arcpy
from arcpy import env
from datetime import datetime
from os import path
import traceback
import sys
# Local Imports
import dev_f_utils as util
import dev_db_utils as dbutil

# Set Geoprocessing environments
#mxd = arcpy.mapping.MapDocument("CURRENT")
#env.addOutputsToMap = True
env.overwriteOutput = True

# Global vars
sr = arcpy.SpatialReference(4326)
fmt = '%m/%d/%Y %H:%M:%S'
conn = dbutil.getDbConn(db='wtg_gdb')

# Parameters
in_points = arcpy.GetParameterAsText(0)
#in_points = 'C:\\CurrentProjects\\Hump19HI\\GIS\\2019HI_Current.gdb\\f_2019HI'

homeDir = path.dirname(in_points)
if not homeDir:
    homeDir = env.workspace

deployName = ''.join(['dl_', in_points[2:]])

# scrape tag_id's from layer
sql_clause = (None, 'ORDER BY "ptt", "timevalue" ASC')
fields = ("ptt", "timevalue", "tag_id")  #"device")
try:
    with arcpy.da.SearchCursor(in_points, fields, None, sr, None, sql_clause) as sCur:
        dev_list = list(set([row[2] for row in sCur]))
    # get summary for tags
    tagDict = dbutil.getTag_Summary(conn, dev_list)
    # {ptt: [tag_class, start_date, stop_date, species_name, gen_sex, tag_id]

    # create new Feature Class
    # list of tuples instead of dict, retains order
    deployCols = [
          ('ptt','TEXT'),
          ('timevalue','DATE'),
          ('tag_type','TEXT'),
          ('species','TEXT'),
          ('sex','TEXT'),
          ('month','TEXT'),
          ('feature_type', 'TEXT'),
          ('haplotype','TEXT'),
          ('locality','TEXT'),
          ('history', 'LONG')
          ]

    deployName = ''.join(['dl_', in_points[2:]])
    deployFile = arcpy.CreateFeatureclass_management(
            homeDir,
            deployName,
            "POINT",
            None,
            "ENABLED",
            "DISABLED",
            sr)
    f_names = ['SHAPE@']
    for f_name, f_type in deployCols:
        arcpy.AddField_management(deployFile, f_name, f_type)
        f_names.append(f_name)

    # append values to new FC
    with arcpy.da.InsertCursor(deployFile, f_names) as iCur:
        fields = ["SHAPE@XY",
                "feature_id",
                "ptt",
                "timevalue",
                "animal_name",
                "species_name",
                "feature_type"]

        with arcpy.da.SearchCursor(in_points, fields, None, sr, None, sql_clause) as sCur:
            for ptt in tagDict.keys():
                sCur.reset()
                pttRow = [row for row in sCur if row[2] == ptt]
                if len(pttRow) == 0:
                    arcpy.AddMessage('Empty: ' + str(ptt) + '# Rows = ' + str(len(pttRow)))
                    continue
                arcpy.AddMessage('Processing: ' + str(ptt) + '# Rows = ' + str(len(pttRow)))
                if pttRow[0][6] != 'deploy':
                    row = [r for r in pttRow if r[6] == 'deploy']
                    if len(row) == 0:
                        arcpy.AddMessage('Empty: ' + str(ptt) + '# Rows = ' + str(len(row)))
                    continue
                else:
                    row = pttRow[0]
                iRow = [row[0],                 # Shape
                        ptt,
                        row[3],                 # timevalue
                        tagDict.get(ptt)[0],    # tag_type
                        tagDict.get(ptt)[3],    # species
                        tagDict.get(ptt)[4],    # sex
                        row[3].strftime('%m'),  # month
                        'deploy',               # feature_type
                        '',                     # haplo
                        '',                     # locality
                        0
                        ]
                iCur.insertRow(iRow)
                row = pttRow[-1]
                iRow = [row[0],
                        ptt,
                        row[3],
                        tagDict.get(ptt)[0],
                        tagDict.get(ptt)[3],
                        tagDict.get(ptt)[4],
                        row[3].strftime('%m'),
                        'final',
                        '','',0
                        ]
                iCur.insertRow(iRow)


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
















