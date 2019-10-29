#-------------------------------------------------------------------------------
# Name: tagdata_import
#-------------------------------------------------------------------------------
#===============================================================================

# Can run against these files:

# Wildlife Computers
# -Behavior.csv
# -Histos.csv
# -Status.csv
# -FastGPS.csv
# *** Must remove extra lines from top of WC csv files !!! ***

# **** Telonics
# serial# Complete.csv


import datetime
import csv
from sys import exit
from os import path

# local modules

import dev_db_utils as db_util
import dev_tables as tables
import map_parameters as params

# constants
inPath = '\\\\MMIDATA\\Public\\Data'
conn = db_util.getDbConn('wtg_gdb')

def str2Date(str_date, fmt):
    timevalue = datetime.datetime.strptime(str_date, fmt)
    return timevalue

#--------------------------------------------------------------------------------
def WC_FastGPS(message_type, tagDict, reader, count):
    fmt = '%m/%d/%Y %H:%M:%S'
    ptt = 0
    feature_ids = []
    feature_type = 'fastloc'
    try:
        while reader.line_num < count:
            for row in reader:
                # Trap: new Ptt
                if row['Name'] and int(row['Name']) != ptt:
                    ptt = int(row['Name'])
                    tag_id = tagDict.get(ptt)[0]
                    animal_id = tagDict.get(ptt)[1]
                    pttStart  = tagDict.get(ptt)[2] # =datetime
                    pttStop   = tagDict.get(ptt)[3]
                    print 'Processing FastLoc messages for Ptt: '+str(ptt)
                if row['Latitude'] and row['Latitude']:
                    timevalue = row['Received']
                    #Compare: tag's start date
                    if str2Date(timevalue,fmt) < pttStart:
                        continue
                    dev = (tag_id, animal_id, timevalue, feature_type)
                    # Instantiate Encounter sub-object
                    featureObj = tables.FastLoc(*dev, **row)
                    # Insert feature row
                    feature_id = db_util.dbTransact(conn, featureObj.sql_insert(),
                                    featureObj.param_dict())
                    if feature_id:
                        feature_ids.append(feature_id)
                        print 'Location at {} added'.format(timevalue)
                        conn.commit()

    except Exception as e:
        conn.rollback()
        print 'WC_FastGPS function error message: ' + e.message

    finally:
        return (feature_ids)

#--------------------------------------------------------------------------------
def WC_HistoLimits(drow, histo_type, limit_type):
    # Trap: still the same type?
    skip = False
    if drow['HistType']!= histo_type:
        # Trap: Limits row or Data row?  Redundant??
        if drow['HistType'] in params.histo_skip:
            skip = True
        elif drow['HistType'] in params.limit_skip:
            skip = True
        elif drow['HistType'] in params.histo_types:
            pass
            #histo_type = drow['HistType']
        elif drow['HistType'] in params.limit_types:
            # Find correct limit type
            rawlimits = {}
            for k, v in drow.viewitems():
                if k[:3]=='Bin':
                    if v[0] == '>':
                        continue
                    rawlimits[k] = float(drow[k])
            limits = sorted(rawlimits.values())
            for limitname, limitlist in params.histo_limits.viewitems():
                if limitlist == limits:
                    limit_type = limitname
            if limit_type:
                histo_type = limit_type[:3] # won't work with DiveDepth etc
                skip = True
            else:
                print 'histo limits not matched ->'
            #skip = True
            #continue  # ...next row
        elif drow['HistType'] == '':
            skip = True
        else: # empty row, or not interested
            skip = True
    return (histo_type, limit_type, skip)
#--------------------------------------------------------------------------------
def insertMeasData(vals):
    try:
        dataObj = tables.Measurement_Data(*vals)                    # Instantiate Measure_Data object
        data_id = db_util.dbTransact(conn, dataObj.sql_insert(),    # Insert measure_data row
                    dataObj.param_dict())
    except Exception as e:
        conn.rollback()
        print 'insertMeasData function error: ' + e.message

    finally:
        return data_id

