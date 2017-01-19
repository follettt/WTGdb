#-------------------------------------------------------------------------------
# Name:        table_objects
# Author:      tomas.follett
# Created:     03/01/2013
# Updated:     Jan-2016

# Helper functions
def par(x): # wrap input with old-style fornatting
    y = '%({})s'.format(x)
    return y

def joyn(x): # shorter join ', '.join()
    y = ', '.join(x)
    return y
def t_int(x):
    if x=='':
        y = None
    else:
        y = int(x)
    return y
def t_float(x):
    if x=='' or x=='0.0':
        y = None
    else:
        y = float(x)
    return y
dictLC = {None:-8,'Z':-8,'B':-2,'A':-1,'0':0,'1':1,'2':2,'3':3}
#-------------------------------------------------------------------------------
class Encounter(object):

    def __init__(self, *dev):
        self.tag_id, self.animal_id, self.timevalue, self.feature_type = dev[0:4]

    def sql_param(self):
        k = sorted(self.__dict__.keys())
       # k.remove('shape_m')
        q = {'t_name': self.feature_type,
            'f_list': joyn(k),
            'f_geom': 'shape_m',
            'p_list': joyn(map(par, k)),
            'f_lat' : 'lat1',
            'p_lat' : par('lat1'),
            'f_lon' : 'lon1',
            'p_lon' : par('lon1'),
            'f_qual': 'quality',
            'p_qual': par('quality'),
            'f_tag' : 'tag_id',
            'p_tag' : par('tag_id'),
            'f_time': 'timevalue',
            'p_time': par('timevalue'),
            'f_feat': 'feature_id'}
        return q


    def sql_insert(self):
        """Return a sql string to perform an INSERT, trap duplicates and build geometry."""

#        insert = 'INSERT INTO geodata.{t_name}({f_list}) \
        insert = "INSERT INTO public.{t_name}({f_list}) \
                    SELECT {p_list} WHERE NOT EXISTS \
                    (SELECT 1 FROM {t_name} WHERE ({f_tag}={p_tag} \
                        AND {f_time}={p_time} AND {f_qual}={p_qual})) \
                  RETURNING {f_feat};".format(**self.sql_param())
        return insert

    def geom_insert(self):
        """Return a sql string to perform an INSERT, trap duplicates and build geometry."""

#        insert = 'INSERT INTO geodata.{t_name}({f_list}, {f_geom}) \
        insert = "INSERT INTO public.{t_name}({f_list}, {f_geom}) \
                  SELECT {p_list}, ST_SetSRID(ST_MakePointM( \
                  {p_lon}, {p_lat}, EXTRACT(EPOCH FROM TIMESTAMP {p_time})),4326) \
                    WHERE NOT EXISTS \
                    (SELECT 1 FROM {t_name} WHERE ({f_tag}={p_tag} \
                        AND {f_time}={p_time} AND {f_qual}={p_qual})) \
                  RETURNING {f_feat};".format(**self.sql_param())
        return insert


    def param_dict(self):
        """Assign parameters to be passed to the INSERT during Execute."""
        params = self.__dict__
        return params

    # ******* Need @decorator to prevent instantiation ***********

#-------------------------------------------------------------------------------
class Argos(Encounter):
    def __init__(self, *dev, **row):
        super(Argos, self).__init__(*dev)

        gt = dev[4]
        if not gt:                  # Argos field name was changed 2013-04-09
            f_gt = '&gt; - 120 DB'  # old
        else:
            f_gt = '> - 120 DB'     # new
        lc = row['Loc. quality']
        self.quality = dictLC[lc]
        if self.quality == -2:      # trap for B1
            if row['Msg'] == '1':
                self.quality = -3
        self.loc_class    = lc if lc<>'' else 'Z'
        self.loc_date     = self.timevalue
        self.passdur      = int(row['Pass'])
        self.satellite    = row['Sat.']
        self.frequency    = float(row['Frequency'])
        self.duplicates   = int(row['Comp.'])
        self.nb_mes       = int(row['Msg'])
        self.mes_gt120    = int(row[f_gt])
        self.best_level   = int(row['Best level'])
        self.lat1         = t_float(row['Lat. sol. 1'])
        self.lon1         = t_float(row['Long. 1'])
        self.lat2         = t_float(row['Lat. sol. 2'])
        self.lon2         = t_float(row['Long. 2'])
        self.iq           = t_int(row['Loc. idx'].zfill(2))
        self.nopc         = t_int(row['Nopc'])
        self.error_radius = t_int(row['Error radius'])
        self.semi_major   = t_int(row['Semi-major axis'])
        self.semi_minor   = t_int(row['Semi-minor axis'])
        self.ellipse      = t_int(row['Ellipse orientation'])
        self.gdop         = t_int(row['GDOP'])
##        if self.lat1 and self.lon1:
##            self.shape_m = (self.lon1, self.lat1)
##        else:
##            self.shape_m = None

    def sql_insert(self):
        return super(Argos, self).sql_insert()

    def geom_insert(self):
        return super(Argos, self).geom_insert()

    def param_dict(self):
        return super(Argos, self).param_dict()

#-------------------------------------------------------------------------------
class ArgosTx(object):
    def __init__(self, *feat, **row):
        self.timevalue, self.feature_id = feat
        self.msg_date = row['Msg Date']
        self.raw_data = ''
        # concantenate raw data
        for col in sorted(row.keys()):
            if col[:6] == "SENSOR":
                lastCol = int(col[-2:])
        for i in range(1, lastCol):
            f_name = 'SENSOR #'+str(i).zfill(2)
            if row[f_name]:
                self.raw_data += row[f_name].zfill(3)
        self.valid = True

    def sql_insert(self):
        k = sorted(self.__dict__.keys())
        q = {'t_name': 'argos_tx',
             'f_list': joyn(k),
             'p_list': joyn(map(par, k))
             }
#        insert = 'INSERT INTO wtgdata.{t_name}({f_list}) \
        insert = 'INSERT INTO public.{t_name}({f_list}) \
             SELECT {p_list} \
             RETURNING transmit_id;'.format(**q)
        return insert

    def param_dict(self):
        params = self.__dict__
        return params

#-------------------------------------------------------------------------------
class Message(object):
    """ From translated data in .csv format"""

    # need different subtypes for the various report types
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
        return sql

    def param_dict(self):
        params = self.__dict__
        return params

class wc_Status(Message):
    def __init__(self, *vals, **row):
        super(wc_Status, self).__init__(*vals)
        self.transmit_time = row['Received']

    def sql_insert(self):
        return super(wc_Status, self).sql_insert()

    def param_dict(self):
        return super(wc_Status, self).param_dict()



#-------------------------------------------------------------------------------
class Measure_Data(object):
    def __init__(self, *vals):
        self.parameter_id = vals[0]
        self.value = vals[1]
        self.measurement_id = vals[2]

    def sql_insert(self):
        """returns the text for an INSERT """
        k = sorted(self.__dict__.keys())
        q = {'t_name':'measure_data',
            'f_list': joyn(k),
            'p_list': joyn(map(par, k))}
        sql = 'INSERT INTO wtgdata.{t_name}({f_list}) \
               SELECT {p_list} \
               RETURNING data_id;'.format(**q)
        return sql

    def param_dict(self):
        params = self.__dict__
        return params


#--------------------------------------------------------------------------------
class Assay(object):pass
#-------------------------------------------------------------------------------
class GPS_Info(object):pass

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



