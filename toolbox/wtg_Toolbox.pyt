# -*- coding: utf-8 -*-

import os
import sys
import arcpy

# enable local imports; allow importing both this directory and one above
local_path = os.path.dirname(__file__) # where This file is
for path in [local_path, os.path.join(local_path, '..')]:
    full_path = os.path.abspath(path)
    sys.path.insert(0, os.path.abspath(path))

# addin specific configuration and utility functions
#import utils as addin_utils
#import config

# import utilities & config from our scripts as well
from scripts import db_utils, f_utils
reload(db_utils)
reload(f_utils)
arcpy.env.addOutputsToMap = False

#-------------------------------------------------------------------------------
class Toolbox(object):
    def __init__(self):
        self.label = u'WTG Filter Tools'
        self.alias = u'WTG Filter Tools'
        self.tools = [SelectTag,
                        Loc_Type,
                        Loc_Class,
                        Redundant,
                        Speed,
                        CreateTracks,
                        Filters]

#-------------------------------------------------------------------------------
class SelectTag(object):
    def __init__(self):
        self.label = u'Select tag(s)'
        self.description = u''
        self.canRunInBackground = False
        self.category = 'Create Data'

    def getParameterInfo(self):
        species = arcpy.Parameter()
        species.name = u'Species'
        species.displayName = u'Choose a Species'
        species.parameterType = 'Required'
        species.direction = 'Input'
        species.datatype = u'String'
        species.filter.type = "ValueList"
        species.filter.list = ['Blue','Bow','Bryde','Fin','Gray','Hump','Hybrid',
                                'RightN','RightS', 'Sperm']
        #---------------------------------------
        cruise = arcpy.Parameter()
        cruise.name = u'Cruise'
        cruise.displayName = u'Choose a Cruise (Season)'
        cruise.parameterType = 'Required'
        cruise.direction = 'Input'
        cruise.datatype = u'String'
        cruise.filter.type = "ValueList"
        #---------------------------------------
        pttList = arcpy.Parameter()
        pttList.name = u'ptt List'
        pttList.displayName = u'Choose: PTT (- Species - Tagtype)'
        pttList.parameterType = 'Required'
        pttList.direction = 'Input'
        pttList.datatype = u'String'
        pttList.filter.type = "ValueList"
        pttList.multiValue = True
        #---------------------------------------
        devices = arcpy.Parameter()
        devices.name = u'devValueTable'
        devices.displayName = u'Device List'
        devices.parameterType = 'Derived'
        devices.direction = 'Output'
        devices.datatype = u'String'
        #---------------------------------------
        combine = arcpy.Parameter()
        combine.name = u'combine'
        combine.displayName = u'Combine tags into one feature class?'
        combine.parameterType = 'Optional'
        combine.direction = 'Input'
        combine.datatype = u'Boolean'
        combine.value = False

        params = [species, cruise, pttList, devices, combine]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        # Species choice
        if parameters[0].valueAsText:
            # populate Cruises list
            parameters[1].filter.list = self.getCruiseList(parameters[0].valueAsText)
            # Cruise choice
            if parameters[1].valueAsText:
                # populate PTT list
                parameters[2].filter.list = self.getPttList(parameters[1].valueAsText)

        return

    def updateMessages(self, parameters):
        return

    def getCruiseList(self, choice):
        conn = db_utils.getDbConn()
        param = {'code': choice}
        result = db_utils.dbSelect(conn, db_utils.sqlToolbox.getCruises, param)
        cruiseList = [x[0] for x in result]
        return cruiseList

    def getPttList(self, choice):
        conn = db_utils.getDbConn()
        param = {'code': choice}
##       result = db_utils.dbSelect(conn, db_utils.sqlToolbox.getTags, param)
##       pttList = [x[0] for x in result]
        result = db_utils.dbSelect(conn, db_utils.sqlToolbox.getMeasDev, param)
        # format list for selection list
        pttList = [str(p[0]).zfill(5)+' - '+p[1]+' - '+p[2] for p in result]
        return pttList

    def getDevice(self, cruise, ptt):
        conn = db_utils.getDbConn()
        param = {'cruise': cruise, 'ptt': int(ptt)}
        result = db_utils.dbSelect(conn, db_utils.sqlToolbox.getDevice, param)
        if result:
          device = result[0][0]
        else:
          device = 0
        return str(device)

    def execute(self, parameters, messages):
        from scripts import f_SelectTags
        reload(f_SelectTags)
        devDict = {}
        pttText = parameters[2].valueAsText
        # extract a list from ';' delimited string
        pttVals = pttText.split(";")
        for p in pttVals:
            # extract ptt from list items
            pttList = p[1:-1].split(' - ')
            ptt = pttList[0]
            # create dict of {ptt: devID}
            devDict[ptt] = self.getDevice(parameters[1].valueAsText, ptt)
        parameters[3].value = str(devDict)
        # run script
        out_list = f_SelectTags.main(devices=parameters[3].valueAsText,
                                        combine=parameters[4].valueAsText)
        if out_list:
            arcpy.env.addOutputsToMap = True
            mxd = arcpy.mapping.MapDocument("CURRENT") # necessary apparently
            # reverse sorting
            out_list.sort(None,None,True)
            # make layers for new feature classes
            for fc in out_list:
                arcpy.MakeFeatureLayer_management(fc, os.path.basename(fc))

