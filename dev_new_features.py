#-------------------------------------------------------------------------------
# Name:        makeNewFeatures.py
# Author:      tomas.follett
#
# Created:     10/07/2013
# Updated:     10/24/2013
#-------------------------------------------------------------------------------
import arcpy
from arcpy import env
import os
import wtg_db_utils as dbutil

sr = arcpy.SpatialReference(4326)
conn = dbutil.getDbConn('mmi_wtg')

#==== parameters for toolbox mode
in_path = dbutil.getSDEConn('mmi_wtg')
in_fc = in_path+'\\mmi_wtg.working.encounter_stage'

out_path = dbutil.getSDEConn('mmi_sde')
stage_fc = out_path + '\\mmi_sde.sde.encounter_stage'
out_fds = out_path + '\\mmi_sde.sde.telemetry'
out_fc = out_fds+ '\\mmi_sde.sde.encounter'

#-----------------------------------------------------------------------------
def truncateSdeEncounter():
  try:
    arcpy.TruncateTable_management(out_fc)
  except Exception as e:
    print 'Error truncating sde.encounter: ' + e.message
  finally:
    print '...Done'
#-----------------------------------------------------------------------------
def truncateSdeStaging():
  try:
    arcpy.TruncateTable_management(stage_fc)
  except Exception as e:
    print 'Error truncating sde.encounter_stage: ' + e.message
  finally:
    print '...Done'

#-----------------------------------------------------------------------------
def truncateWtgStaging():
  try:
    sql = dbutil.sqlArgosImport.truncateWtgStaging
    result = dbutil.dbTransact(conn, sql, ())
  except Exception as e:
    print 'Error truncating wtg.encounter_stage: ' + e.message
    conn.rollback()
  finally:
    conn.commit()
    print '...Done'
#-----------------------------------------------------------------------------
def fillStaging(featList):
  param = {'feats': tuple(featList)}
  sql = dbutil.sqlArgosImport.appendStaging
  try:
    result = dbutil.dbSelect(conn, sql, param)
    #objsList = [f[0] for f in result]
  except Exception as e:
    print 'Error appending wtg.encounter_stage: ' + e.message
    conn.rollback()
  finally:
    result = None
    conn.commit()
    print '...Done'
  #return objsList
#-----------------------------------------------------------------------------
def makeXY():
  arcpy.env = 'in_memory'
  try:
    scratchFile = arcpy.MakeXYEventLayer_management(in_fc, "longitude","latitude",
                                                'scratch' , sr, None)
  except Exception as e:
    print 'Error creating in_memory XY event layer: ' + e.message
  finally:
    print '...Done'
  return scratchFile
#-----------------------------------------------------------------------------
def copyToStage(scratchFile):
  arcpy.env = out_path
  env.overwriteOutput = True
  try:
    arcpy.CopyFeatures_management(scratchFile, stage_fc)
  except Exception as e:
    print 'Error copying scratch features to sde.encounter_stage: ' + e.message
  finally:
    print '...Done'
#-----------------------------------------------------------------------------
def loadEncounter():
  try:  # inside of an edit session...
    with arcpy.da.Editor(out_path) as edit:
      with arcpy.da.InsertCursor(out_fc, dbutil.sqlArgosImport.f_names) as inCur:
        with arcpy.da.SearchCursor(stage_fc, dbutil.sqlArgosImport.f_names) as sCur:
          for row in sCur:
            inCur.insertRow(row)
  except Exception as e:
    print 'Error inserting sde.encounter_stage to sde.encounter: ' + e.message
  finally:
    print "Finished with Encounter updates"

#-----------------------------------------------------------------------------
def main(featList):
  newLoad = False
  print 'Begin creating new features from wtg.encounter'
  # truncate mmi_wtg staging table
  print 'Truncating wtg.encounter_stage...'
  truncateWtgStaging()

  # If not passed in, find a list of the new featureids
  if featList == []:
    newLoad = True
    param = {}
    sql = dbutil.sqlArgosImport.getAllEncounters
    result = dbutil.dbSelect(conn, sql, param)
    featList = [f[0] for f in result]
    #== get from FeatureList.csv instead!

  # copy new records to staging table
  print 'Appending wtg.encounter_stage...'
  fillStaging(sorted(featList))
  # create temporary XY layer
  print 'Creating in_memory XY event layer...'
  scratchFile = makeXY()
  #truncate SDE Encouter_Stage
  print 'Truncating sde.encounter_stage...'
  truncateSdeStaging()
  if newLoad:
    print 'WARNING!! Truncating sde.encounter...'
    truncateSdeEncounter()
  # copy features to staging featureclass
  print "Appending sde.encounter_stage..."
  copyToStage(scratchFile)
  # insert staging features to Encounter
  print "Loading sde.encounter from staging..."
  loadEncounter()

#-----------------------------------------------------------------------------
if __name__ == '__main__':
    featList = []
    #featList = range(148102,148108)
    main(featList)
    #main([])