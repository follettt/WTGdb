#-------------------------------------------------------------------------------
# Name:        db_table_lib
# Author:      tomas.follett
# Created:     03/01/2013
# Updated:     Apr-2018

# Table Objects for inserts

# Helpful functions
par = lambda x: '%({})s'.format(x)
joyn = lambda x: ', '.join(x)
## Revised from these
##def par(x): # wrap input with old-style fornatting as required by psycopg
##    y = '%({})s'.format(x)
##    return y
##def joyn(x): # shorter join ', '.join()
##    y = ', '.join(x)
##    return y
#used only by class wc_behavior, actually just calling parsedate SLOW!!
from wtg_utils import str2Date

#===============================================================================
class Encounter(object):

    #   args: dev = (tag_id, animal_id, timeVal, feature_type, gt)
    # kwargs: row =  {field:value, field:value} DictReader of raw Argos CSV
    def __init__(self, *dev, **row):
        self.tag_id, self.animal_id, self.timevalue, self.feature_type = dev[0:4]
        self.latitude = row['lat1']
        self.longitude= row['lon1']

    def sql_param(self):

        k = sorted(self.__dict__.keys())    # sorted dict of {fieldname: value}
        q = {'t_name': self.feature_type,   # destination child table
            'f_list': joyn(k),              # list of fields
            'p_list': joyn(map(par, k))     # data wrapped for sql Insert
            }
        return q

    def sql_insert(self):
        """Return a sql string to perform an INSERT, trap duplicates."""
        insert = "INSERT INTO geodata.{t_name}({f_list}) \
                    SELECT {p_list} \
                  RETURNING feature_id;".format(**self.sql_param())
        return insert

    def param_dict(self):
        """Assign parameters to be passed to the INSERT during Execute."""
        params = self.__dict__
        return params

    # ******* Need @decorator to prevent instantiation ***********
    # @classmethod

#-------------------------------------------------------------------------------
class Argos(Encounter):

    def __init__(self, *dev, **row):
        # Encounter fields
        super(Argos, self).__init__(*dev, **row)
        # Trap Argos fieldname that changed 2013-04-09
        #f_gt = 'sub120'
        # Translate LC to quality
        dictLC = {'':-9,'Z':-8,'B':-2,'A':-1,'0':0,'1':1,'2':2,'3':3}
        # differentiate B1 and B2
        #if row['loc_class']=='B' and row['nbmes'] == '1':
        #    self.quality = -3
        #else:
        if row['loc_class']:
            if row['loc_class'] ==' ':
                self.quality = -8
                self.loc_class = 'Z'
            else:
                self.quality = dictLC[row['loc_class']]
                self.loc_class = row['loc_class']
        else:
            self.quality = -8
            self.loc_class = 'Z'
        # Argos fields
        self.loc_class    = row['loc_class'] if row['loc_class'] else 'Z'
        #self.passdur      = int(row['pass']) if row['pass'] else 0
        self.satellite    = row['satellite'] if row['satellite'] else ''
        self.frequency    = float(row['calculfreq']) if row['calculfreq'] else None
        self.nb_mes       = int(row['nbmes']) if row['nbmes'] else None
        self.mes_gt120    = int(row['nbmeslt120']) if row['nbmeslt120'] else None
        self.best_level   = int(row['bestlevel']) if row['bestlevel'] else None
        self.latitude     = float(row['lat1']) if row['lat1'] else None
        self.longitude    = float(row['lon1']) if row['lon1'] else None
        self.lat2         = row['lat2'][:10] if row['lat2'][:10] else None
        self.lon2         = row['lon2'][:10] if row['lon2'][:10] else None
        self.iq           = str(int(row['iq'].zfill(2))) if row['iq'] else 0

    def sql_param(self):
        k = sorted(self.__dict__.keys())
        q = {'f_list': joyn(k),
            'p_list': joyn(map(par, k)),
            'f_qual': 'quality',
            'p_qual': par('quality'),
            'f_tag' : 'tag_id',
            'p_tag' : par('tag_id'),
            'f_time': 'timevalue',
            'p_time': par('timevalue'),
            'f_sat': 'satellite',
            'p_sat': par('satellite')
            }
        return q

    def sql_insert(self):
        # EXISTS clause prevents duplicates
        # **** Satellite added 11/30/2017  *************** NOT finding the field?????????????
        insert = "INSERT INTO geodata.argos ({f_list}) \
                    SELECT {p_list} \
                    WHERE NOT EXISTS \
                        (SELECT 1 FROM geodata.argos WHERE ({f_tag}={p_tag} \
                        AND {f_time}={p_time} AND {f_qual}={p_qual} \
                        AND {f_sat}={p_sat})) \
                    RETURNING feature_id;".format(**self.sql_param())
        return insert

    def param_dict(self):
        return super(Argos, self).param_dict()

