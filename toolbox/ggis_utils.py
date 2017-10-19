import os
import sys
import time

import arcpy
#import pythonaddins
import dateutil.parser

# enable local imports
local_path = os.path.dirname(__file__)
sys.path.insert(0, local_path)

# import local settings
import config

def toolDialog(toolbox, tool):
    """Error-handling wrapper around pythonaddins.GPToolDialog."""
    result = None
    try:
        result = pythonaddins.GPToolDialog(toolbox, tool)
        # FIXME: this is a hack to prevent:
        # TypeError: GPToolDialog() takes at most 1 argument (2 given)
        print '',
    except TypeError:
        print "recieved TypeError when trying to run GPToolDialog(" + \
            "{toolbox}, {tool}))".format(toolbox=toolbox, tool=tool)
    # don't return anything. this prevents:
    #   TypeError: GPToolDialog() takes at most 1 argument (2 given)
    return result

def selectedLayer():
    # return the selected layer object, check that it's just points
    layer = None
    if config.selected_layer:
        # our preference is to always use the selected_layer object, which is
        # populated by our combination box.
        layer = config.selected_layer
    else:
        # if no layer is set, default to the current layer in the TOC
        layer = pythonaddins.GetSelectedTOCLayerOrDataFrame()

    #try:
    desc = arcpy.Describe(layer)
    #except:
    #    pass
    if layer is None or desc.datasetType not in config.allowed_formats:
        msg = "No layer selected! Please select a point layer from the table of contents."
        title = "No selected layer"
        pythonaddins.MessageBox(msg, title)
    else:
        if desc.shapeType not in config.allowed_types:
            msg = "Selected layer doesn't contain points."
            title = "No points in layer"
            pythonaddins.MessageBox(msg, title)
            layer = None
        # set our default SRID based on the input data layer
        config.sr = desc.spatialReference
    return layer

def currentLayers():
    # find layers in current map document
    layers = []
    # inspect the layer list, find the first point layer
    mxd = arcpy.mapping.MapDocument("current")
    # get a list of all layers, store it
    config.all_layers = arcpy.mapping.ListLayers(mxd)

    # iterate over our layers, find those which are candidates for analysis
    if config.all_layers is not None:
        for layer in config.all_layers:
            try:
                # FIXME: check performance on this. if expensive, do something cheaper
                desc = arcpy.Describe(layer)
                if desc.datasetType in config.allowed_formats and \
                    desc.shapeType in config.allowed_types:
                    layers.append(layer)
            except:
                # silently skip layers which don't support describe (e.g. AGOL).
                continue
    return layers

def getLayerByName(name):
    named_layer = None
    for layer in currentLayers():
        if layer.name == name:
            named_layer = layer
    return named_layer

def loadLayer(file_name):
    layer = None
    layer = arcpy.mapping.Layer(file_name)
    if layer is not None:
        mxd = arcpy.mapping.MapDocument("CURRENT")
        df = arcpy.mapping.ListDataFrames(mxd, "*")[0]
        arcpy.mapping.AddLayer(df, layer, "TOP")
        arcpy.RefreshActiveView()
        arcpy.RefreshTOC()
    return layer

def loadDefaultLayer(timeout=3600):
    # this is a hack -- if the class has been updated recently, refresh the list
    layer = None
    if os.path.exists(config.settings.fc_path):
        diff_in_sec = time.time() - os.path.getmtime(config.settings.fc_path)
        if timeout is None or diff_in_sec <= timeout:
            with open(config.fc_path_file) as f:
                layer = loadLayer(f.read())
    return layer

def extentPolygon(extent, source_layer=None):
    polygon_extent = None

    if extent:
        if source_layer:
            # extract the spatial reference from the source layer
            desc = arcpy.Describe(source_layer)
            input_sr = desc.spatialReference
        else:
            # use default spatial reference
            input_sr = config.sr
        # get the CURRENT data frame's spatial reference, this will be what's
        # used for the coorinates returned from onRectangle:
        mxd = arcpy.mapping.MapDocument("current")
        # get a list of all layers, store it
        df_sr = mxd.activeDataFrame.spatialReference

        # extract the coordinates from our extent object
        coords = [[extent.XMin,extent.YMin],[extent.XMax,extent.YMin], \
                    [extent.XMax,extent.YMax],[extent.XMin,extent.YMax]]

        # convert it to a polygon, we need this to compute the intersection
        polygon_extent = arcpy.Polygon(arcpy.Array(
            [arcpy.Point(x,y) for x,y in coords]), df_sr)

        if df_sr.exportToString() != input_sr.exportToString():
            # project this polygon BACK to the dataset projection
            polygon_extent = polygon_extent.projectAs(input_sr)

    return polygon_extent

def selectIndividuals(output_feature, display=False):
    res = {}
    fields = [f.name for f in arcpy.ListFields(output_feature)]
    if config.settings.id_field in fields:
        cur = arcpy.da.SearchCursor(output_feature, (config.settings.id_field))
        individuals = [row[0] for row in cur]
        unique_individuals = set(individuals)
        res = {'indiv' : individuals, 'unique' : unique_individuals}
        if display == True:
            msg = "Samples: {0}, Unique Individuals: {1}".format(
                    len(individuals), len(unique_individuals))
            title = "Samples found in selection"
            pythonaddins.MessageBox(msg, title)
    else:
        print "Couldn't find an individual ID field!"

    return res

def intersectFeatures(input_feature, intersect_feature, output_feature):
    # perform an intersection. Can take an optional 'add to selection' vs. 'new selection'
    selection_results = arcpy.SelectLayerByLocation_management(
            input_feature, "INTERSECT", intersect_feature)

    # overwrite outputs
    if arcpy.Exists(output_feature):
        arcpy.Delete_management(output_feature)

    # FIXME: expose the TOC on / off to the user
    add_output = arcpy.env.addOutputsToMap
    arcpy.env.addOutputsToMap = True
    # copy features to our output feature
    arcpy.CopyFeatures_management(selection_results.getOutput(0), output_feature)
    arcpy.env.addOutputsToMap = add_output

    return output_feature

def writeToSRGD(fc, output_path):
    # TODO: resolve issues in #39.
    with open(output_path, 'w') as output_file:
        ignored_fields = ['OID', 'OBJECTID', 'Shape']
        fields = [field.name for field in arcpy.ListFields(fc) if \
            field.name not in ignored_fields]
        output_file.write(",".join(fields) + '\n')
        our_date = "Date_formatted"
        date_exists = False
        # If we don't have a formatted date field, don't try to manipulate it.
        if our_date in fields:
            date_pos = fields.index(our_date)
            date_exists = True
        with arcpy.da.SearchCursor(fc, fields) as cursor:
            for row in cursor:
                formatted_row = list(row[:])
                if date_exists:
                    date_value = row[date_pos]
                    try:
                        formatted_row[date_pos] = formatDate(date_value)
                    except Exception as e:
                        arcpy.AddError(e)
                output_file.write(",".join([xstr(r) for r in formatted_row]) + "\n")

def formatDate(input_date):
    """
    if type (input_date) == 'str':
        # do what we did before
        parsed_date = dateutil.parser.parse(input_date)
    else:
        # we got a datetime object! we don't NEED to parse it from a string, just use it as-is
        parsed_date = input_date
    """
    format_date = input_date.strftime("%Y-%m-%d %H:%M:%S"). replace(" ", "T")
    return format_date

def xstr(s):
    # replace None values with empty strings
    if s is None:
        return ''
    return str(s)
