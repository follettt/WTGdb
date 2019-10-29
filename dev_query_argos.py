#-------------------------------------------------------------------------------
# Name:        select_argos.py
# Created:      12/14/2017

# Select encounters from WTG_GUI as a Query Layer
#
#
#-------------------------------------------------------------------------------
import arcpy

# local imports
import dev_f_utils as f_utils
import dev_db_utils as db_utils

sr = arcpy.SpatialReference(4326)
# Code to work with desktop
mxd = arcpy.mapping.MapDocument('CURRENT')
df = arcpy.mapping.ListDataFrames(mxd)[0]
mxd.activeView = df.name

# input params
# Parameters 0,1,2 are provided by Tool Validation code
#species = arcpy.GetParameterAsText(0)
#project = arcpy.GetParameterAsText(1)
#pttList = arcpy.GetParameterAsText(2)
devices = arcpy.GetParameterAsText(3)
combine = arcpy.GetParameterAsText(4)
#  "{'ptt.zfill(5)' : 'tag_id'}"
#devices = "{'04175': '792', '00827': '786'}"
#combine = 'false'

# *** TODO: Probably need to grab start stop dates ************

# Validation code returns string '{dict}'; eval() converts to actual dict
devDict = eval(devices)

if combine == 'true':
    # isolate tag_id's
    tagList = tuple([int(v) for v in devDict.values()])                         # tag_id's
    sqlSelect = "SELECT * FROM geodata.v_argos_ellipse \
                 WHERE tag_id in {0}".format(tagList)
    layerName = 'q_tags_argos'
    # v_argos_ellipse DB View uses fid as a "sacrificial" key for Arcmap to ingest as OBJID
    q_layer = arcpy.MakeQueryLayer_management("Database Connections/wtg_gdb.sde",
                                                layerName,
                                                sqlSelect,
                                                "fid",
                                                "POINT",
                                                "4326",
                                                sr)
else:
    for ptt, devID in devDict.iteritems():
        layerName = 'q_' +ptt+'_argos'
        sqlSelect ="SELECT * FROM geodata.v_argos_ellipse WHERE tag_id = {0}".format(int(devID))
        q_layer = arcpy.MakeQueryLayer_management("Database Connections/wtg_gdb.sde",
                                                layerName,
                                                sqlSelect,
                                                "fid",
                                                "POINT",
                                                "4326",
                                                sr)

lyr = arcpy.mapping.Layer(layerName)

arcpy.mapping.AddLayer(df, lyr, 'TOP')
df.extent = lyr.getSelectedExtent()

##try:
##except arcpy.ExecuteError:
##    msgs = arcpy.GetMessages(2)
##    arcpy.AddError(msgs)
##    print msgs
##except:
##    tb = sys.exc_info()[2]
##    tbinfo = traceback.format_tb(tb)[0]
##    pymsg = "PYTHON ERRORS:\nTraceback info:\n" + tbinfo + "\nError Info:\n" + str(sys.exc_info()[1])
##    msgs = "ArcPy ERRORS:\n" + arcpy.GetMessages(2) + "\n"
##    arcpy.AddError(pymsg)
##    arcpy.AddError(msgs)
##    print pymsg + "\n"
##    print msgs