#-------------------------------------------------------------------------------
class ArgosTx(object):
    def __init__(self, *feat, **row):
        self.timevalue, self.feature_id = feat
        self.raw_data = row['rawdata']
##        # find last column that has data
##        for col in sorted(row.keys()):
##            if col[:6] == "SENSOR":
##                lastCol = int(col[-2:])
### TRAP: for HEX Data!!
##        # concantenate raw data
##        for i in range(1, lastCol):
##            f_name = 'SENSOR #'+str(i).zfill(2)
##            if row[f_name]:
##                self.raw_data += row[f_name].zfill(3)

    def sql_insert(self):
        k = sorted(self.__dict__.keys())
        q = {'f_list': joyn(k),
             'p_list': joyn(map(par, k))
             }
        insert = 'INSERT INTO wtgdata.transmit ({f_list}) \
                    SELECT {p_list} \
                  RETURNING transmit_id;'.format(**q)
        return insert

    def param_dict(self):
        params = self.__dict__
        return params

#===============================================================================
class FastLoc(Encounter):
    def __init__(self, *dev, **row):
        # Encounter fields
        super(FastLoc, self).__init__(*dev, **row)
        self.quality = 8
        # FastLoc fields
        self.sats_used = int(row['Satellites']) if row['Satellites'] else None
        self.bad_sats = int(row['Bad Sats']) if row['Bad Sats'] else None
        self.residual = float(row['Residual']) if row['Residual'] else None
        self.time_error = float(row['Time Error']) if row['Time Error'] else None

    def sql_param(self):
        k = sorted(self.__dict__.keys())
        q = {'f_list': joyn(k),
            'p_list': joyn(map(par, k)),
            'f_tag' : 'tag_id',
            'p_tag' : par('tag_id'),
            'f_time': 'timevalue',
            'p_time': par('timevalue')}
        return q

    def sql_insert(self):
        insert = "INSERT INTO geodata.fastloc ({f_list}) \
                    SELECT {p_list} \
                    WHERE NOT EXISTS \
                        (SELECT 1 FROM geodata.fastloc WHERE ({f_tag}={p_tag} \
                        AND {f_time}={p_time})) \
                    RETURNING feature_id;".format(**self.sql_param())
        return insert

    def param_dict(self):
        return super(FastLoc, self).param_dict()

#===============================================================================
class PhotoID(Encounter):

    def __init__(self, *dev, **row):
        # Encounter fields
        super(PhotoID, self).__init__(*dev, **row)
        self.quality = 8
        # PhotoID fields
        self.filename = row['filename']
        self.photographer = row['photographer']
        self.owner = row['owner']
        self.anatomy = row['anatomy'] if row['anatomy'] else None
        self.aspect = row['aspect'] if row['aspect'] else None
        self.gps_unit = row['gps_unit'] if row['gps_unit'] else None

    def sql_param(self):
        k = sorted(self.__dict__.keys())
        q = {'f_list': joyn(k),
            'p_list': joyn(map(par, k)),
            'f_tag' : 'tag_id',
            'p_tag' : par('tag_id'),
            'f_time': 'timevalue',
            'p_time': par('timevalue')}
        return q

    def sql_insert(self):
        insert = "INSERT INTO geodata.photo ({f_list}) \
                    SELECT {p_list} \
                    WHERE NOT EXISTS \
                        (SELECT 1 FROM geodata.photo WHERE ({f_tag}={p_tag} \
                        AND {f_time}={p_time})) \
                    RETURNING feature_id;".format(**self.sql_param())
        return insert

    def param_dict(self):
        return super(PhotoID, self).param_dict()

