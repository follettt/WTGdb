# Build out data messages from Argos Raw, based on GDB parameters
#from os import path
#import sys
import csv
import datetime
import dev_db_utils as dbutil
import dev_tables as tables

conn = dbutil.getDbConn('wtg_gdb')
fmt = '%m/%d/%Y %H:%M:%S'

measures = []

#-------------------------------------------------------------------------------
def exam_data(raw_data, proc):

    value = 0
    valid = 'False'

    if proc == 'Hex':
        if len(raw_data) != 8:
            print "Wrong length :" + raw_data
            return 0, 0, 'False'
        else:
            hex1 = raw_data[:4]
            hex2 = raw_data[4:]
            val1 = int(hex1, 16)
            val2 = int(hex2, 16)

    elif proc == 'DAP':
        if len(raw_data) != 12:
            print "Odd # characters :" + raw_data
            return 0, 0, 'False'
        else:
            h2d = lambda d: hex(d)[2:].zfill(2)
            # convert integers to hex,
            hex1 = ''.join([h2d(int(raw_data[:3])), h2d(int(raw_data[3:6]))])
            hex2 = ''.join([h2d(int(raw_data[6:9])), h2d(int(raw_data[9:12]))])
            val1 = int(hex1, 16)
            val2 = int(hex2, 16)

    elif proc == 'Dec': # CHECK Vals starting with 2008CA & tagtypes 33,35,36
        prev_len = 3
        string = len(raw_data)
        if string % 2 != 0: # odd length
            print "Odd # characters :" + raw_data
            return 0, 0, 'False'
        else:
            seg = string/2
            if prev_len - seg > 1:
                return 0, 0, 'False'
            else:
                val1 = int(raw_data[:seg])
                val2 = int(raw_data[seg:])
                prev_len = string

    if val1 != val2:    # CRC error
        valid = 'False'
    elif val1 == val2:
        valid = 'True'

        # not the right solution, counter will keep increasing
##        if val1 <= counter:
##            if val1 < 5000 and counter > 50000:    # count across rollover
##                 val1 += (65536 - counter)

    return val1, val2, valid


#-------------------------------------------------------------------------------
def insertMeasData(vals):

    data_id = None
    try:
        dataObj = tables.Measurement_Data(*vals)                    # Instantiate Measure_Data object
        data_id = dbutil.dbTransact(conn, dataObj.sql_insert(),    # Insert measure_data row
                    dataObj.param_dict())
    except Exception as e:
        conn.rollback()
        print 'insertMeasData function error: ' + e.message

    finally:
        return data_id


def main(tagDict, proj):
    global measures
    message_type = 'tel_counter'
    pttList = sorted([p for p in tagDict.keys()])
    for ptt in pttList:
        print ptt
        tag_id = tagDict[ptt][0]

        # skip tag(s)
#        if tag_id not in [506]:
#           continue

        result = dbutil.getTelParam(conn, tag_id)
        param = result[0]
        proc = result[1]
        if param not in ('CTAS','CNOT','CNOS'):
            continue
        transmits = dbutil.getRawData(conn, tag_id)
        for row in transmits:
#            if row[2] < 508255:
#               continue
            val1, val2, valid = exam_data(row[4], proc) # process raw data
            if val1 == 0:                               # Skip weird string lengths
                continue
            print (ptt, row[3], valid, val1, val2)
            # build message for insert
            meas_row = {'tag_id':tag_id,
                   'transmit_id':row[2],
                    'value_time':row[3],
                  'message_type':message_type,
                 'transmit_time':row[3],
                         'valid':valid}

            # insert message, return measurement_id
            vals = (tag_id, message_type)
            messageObj = eval('tables.{}(*vals, **meas_row)'.format(message_type))  # Instantiate Message object
            measurement_id = dbutil.dbTransact(conn, messageObj.sql_insert(), # Insert message row
                                messageObj.param_dict())
            if measurement_id:
                # get from DB
                if valid == 'False':
                    for val in [str(val1), str(val2)]:
                        data_row = val
                        vals = (param, data_row, measurement_id)
                        data_id = insertMeasData(vals)
                    if data_id:
                        conn.commit()
                    else:
                        print 'DB Error'
                elif valid == 'True':
                    data_row = str(val1)
                    vals = (param, data_row, measurement_id)
                    data_id = insertMeasData(vals)
                    if data_id:
                        conn.commit()
                    else:
                        print 'DB Error'


if __name__ == '__main__':

    proj = '2014AK'
    tagDict = dbutil.getDeployTags(conn, proj)

    main(tagDict, proj)

##tagDict = {ptt: 0  (tag_id,
##          1  animal_id,
##          2  start_date,
##          3  stop_date,
##          4  tagtype_id,
##          5  serial,
##          6  data_dir,
##          7  report_file,
##          8  species)}

##  result = [0 feature_id,
##             1 passTime,
##             2 transmit_id,
##             3 transmit_time,
##             4 raw_data]