#--------------------------------------------------------------------------------
def WC_Message(message_type, tagDict, reader, count):
    fmt = '%m/%d/%Y %H:%M:%S'
    ptt = 0
    measure_ids = []
    data_ids = []
    histo_type = ''
    limit_type = ''
    datefld = params.wc_start[message_type]
    try:
        while reader.line_num < count:
            for row in reader:
                if message_type == 'wc_histos':
                    # Trap empty rows!
                    if row['HistType'] in params.limit_types:                   #Get parameter_id's
                        datarow = {k:v for k,v in row.items() if v}
                        histo_type, limit_type, skip = WC_HistoLimits(datarow, histo_type, limit_type)
                        if skip:
                            skip = False
                            continue
                        continue
                    elif row['HistType'] in params.histo_skip:
                        continue
                    elif row['HistType'] in params.limit_skip:
                        continue
                    elif not row['HistType']:
                        continue
                if message_type == 'wc_status':
                    if not row['Received']:                                     # Skip line without a date
                        continue
                    empty = False
                    for param, field in eval('params.{}.viewitems()'.format(message_type)):
                        if row[field]:
                            empty = False
                        else:
                            empty = True
                    if empty:
                        continue
                if message_type == 'wc_behavior':                               # Trap: for 'What = Dive only
                    if row['What'] != 'Dive':
                        continue
                if row['Ptt']:                                                  # Compare: new Ptt
                    if int(row['Ptt']) != ptt:
                        ptt = int(row['Ptt'])
                        tag_id = tagDict.get(ptt)[0] #=integer
                        pttStart  = tagDict.get(ptt)[2] #=datetime
                        pttStop   = tagDict.get(ptt)[3]
                        print 'Processing {0} for PTT: {1}'.format(message_type, ptt)
                if str2Date(row[datefld],fmt) < pttStart:                           #Compare: tag's start date
                    continue
                if str2Date(row[datefld],fmt) > pttStop:                            #Compare: tag's stop date
                    continue
                # Ready to add message row
                vals = (tag_id, message_type)
                messageObj = eval('tables.{}(*vals, **row)'.format(message_type))  # Instantiate Message object
                measurement_id = db_util.dbTransact(conn, messageObj.sql_insert(), # Insert message row
                                    messageObj.param_dict())

    # *****The Problem is that an empty status row creates a message with no data
                if measurement_id:
                    measure_ids.append(measurement_id)
                    print  'Message {0} at {1} added'.format(message_type, row[datefld])
                    if message_type == 'wc_histos':                             # Add measure_data to message
                        # Capture histo values via parameter dict
                        for bin, val in params.histo_bins[limit_type].items():
                            if bin in row.viewkeys():
                                if row[bin]!='0' and row[bin]!='':
                                    vals = (val, row[bin], measurement_id)
                                    # add measure_data row
                                    data_id = insertMeasData(vals)
                                    if data_id:
                                        data_ids.append(data_id)
                                        conn.commit()
                    else:                                                       # Behavior or  Status message
                        # Iter thru dict of fieldnames
                        for param, field in eval('params.{}.viewitems()'.format(message_type)):
                            if field in reader.fieldnames:
                                if row[field]:
                                    vals = (param, row[field], measurement_id)
                                    # add measure_data row
                                    data_id = insertMeasData(vals)
                                    if data_id:
                                        data_ids.append(data_id)
                                        conn.commit()

    except Exception as e:
        conn.rollback()
        print 'WC_Message function error message: ' + e.message
        #print datarow()
    finally:
        return (measure_ids, data_ids)