#===============================================================================
class Proxy(Encounter):
    def __init__(self, *dev, **row):
        # Encounter fields
        super(Proxy, self).__init__(*dev, **row)
        self.quality = -7
        # Proxy fields
        self.replace_fid = row['original_fid'] if row['original_fid'] else None
        self.source = row['source']

    def sql_param(self):
        k = sorted(self.__dict__.keys())
        q = {'f_list': joyn(k),
            'p_list': joyn(map(par, k)),
            'f_tag' : 'tag_id',
            'p_tag' : par('tag_id'),
            'f_time': 'timevalue',
            'p_time': par('timevalue')}
        return q

    def sql_insert(self):
        insert = "INSERT INTO geodata.proxy ({f_list}) \
                    SELECT {p_list} \
                    WHERE NOT EXISTS \
                        (SELECT 1 FROM geodata.proxy WHERE ({f_tag}={p_tag} \
                        AND {f_time}={p_time})) \
                    RETURNING feature_id;".format(**self.sql_param())
        return insert

    def param_dict(self):
        return super(Proxy, self).param_dict()

#===============================================================================
class Message(object):
    """ From translated data in .csv format"""
    def __init__(self, *vals, **row):
        self.tag_id, self.message_type = vals

    def sql_insert(self):
        """returns the text for an INSERT """
        k = sorted(self.__dict__.keys())
        q = {'t_name':'message',
            'f_list': joyn(k),
            'p_list': joyn(map(par, k))}

        sql = 'INSERT INTO wtgdata.{t_name}({f_list}) \
               SELECT {p_list} \
               RETURNING measurement_id;'.format(**q)
#   Dupe trap            WHERE NOT EXISTS \
#                    (SELECT 1 FROM wtgdata.{t_name} WHERE ({f_tag}={p_tag}
#                     AND {f_time}={p_time}

        return sql

    def param_dict(self):
        params = self.__dict__
        return params

#-------------------------------------------------------------------------------
class wc_status(Message):
    def __init__(self, *vals, **row):
        super(wc_status, self).__init__(*vals)
        self.transmit_time = row['Received']
        self.value_time = row['RTC'] if row['RTC'] else row['Received']

    def sql_insert(self):
        return super(wc_status, self).sql_insert()

    def param_dict(self):
        return super(wc_status, self).param_dict()

#-------------------------------------------------------------------------------
class tel_status(Message):
    def __init__(self, *vals, **row):
        super(tel_status, self).__init__(*vals)
        self.transmit_time = row['Receive Time']
        self.value_time = row['Acquisition Time']

    def sql_insert(self):
        return super(tel_status, self).sql_insert()

    def param_dict(self):
        return super(tel_status, self).param_dict()

#-------------------------------------------------------------------------------
class wc_behavior(Message):
    def __init__(self, *vals, **row):
        super(wc_behavior, self).__init__(*vals)
        self.value_time = row['Start']
        if row['End']:
# **************** get rid of str2Date!
            delta = str2Date(row['End']) - str2Date(row['Start'])
            self.duration = delta.seconds/60.0

    def sql_insert(self):
        return super(wc_behavior, self).sql_insert()

    def param_dict(self):
        return super(wc_behavior, self).param_dict()

#-------------------------------------------------------------------------------
class tel_dives(Message):
    def __init__(self, *vals, **row):
        super(tel_dives, self).__init__(*vals)
        self.value_time = row['Dive Start Time']
        self.duration = row['Dive Duration']

    def sql_insert(self):
        return super(tel_dives, self).sql_insert()

    def param_dict(self):
        return super(tel_dives, self).param_dict()