#-------------------------------------------------------------------------------
class Loc_Type(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "1: Location Type"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Filter'

    def getParameterInfo(self):

        in_file = arcpy.Parameter()
        in_file.name = u'in_file'
        in_file.displayName = u'Input dataset'
        in_file.parameterType = 'Required'
        in_file.direction = 'Input'
        in_file.datatype = u'GPFeatureLayer'

        typeBox = arcpy.Parameter()
        typeBox.name = u'typeBox'
        typeBox.displayName = u'Choose Location Type(s)'
        typeBox.parameterType = 'Required'
        typeBox.datatype = u'String'
        typeBox.direction = 'Input'
        typeBox.filter.type = "ValueList"
        typeBox.filter.list = ['Tag Deployed',
                                'Biopsy Sample',
                                'Argos Pass',
                                'FastLoc GPS',
                                'Photo ID',
                                'Derived']
        typeBox.multiValue = True
        typeBox.values = ['Tag Deployed','Biopsy Sample','Argos Pass']

        newFields = arcpy.Parameter()
        newFields.name = u'newFields'
        newFields.displayName = u'Don\'t create Log file, add filter column instead'
        newFields.parameterType = 'Optional'
        newFields.direction = 'Input'
        newFields.datatype = u'Boolean'

        params = [in_file, typeBox, newFields]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        from scripts import f_LocType
        reload(f_LocType)
        ty_file  = f_LocType.main(in_file=parameters[0].valueAsText,
                                    type_List=parameters[1].values,
                                    newFields=parameters[2].valueAsText)
        if ty_file:
            ty_file = str(ty_file)
            arcpy.env.addOutputsToMap = True
            mxd = arcpy.mapping.MapDocument("CURRENT")
            layer = os.path.basename(ty_file)
            arcpy.MakeFeatureLayer_management(ty_file, layer)


#-------------------------------------------------------------------------------
class Loc_Class(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "2: Location Class"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Filter'

    def getParameterInfo(self):

        in_file = arcpy.Parameter()
        in_file.name = u'in_file'
        in_file.displayName = u'Input dataset'
        in_file.parameterType = 'Required'
        in_file.direction = 'Input'
        in_file.datatype = u'GPFeatureLayer'

        lcBox = arcpy.Parameter()
        lcBox.name = u'lcBox'
        lcBox.displayName = u'Choose Location Class(es)'
        lcBox.parameterType = 'Required'
        lcBox.datatype = u'String'
        lcBox.direction = 'Input'
        lcBox.filter.type = "ValueList"
        lcBox.filter.list = ['G','3','2','1','0','A','B2','B1','D']
        lcBox.multiValue = True
        lcBox.values = ['G','3','2','1','0','A','B2','B1']

        newFields = arcpy.Parameter()
        newFields.name = u'newFields'
        newFields.displayName = u'Don\'t create Log file, add filter column instead'
        newFields.parameterType = 'Optional'
        newFields.direction = 'Input'
        newFields.datatype = u'Boolean'

        params = [in_file, lcBox, newFields]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        from scripts import f_LocClass
        reload(f_LocClass)
        lc_file = f_LocClass.main(in_file=parameters[0].valueAsText,
                                    lc_List=parameters[1].values,
                                    newFields=parameters[2].valueAsText)
        if lc_file:
            lc_file = str(lc_file)
            arcpy.env.addOutputsToMap = True
            mxd = arcpy.mapping.MapDocument("CURRENT")
            layer = os.path.basename(lc_file)
            arcpy.MakeFeatureLayer_management(lc_file, layer)

#-------------------------------------------------------------------------------
class Redundant(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "3: Orbit Redundant"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Filter'

    def getParameterInfo(self):

        in_file = arcpy.Parameter()
        in_file.name = u'in_file'
        in_file.displayName = u'Input dataset'
        in_file.parameterType = 'Required'
        in_file.direction = 'Input'
        in_file.datatype = u'GPFeatureLayer'

        minTime = arcpy.Parameter()
        minTime.name = u'minTime'
        minTime.displayName = u'Minimum Time in minutes'
        minTime.parameterType = 'Required'
        minTime.direction = 'Input'
        minTime.datatype = u'String'
        minTime.enabled = True
        minTime.value = '20'

        newFields = arcpy.Parameter()
        newFields.name = u'newFields'
        newFields.displayName = u'Don\'t create Log file, add filter column instead'
        newFields.parameterType = 'Optional'
        newFields.direction = 'Input'
        newFields.datatype = u'Boolean'

        params = [in_file, minTime, newFields]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        from scripts import f_Redundant
        reload(f_Redundant)
        rd_file = f_Redundant.main(in_file=parameters[0].valueAsText,
                            minTime=parameters[1].valueAsText,
                            newFields=parameters[2].valueAsText)
        if rd_file:
            rd_file = str(rd_file)
            arcpy.env.addOutputsToMap = True
            mxd = arcpy.mapping.MapDocument("CURRENT")
            layer = os.path.basename(rd_file)
            arcpy.MakeFeatureLayer_management(rd_file, layer)

#-------------------------------------------------------------------------------
class Speed(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "4: Maximum Speed"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Filter'

    def getParameterInfo(self):

        in_file = arcpy.Parameter()
        in_file.name = u'in_file'
        in_file.displayName = u'Input dataset'
        in_file.parameterType = 'Required'
        in_file.direction = 'Input'
        in_file.datatype = u'GPFeatureLayer'

        maxSpeed = arcpy.Parameter()
        maxSpeed.name = u'maxSpeed'
        maxSpeed.displayName = u'Maximum Speed'
        maxSpeed.parameterType = 'Required'
        maxSpeed.direction = 'Input'
        maxSpeed.datatype = u'String'
        maxSpeed.enabled = True
        maxSpeed.value = '12.0'

        newFields = arcpy.Parameter()
        newFields.name = u'newFields'
        newFields.displayName = u'Don\'t create Log file, add filter column instead'
        newFields.parameterType = 'Optional'
        newFields.direction = 'Input'
        newFields.datatype = u'Boolean'

        params = [in_file, maxSpeed, newFields]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        from scripts import f_Speed
        reload(f_Speed)
        sp_file = f_Speed.main(in_file=parameters[0].valueAsText,
                        maxSpeed=parameters[1].valueAsText,
                        newFields=parameters[2].valueAsText)
        if sp_file:
            sp_file = str(sp_file)
            arcpy.env.addOutputsToMap = True
            mxd = arcpy.mapping.MapDocument("CURRENT")
            layer = os.path.basename(sp_file)
            arcpy.MakeFeatureLayer_management(sp_file, layer)

#-------------------------------------------------------------------------------
class CreateTracks(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Tracks: Create"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Create Data'

    def getParameterInfo(self):
        """Define parameter definitions"""
        in_file = arcpy.Parameter()
        in_file.name = u'in_file'
        in_file.displayName = u'Input dataset'
        in_file.parameterType = 'Required'
        in_file.direction = 'Input'
        in_file.datatype = u'GPFeatureLayer'
        #---------------------------------------
##        combine = arcpy.Parameter()
##        combine.name = u'combine'
##        combine.displayName = u'Input Combined?'
##        combine.parameterType = 'Optional'
##        combine.direction = 'Input'
##        combine.datatype = u'Boolean'

        params = [in_file]      #, combine
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        from scripts import f_makePath
        reload(f_makePath)
        tr_file = f_makePath.main(in_file=parameters[0].valueAsText)#,combine=parameters[1].valueAsText)
        if tr_file:
            tr_file = str(tr_file)
            arcpy.env.addOutputsToMap = True
            mxd = arcpy.mapping.MapDocument("CURRENT")
            layer =os.path.basename(tr_file)
            arcpy.MakeFeatureLayer_management(tr_file, layer)

#-------------------------------------------------------------------------------
class Filters(object):

    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "All Filters"
        self.description = ""
        self.canRunInBackground = False
        self.category = 'Filter'

    def getParameterInfo(self):

        in_file = arcpy.Parameter()
        in_file.name = u'in_file'
        in_file.displayName = u'Input dataset'
        in_file.parameterType = 'Required'
        in_file.direction = 'Input'
        in_file.datatype = u'GPFeatureLayer'

        # Location Type filter
        typeBox = arcpy.Parameter()
        typeBox.name = u'typeBox'
        typeBox.displayName = u'Choose Location Type(s)'
        typeBox.parameterType = 'Optional'
        typeBox.datatype = u'String'
        typeBox.direction = 'Input'
        typeBox.filter.type = "ValueList"
        typeBox.filter.list = ['Tag Deployed',
                                'Biopsy Sample',
                                'Argos Pass',
                                'FastLoc GPS',
                                'Photo ID',
                                'Derived',
                                'Stranding']
        typeBox.multiValue = True
        typeBox.values = ['Tag Deployed', 'Biopsy Sample', 'Argos Pass']
        typeBox.category = '1 - Location Type [T]'

        # Location Class filter
        lcBox = arcpy.Parameter()
        lcBox.name = u'lcBox'
        lcBox.displayName = u'Choose Location Class(es)'
        lcBox.parameterType = 'Optional'
        lcBox.datatype = u'String'
        lcBox.direction = 'Input'
        lcBox.filter.type = "ValueList"
        lcBox.filter.list = ['G','3','2','1','0','A','B2','B1','D']
        lcBox.multiValue = True
        lcBox.values = ['G', '3', '2', '1', '0', 'A', 'B2', 'B1']
        lcBox.category = '2 - Location Class [L]'

        # Redundant filter
        minTime = arcpy.Parameter()
        minTime.name = u'minTime'
        minTime.displayName = u'Minimum Time in minutes'
        minTime.parameterType = 'Optional'
        minTime.direction = 'Input'
        minTime.datatype = u'String'
        minTime.enabled = True
        minTime.value = '20'
        minTime.category = '3 - Orbit Redundant [R]'

        # Speed filter
        maxSpeed = arcpy.Parameter()
        maxSpeed.name = u'maxSpeed'
        maxSpeed.displayName = u'Maximum Speed'
        maxSpeed.parameterType = 'Optional'
        maxSpeed.direction = 'Input'
        maxSpeed.datatype = u'String'
        maxSpeed.enabled = True
        maxSpeed.value = '12'
        maxSpeed.category = '4 - Maximum Speed [S]'

        newFields = arcpy.Parameter()
        newFields.name = u'newFields'
        newFields.displayName = u'Don\'t create Log file, add filter column instead'
        newFields.parameterType = 'Optional'
        newFields.direction = 'Input'
        newFields.datatype = u'Boolean'

        params = [in_file, typeBox, lcBox, minTime, maxSpeed, newFields]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""


    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        from scripts import f_Filters
        reload(f_Filters)

        type_list = parameters[1].values
##        lc_list = self.getClass(parameters[2].values)
        lc_list = parameters[2].values
##        minTime = self.getRedun(parameters[3].valueAsText)
        minTime = parameters[3].valueAsText
##        maxSpeed = self.getSpeed(parameters[4].valueAsText)
        maxSpeed = parameters[4].valueAsText

        out_file  = f_Filters.main(in_file=parameters[0].valueAsText,
                                    newFields=parameters[5].valueAsText,
                                    type_list=type_list,
                                    lc_list=lc_list,
                                    minTime=minTime,
                                    maxSpeed=maxSpeed)

        if out_file:
            out_file = str(out_file)
            arcpy.env.addOutputsToMap = True
            mxd = arcpy.mapping.MapDocument("CURRENT")
            layer = os.path.basename(out_file)
            arcpy.MakeFeatureLayer_management(out_file, layer)

##    def getClass(self, choice):
##        lc_list = None
##        if choice != ['G', '3', '2', '1', '0', 'A', 'B2', 'B1']:
##            lc_list = choice
##        return lc_list
##
##    def getRedun(self, time):
##        minTime = None
##        if time != '0':
##            minTime = time
##        return minTime
##
##    def getSpeed(self, speed):
##        maxSpeed = None
##        if speed != '0':
##            maxSpeed = speed
##        return maxSpeed


 #for Add-in:
##toolbox =  'C:\\WTG_Tools\\toolbox\\wtg_Toolbox.pyt'
##tool = 'Filters'
##pythonaddins.GPToolDialog(toolbox, tool)


# TEMPLATE
##class Tool(object):
##    def __init__(self):
##        """Define the tool (tool name is the name of the class)."""
##        self.label = "Tool"
##        self.description = ""
##        self.canRunInBackground = False
##
##    def getParameterInfo(self):
##        """Define parameter definitions"""
##        params = None
##        return params
##
##    def isLicensed(self):
##        """Set whether tool is licensed to execute."""
##        return True
##
##    def updateParameters(self, parameters):
##        """Modify the values and properties of parameters before internal
##        validation is performed.  This method is called whenever a parameter
##        has been changed."""
##        return
##
##    def updateMessages(self, parameters):
##        """Modify the messages created by internal validation for each tool
##        parameter.  This method is called after internal validation."""
##        return
##
##    def execute(self, parameters, messages):
##        """The source code of the tool."""
##        return