#--------------------------------------------------------------------------------
def Tel_Message(message_type, tagDict, reader, count):
    fmt = '%m/%d/%Y %H:%M:%S'
    ptt = 0
    measure_ids = []
    data_ids = []
    try:
        while reader.line_num < count:    # date format is funky! 2015/12/06 15:45:49
            for row in reader:
                # New Ptt?
                if row['Ptt']:
                    if int(row['Ptt']) != ptt:
                        ptt = int(row['Ptt'])
                        tag_id = tagDict.get(ptt)[0] #=integer
                        pttStart  = tagDict.get(ptt)[2] #=datetime
                        pttStop   = tagDict.get(ptt)[3]
                        print 'Processing {0} for PTT: {1}'.format(message_type, ptt)
                #Compare: tag's start/stop date
                if str2Date(row['Receive Time'], fmt) <= pttStart:
                    continue
                if str2Date(row['Receive Time'], fmt) >= pttStop:
                    continue
                # Ready to add message row
                vals = (tag_id, message_type)
                messageObj = eval('tables.{}(*vals, **row)'.format(message_type))  # Instantiate Message object
                measurement_id = db_util.dbTransact(conn, messageObj.sql_insert(), # Insert message row
                                    messageObj.param_dict())
                if measurement_id:
                    measure_ids.append(measurement_id)
                    print  'Message {0} at {1} added'.format(message_type, str2Date(row['Receive Time'],fmt))
                    # Iter thru dict of fieldnames
                    for param, field in eval('params.{}.viewitems()'.format(message_type)):
                        if field in reader.fieldnames:
                            if row[field]:
                                if param == 'low_voltage' and row[field] == 'No':
                                    pass
                                elif param == 'sws_fail' and row[field] == 'No':
                                    pass
                                else:
                                    vals = (param, row[field], measurement_id)
                                    # add measure_data row
                                    data_id = insertMeasData(vals)
                                    if data_id:
                                        data_ids.append(data_id)
                                        conn.commit()

    except Exception as e:
        conn.rollback()
        print 'Tel_Message function error message: ' + e.message
        #print datarow()
    finally:
        return (measure_ids, data_ids)

#--------------------------------------------------------------------------------
def Switcher(message_type, inFile, proj):

    try:
        with open(inFile, 'rb') as in_file:
            count = sum(1 for line in in_file)
            in_file.seek(0)  # reset file
# WC files
            if message_type in params.message_types[:4]:
                pttfield = 'Name' if message_type == 'wc_fastgps' else 'Ptt'
                ptt_list = tuple(set([int(row[pttfield]) for row                # List all ptt's in file
                            in csv.DictReader(in_file) if row[pttfield]]))
                in_file.seek(0)                                                 # reset file
                reader = csv.DictReader(in_file)
                tagDict = db_util.getTags(conn, ptt_list, proj)                 # Retreive tag_id's from ptt's
                if message_type == 'wc_fastgps':
                    result = WC_FastGPS('wc_fastgps', tagDict, reader, count)
                else:
                    result = WC_Message(message_type, tagDict, reader, count)
# Telonics files
            elif message_type in params.message_types[4:]:
                ptt_list = tuple(set([int(row['Ptt']) for row
                            in csv.DictReader(in_file) if row['Ptt']]))
                in_file.seek(0)
                reader = csv.DictReader(in_file)
                tagDict = db_util.getTags(conn, ptt_list, proj)
                result = Tel_Message(message_type, tagDict, reader, count)
    except csv.Error as ce:
        exit('file %s, line %d: %s' % (filename, reader.line_num, ce))
    except Exception as e:
        print 'Switcher function Error: '
        print e.message

#--------------------------------------------------------------------------------
def main(proj):
    # msg_files = big dict of report file paths in map_parameters
    for m_type, f_name in params.msg_files[proj]:
        if m_type > 10:
            continue
        message_type = params.message_types[m_type]
        inFile = path.join(inPath, 'Tag_Data', proj[:4], f_name)
        if path.exists(inFile):
            print 'Starting message file: '+f_name
            Switcher(message_type, inFile, proj)
        else:
            print f_name+' Not found!'

#--------------------------------------------------------------------------------
if __name__ == '__main__':

    proj = '2019HI'
 #   main(proj)