#-------------------------------------------------------------------------------
class wc_histos(Message):
    def __init__(self, *vals, **row):
        super(wc_histos, self).__init__(*vals)
        self.value_time = row['Date']
        self.duration = 3600            # ** default to 6 hours (for now)

    def sql_insert(self):
        return super(wc_histos, self).sql_insert()

    def param_dict(self):
        return super(wc_histos, self).param_dict()


#===============================================================================
class Measurement_Data(object):
    def __init__(self, *vals):
        self.parameter_id = vals[0]
        self.value = vals[1]
        self.measurement_id = vals[2]

    def sql_insert(self):
        """returns the text for an INSERT """
        k = sorted(self.__dict__.keys())
        q = {'t_name':'measurement_data',
            'f_list': joyn(k),
            'p_list': joyn(map(par, k))}

        sql = 'INSERT INTO wtgdata.{t_name}({f_list}) \
               SELECT {p_list} \
               RETURNING data_id;'.format(**q)
        return sql

    def param_dict(self):
        params = self.__dict__
        return params

#===============================================================================
class Deployment(object):

   def __init__(self, *vals):
        self.tag_id, \
        self.last_pass, \
        self.sum_passes, \
        self.sum_pass_days, \
        self.sumdep_pass, \
        self.last_location, \
        self.sum_locations, \
        self.sum_location_days, \
        self.sum_dep_loc, \
        self.sum_msgs \
         = vals

   def sql_update(self):
        k = sorted(self.__dict__.keys())
        q = {'f_list': joyn(k),
            'p_list': joyn(map(par, k))}

        sql = 'UPDATE wtgdata.deployment \
                SET last_pass = %(last_pass)s, \
                    last_location = %(last_location)s \
                WHERE tag_id = %(tag_id)s;' \
                .format(('tag_id', 'stop_date'))
        return sql

   def param_dict(self):
        params = self.__dict__
        return params

#===============================================================================
class Device(object):
    def __init__(self, *dev):
        self.tag_id, self.stop_date = dev

    def sql_update_last(self):
        k = sorted(self.__dict__.keys())
        q = {'f_list': joyn('tag_id'),
            'p_list': joyn(map(par, k))}

        sql = 'UPDATE wtgdata.device \
                SET last_tx = %(stop_date)s \
                WHERE tag_id = %(tag_id)s;'.format(('tag_id', 'stop_date'))
        return sql

    def param_dict(self):
        params = self.__dict__
        return params

#===============================================================================
class PttList(object):
    def __init__(self, *vals):
        self.ptt, self.last_tx = vals

    def sql_update_last(self):
        k = sorted(self.__dict__.keys())
        q = {'f_list': joyn('ptt'),
            'p_list': joyn(map(par, k))}

        sql = 'UPDATE wtgdata.ptt_list \
                SET mmi_latest = %(last_tx)s \
                WHERE ptt = %(ptt)s;'.format(('ptt', 'last_tx'))
        return sql

    def param_dict(self):
        params = self.__dict__
        return params

#--------------------------------------------------------------------------------
class Assay(object):pass
#-------------------------------------------------------------------------------
##class Encounter_1(object):
##    """template for Encounter subtypes """
##    def __init__(self, **kw):
##        self.animal_id    = kw['animal_id']
##        self.tag_id       = kw['tag_id']
##        self.timevalue    = kw['timevalue']
##        self.feature_type = kw['feature_type']
##        self.quality      = kw['quality']
##        self.shape_m      = kw['shape_m']
##
##    def sql_insert(self):
##        """Return a sql string to perform an INSERT, trap duplicates and build geometry."""
##        k = sorted(self.__dict__.keys())
##        k.remove('shape_m')
##        q = {'t_name': self.feature_type,        # 'argos'
##                'f_list': joyn(k),               # string list
##                'p_list': joyn(map(par, k)),     # "wrapped" f_list without 'geom'
##                'f_geom': 'shape_m',
##                'p_geom': par('shape_m'),
##                'f_qual': 'quality',
##                'p_qual': par('quality'),
##                'f_tag' : 'tag_id',
##                'p_tag' : par('tag_id'),
##                'f_time': 'timevalue',
##                'p_time': par('timevalue'),
##                'f_feat': 'feature_id'}
##        insert = 'INSERT INTO geodata.{t_name}({f_list}, {f_geom}) \
##                    SELECT {p_list}, \
##                        ST_SetSRID(ST_MakePointM({p_geom}, \
##                            EXTRACT(epoch FROM {f_time})),4326) \
##                    WHERE NOT EXISTS \
##                    (SELECT 1 FROM {t_name} WHERE ({f_tag}={p_tag} \
##                        AND {f_time}={p_time} AND {f_qual}={p_qual})) \
##                  RETURNING {f_feat};'.format(**q)
##        return insert
##
##    def param_dict(self):
##        """Assign parameters to be passed to the INSERT during Execute."""
##        params = sorted(self.__dict__)
##        return params
##
##
###  @abstractmethod
###    def feature_type():
###        """"Return a string representing the type of encounter this is."""
##
###--------------------------------------------------------------------------------
##class Argos_1(Encounter):
##
##    def __init__(self, **kw):
##        super(Argos, self).__init__(**kw)
##        self.loc_class      = kw['loc_class']
##        self.loc_date       = kw['loc_date']
##        self.passdur        = kw['passdur']
##        self.satellite      = kw['satellite']
##        self.frequency      = kw['frequency']
##        self.duplicates     = kw['duplicates']
##        self.nb_mes         = kw['nb_mes']
##        self.mes_gt120      = kw['mes_gt120']
##        self.best_level     = kw['best_level']
##        self.lat1           = kw['lat1']
##        self.lon1           = kw['lon1']
##        self.lat2           = kw['lat2']
##        self.lon2           = kw['lon2']
##        self.iq             = kw['iq']
##        self.nopc           = kw['nopc']
##        self.error_radius   = kw['error_radius']
##        self.semi_major     = kw['semi_major']
##        self.semi_minor     = kw['semi_minor']
##        self.ellipse        = kw['ellipse']
##        self.gdop           = kw['gdop']
##
##    def sql_insert(self):
##        return super(Argos, self).sql_insert()
##    def param_dict(self):
##        return super(Argos, self).param_dict()
#--------------------------------------------------------------------------------
    # sql module depends on psycopg2-v2.7, not released yet
##    table = sql.Identifier('geodata.tablename')
##    sqlstring = sql.SQL('INSERT INTO {0}({1}) SELECT {2}, \
##                            ST_SetSRID(ST_MakePointM({3}, \
##                            EXTRACT(epoch FROM {4})),{5}) \
##                            WHERE {6} IS NOT NULL \
##                            WHERE NOT EXISTS (SELECT 1 FROM {0} \
##                            WHERE ({7}={8} AND {9}={10} AND {11}={12})) \
##                            RETURNING {13};').format(
##                    table,                                                  # 0 geodata.tablename
##                    sql.SQL(', ').join(map(sql.Identifier, f)),             # 1 (fields)
##                    sql.SQL(', ').join(map(sql.Placeholder, f)),            # 2 (%(fields)s)
##                    sql.SQL(', ').join(map(sql.Placeholder, geom)),         # 3 %(lon)s, %(lat)s
##                    sql.Placeholder(f[3]),                                  # 4 %(timevalue)s)
##                    sql.Literal(4326),                                      # 5 4326
##                    sql.Placeholder(geom[0]),                               # 6 lat
##                    sql.Identifier(f[1]),                                   # 7 tag_id
##                    sql.Placeholder(f[1]),                                  # 8 %(tag_id)s
##                    sql.Identifier(f[3]),                                   # 9 timevalue
##                    sql.Placeholder(f[3]),                                  # 10 %(timevalue)s
##                    sql.Identifier(f[4]),                                   # 11
##                    sql.Placeholder(f[4]),                                  # 12
##                    sql.Identifier('feature_id')                            # 13
#-------------------------------------------------------------------------------



