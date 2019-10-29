#
#
# Map parameter_id's to csv fieldnames
#-------------------------------------------------------------------------------
message_types = ['wc_status',   # 0
                'wc_behavior',  # 1
                'wc_histos',    # 2
                'wc_fastgps',   # 3
                'tel_status',   # 4
                'tel_dives',    # 5
                'tel_counter']   # 6

# Wildlife Computers csv reports
#==============================================================================='\\2019Dupes.csv'
# Different date fields for each report
# Dict =    {Report        : Date field}
wc_start = {'wc_status'   : 'Received',
            'wc_behavior' : 'Start',
            'wc_histos'   : 'Date',
            'wc_fastgps'  : 'Received',  #  'Date'+'Time' *** Fixed in All-FastGPS.csv now 'Received'
            'wc_statusold': 'ReceptionDateTime' # 07-08 Status
             }

# Fields to capture for measurement_data
# Dict =    {parameter_id : Column}
wc_status = {'time_offset':'Time Offset',
             'transmits'   :'Transmits',
             'batt_voltage':'BattVoltage',
             'tx_voltage'  :'TransmitVoltage',
             'tx_current'  :'TransmitCurrent',
             'temperature' :'Temperature'}
#             'voltage'     :'Voltage',
wc_behavior = {'end_time'    :'End',
               'dive_shape'  :'Shape',
               'depth_min'   :'DepthMin',   #Change to average ********
               'depth_max'   :'DepthMax',
               'duration_min':'DurationMin',
               'duration_max':'DurationMax'}
               #'shallow'     :'Shallow',
               #'deep'        :'Deep'}

wc_fastgps = {'loc_number':'LocNumber',
             'failures'   :'Failures',
             'satellites' :'Satellites',
             'latitude'   :'Latitude',
             'longitude'  :'Longitude',
             'bad_sats'   :'Bad Sats',
             'residual'   :'Residual',
             'time_error' :'Time Error'}

wc_histos = {'hist_type'    :'HistType',
            'time_offset'   :'Time Offset',
            'count'         :'Count'}
            #,'bad_thermistor':'BadTherm'}
            #,'num_bins'      :'NumBins' }

# 'sum_period' == has to come from a query
histo_types = ['TAT','TAD'] #
histo_skip  = ['DiveDepth','DiveDuration','Percent']
limit_types = ['TATLIMITS','TADLIMITS'] #
limit_skip  = ['DiveDepthLIMITS','DiveDurationLIMITS']

# Limit name: Values in LIMITS row
histo_limits = {'TAD20-1400_0.5':[20.0,100.0,200.0,300.0,400.0,500.0,600.0,
                                700.0,800.0,900.0,1000.0,1200.0,1400.0,2007.5],
                'TAD20-1400_1.0':[20.0,100.0,200.0,300.0,400.0,500.0,600.0,700.0,
                                800.0,900.0,1000.0,1200.0,1400.0,4015.0],
                'TAD25-400_1.0' :[25.0,50.0,75.0,100.0,125.0,150.0,175.0,200.0,
                                225.0,250.0,275.0,300.0,400.0,4015.0],
                'TAT6-60_2C'    :[6.0,8.0,10.0,12.0,14.0,16.0,18.0,20.0,22.0,
                                24.0,26.0,60.0],
                'TAT10-60_2C'   :[10.0,12.0,14.0,16.0,18.0,20.0,22.0,24.0,26.0,
                                28.0,30.0,60.0],
                'TAT-2-50_3C'   :[-2.0,0.0,3.0,6.0,9.0,12.0,15.0,18.0,21.0,24.0,
                                27.0,30.0,33.0,50.0]}

# Limit name: parameter_id's
histo_bins = {'TAD20-1400_0.5':{'Bin1':'tad-40:20m','Bin2':'tad020.5:100m',
            'Bin3':'tad100.5:200m','Bin4':'tad200.5:300m','Bin5':'tad300.5:400m',
            'Bin6':'tad400.5:500m','Bin7':'tad500.5:600m','Bin8':'tad600.5:700m',
            'Bin9':'tad700.5:800m','Bin10':'tad800.5:900m','Bin11':'tad900.5:1000m',
            'Bin12':'tad1000.5:1200m','Bin13':'tad1200.5:1400m','Bin14':'tad1400.5:2007.5m'},
           'TAD20-1400_1.0':{'Bin1':'tad-80:20m','Bin2':'tad021:100m',
            'Bin3':'tad101:200m','Bin4':'tad201:300m','Bin5':'tad301:400m',
            'Bin6':'tad401:500m','Bin7':'tad501:600m','Bin8':'tad601:700m',
            'Bin9':'tad701:800m','Bin10':'tad801:900m','Bin11':'tad901:1000m',
            'Bin12':'tad1001:1200m','Bin13':'tad1201:1400m','Bin14':'tad1401:4015m'},
           'TAD25-400_1.0':{'Bin1':'tad-80:25m','Bin2':'tad026:50m',
            'Bin3':'tad051:75m','Bin4':'tad76:100m','Bin5':'tad101:125m',
            'Bin6':'tad126:150m','Bin7':'tad151:175m','Bin8':'tad176:200m',
            'Bin9':'tad201:225m','Bin10':'tad226:250m','Bin11':'tad251:275m',
            'Bin12':'tad276:300m','Bin13':'tad301:400m','Bin14':'tad401:4015m'},
           'TAT6-60_2C':{'Bin1':'tat-40:6C','Bin2':'tat06.1:8C','Bin3':'tat08.1:10C',
            'Bin4':'tat10.1:12C','Bin5':'tat12.1:14C','Bin6':'tat14.1:16C','Bin7':'tat16.1:18C',
            'Bin8':'tat18.1:20C','Bin9':'tat20.1:22C','Bin10':'tat22.1:24C','Bin11':'tat24.1:26C',
            'Bin12':'tat26.1:60C'},
           'TAT10-60_2C':{'Bin1':'tat-40:10C','Bin2':'tat10.1:12C','Bin3':'tat12.1:14C',
            'Bin4':'tat14.1:16C','Bin5':'tat16.1:18C','Bin6':'tat18.1:20C','Bin7':'tat20.1:22C',
            'Bin8':'tat22.1:24C','Bin9':'tat24.1:26C','Bin10':'tat26.1:28C','Bin11':'tat28.1:30C',
            'Bin12':'tat30.1:60C'},
           'TAT-2-50_3C':{'Bin1':'tat-40:-2C','Bin2':'tat-02.1:0C','Bin3':'tat00.1:3C',
            'Bin4':'tat03.1:6C','Bin5':'tat06.1:9C','Bin6':'tat09.1:12C','Bin7':'tat12.1:15C',
            'Bin8':'tat15.1:18C','Bin9':'tat18.1:21C','Bin10':'tat21.1:24C','Bin11':'tat24.1:27C',
            'Bin12':'tat27.1:30C','Bin13':'tat30.1:33C','Bin14':'tat33.1:50C'}
            }

#===============================================================================
""" LETS make a whole Telonics CLASS with methods and properties!
"""


# Telonics csv reports
           # {parameter_id : Column}

# Used in data_tamer to exclude WC tags
tel_tagtypes = [47, 48, 49, 51, 52, 53, 54, 55]
# 47    = 2015 rdw640
# 48,49 = 2016 rdw665
# 51    = 2017 rdw665 before leak found
# 52    = 2017 rdw665 no depth sensor
# 53    = 2017 rdw665 repaired leak
# 54    = 2018 rdw665
# 55    = 2019 rdw665

# used in data_tamer to parse different report formats
tel_passes   = ['Acquisition Time',
                'Acquisition Start Time',
                'Argos Location Class',
                'Argos NOPC',
                'Argos Error Radius',
                'Argos Semi-Major Error',
                'Argos Semi-Minor Error',
                'Argos Error Orientation',
                'Argos GDOP',
                'Argos Latitude',
                'Argos Longitude',
                'Argos Altitude',
                'Receive Time',
                'Satellite Name',
                'Repetition Count'] # Should == count of messages
# For all rows EXCEPT dive data:
#   Acquisition Time == Acquisition Start Time == Receive Time
#......................................................
tel_util_47  = ['Receive Time',
                'Satellite Name',
                'Temperature',
                'Transmission Count',
                'Battery Voltage T3',
                'Transmission Efficiency Indicator',
                'Argos Signal Strength',
                'Saltwater Failsafe',
                'Error']

tel_dive_47  = ['Dive Start Time',
                'Dive Duration',
                'Receive Time',
                'Satellite Name']

#......................................................
tel_util_48  = ['Receive Time',
                'Satellite Name',
                'Repetition Count',
                'Argos Signal Strength',
                'Low Voltage',
                'Error']

tel_dive_48  = ['Dive Start Time',  # Weekday format
                'Dive Duration',
                'Dive Depth',
                'Dive Lunge Count',
                'Receive Time',
                'Satellite Name']
#......................................................
# *** Try using Dict to make parse_csv more generic?
tel_dr47 = {'Receive Time':19,'Dive Start Time':12}
tel_dr48 = {'Receive Time':17,'Dive Start Time':12}
tel_dr51 = {'Receive Time':22,'Dive Start Time':12} # 51,53,54,55
tel_dr52 = {'Receive Time':21,'Dive Start Time':12} # 52=DUR+ (no depth)
#......................................................
tel_util_51  = ['Temperature',
                'Battery Voltage T3',
                'Transmission Efficiency Indicator',
                'Lunge Detection Mean',
                'Lunge Detection Stdev',
                'Satellite Uplink',
                'Receive Time',
                'Satellite Name',
                'Repetition Count',     # drop from table
                'Argos Signal Strength',
                'Error']

# Low Voltage occurs as part of dive headers, not with util!!
# Consider it another kind of util msg

tel_dhdr_51  = ['Satellite Uplink', # == "Hit"
                'Receive Time',     # == Dive Receive Times
                'Satellite Name',   #
                'Repetition Count', # == 1
                'Argos Signal Strength',
                'Low Voltage',
                'Error']

tel_dive_51  = ['Dive Start Time',  # Weekday format
                'Dive Duration',
                'Dive Depth',
                'Dive Lunge Count',
                'Receive Time',
                'Satellite Name']

tel_dive_52  = ['Dive Start Time',  # Weekday format
                'Dive Duration',
                'Dive Lunge Count',
                'Receive Time',
                'Satellite Name']

#......................................................

""" BARB
New definitions and short names for modified tags
DM, DUR,  ???
"""
# Used by dev_message_etl
tel_status =    {'acquisition':'Acquisition Time',
                'error_flag'  :'Error',
                'low_voltage' :'Low Voltage',
                'lunge_mean'  :'Lunge Detection Mean',
                'lunge_stdev' :'Lunge Detection Stdev',
                'recieve_time':'Receive Time',
                'sws_fail'    :'Saltwater Failsafe',
                'temperature' :'Temperature',
                'transmits'   :'Transmission Count',
                'tx_eff'      :'Transmission Efficiency Indicator',
                'tx_voltage'  :'Battery Voltage T3'}

tel_dives =     {'dive_start' :'Dive Start Time',
                'dive_dur'    :'Dive Duration',
                'depth'       :'Dive Depth',
                'lunge_count' :'Dive Lunge Count',
                'recieve_time':'Receive Time'}

tel_counter = {}
#-------------------------------------------------------------------------------


# message_type: File path\\name
msg_files= {
  '2007MX':[(3,'Mar_BCS_Sperm\\WC_Tx_Solved\\All-FastGPS.csv'),                 ##
            (0,'Mar_BCS_Sperm\\WC_Tx_Solved\\All-Status.csv'),                  ##
            (1,'Mar_BCS_Sperm\\WC_Tx_Solved\\All-Behavior.csv'),                ##
            (3,'Mar_BCS_Sperm\\WC_Recovered\\All-FastGPS.csv'),                 ##
            (0,'Mar_BCS_Sperm\\WC_Recovered\\All-Status.csv'),                  ##
            (1,'Mar_BCS_Sperm\\WC_Recovered\\All-Behavior.csv')                 ##
            ],
  '2008MX':[(3,'Apr_BCS_Sperm\\WC_Tx_Solved\\Apr\\AllTags-TxGPS-FastGPS.csv'),  ##
            (0,'Apr_BCS_Sperm\\WC_Tx_Solved\\Apr\\AllTags-TxGPS-Status.csv'),   ##
            (1,'Apr_BCS_Sperm\\WC_Tx_Solved\\Apr\\AllTags-TxGPS-Behavior.csv'), ##
            (3,'Apr_BCS_Sperm\\WC_Recovered\\Apr\\All-FastGPS.csv'),            ##
            (0,'Apr_BCS_Sperm\\WC_Recovered\\Apr\\All-Status.csv'),             ##
            (1,'Apr_BCS_Sperm\\WC_Recovered\\Apr\\All-Behavior.csv'),           ##
            (3,'Apr_BCS_Sperm\\WC_Recovered\\Jun\\All-FastGPS.csv'),            ##
            (0,'Apr_BCS_Sperm\\WC_Recovered\\Jun\\All-Status.csv'),             ##
            (1,'Apr_BCS_Sperm\\WC_Recovered\\Jun\\All-Behavior.csv')            ##
            ],
  '2009OR':[(0,'Aug_OR_Gray\\WC_Tx_Solved\\Gray09All-Status.csv'),              ##
            (2,'Aug_OR_Gray\\WC_Tx_Solved\\Gray09All-Histos.csv')               ##
            ],
  '2010RU':[(0,'Sep_RUS_Gray\\WC_Tx_Solved\\All-Status.csv'),                   ##
            (2,'Sep_RUS_Gray\\WC_Tx_Solved\\All-Histos.csv')                    ##
            ],
  '2011GoM':[(3,'Jul_GOM_Sperm\\WC_Tx_Solved\\MK10\\All-FastGPS.csv'),          ##
            (0,'Jul_GOM_Sperm\\WC_Tx_Solved\\MK10\\All-Status.csv'),            ##
            (1,'Jul_GOM_Sperm\\WC_Tx_Solved\\MK10\\All-Behavior.csv'),          ##
            (2,'Jul_GOM_Sperm\\WC_Tx_Solved\\MK10\\All-Histos.csv'),            ##
            (0,'Jul_GOM_Sperm\\WC_Tx_Solved\\SPOT5\\All-Status.csv'),           ##
            (2,'Jul_GOM_Sperm\\WC_Tx_Solved\\SPOT5\\All-Histos.csv'),           ##
            (3,'Jul_GOM_Sperm\\WC_Recovered\\4173\\4173-FastGPS.csv'),          ##
            (0,'Jul_GOM_Sperm\\WC_Recovered\\4173\\4173-Status.csv'),           ##
            (1,'Jul_GOM_Sperm\\WC_Recovered\\4173\\4173-Behavior.csv'),         ##
            (2,'Jul_GOM_Sperm\\WC_Recovered\\4173\\4173-Histos.csv')            ##
            ],
  '2011RU':[(0,'Aug_RUS_Gray\\WC_Tx_Solved\\All-Status.csv'),                   ##
            (2,'Aug_RUS_Gray\\WC_Tx_Solved\\All-Histos.csv')                    ##
            ],
  '2012GoM':[(0,'Aug_GOM_Sperm\\WC_Tx_Solved\\All-Status.csv'),                 ##
            (2,'Aug_GOM_Sperm\\WC_Tx_Solved\\All-Histos.csv')                   ##
            ],
  '2012PNW':[(0,'Oct_OR_Gray\\WC_Tx_Solved\\All-Status.csv'),                   ##
            (2,'Oct_OR_Gray\\WC_Tx_Solved\\All-Histos.csv')                     ##
            ],
  '2013GoM':[(0,'Jul_GOM_Sperm\\WC_Tx_Solved\\SPOT5\\All-Status.csv'),          ##No FastLoc received
            (2,'Jul_GOM_Sperm\\WC_Tx_Solved\\SPOT5\\All-Histos.csv'),           ##
            (0,'Jul_GOM_Sperm\\WC_Tx_Solved\\MK10\\All-Status.csv'),            ## 838 Only, no Histos
            (1,'Jul_GOM_Sperm\\WC_Tx_Solved\\MK10\\All-Behavior.csv'),          ##
            (3,'Jul_GOM_Sperm\\WC_Recovered\\All-FastGPS.csv'),                 ## Recalc apr2019
            (0,'Jul_GOM_Sperm\\WC_Recovered\\All-Status.csv'),                  ##
            (1,'Jul_GOM_Sperm\\WC_Recovered\\All-Behavior.csv'),                ##
            (2,'Jul_GOM_Sperm\\WC_Recovered\\All-Histos.csv')                   ##
            ],
  '2013PNW':[(0,'Oct_PNW_Gray\\WC_Tx_Solved\\All-Status.csv'),                  ##
            (2,'Oct_PNW_Gray\\WC_Tx_Solved\\All-Histos.csv')                    ##
            ],
  '2014CA':[(0,'Aug_CA_Blue_Fin\\WC_Tx_Solved\\SPOT5\\All-Status.csv'),         ##
            (2,'Aug_CA_Blue_Fin\\WC_Tx_Solved\\SPOT5\\All-Histos.csv'),         ##
            (3,'Aug_CA_Blue_Fin\\WC_Tx_Solved\\MK10\\5790-FastGPS.csv'),        ##
            (0,'Aug_CA_Blue_Fin\\WC_Tx_Solved\\MK10\\5790-Status.csv'),         ##
            (1,'Aug_CA_Blue_Fin\\WC_Tx_Solved\\MK10\\5790-Behavior.csv'),       ##
            (2,'Aug_CA_Blue_Fin\\WC_Tx_Solved\\MK10\\5790-Histos.csv'),         ##
            (3,'Aug_CA_Blue_Fin\\WC_Recovered\\All-FastGPS.csv'),               ##
            (0,'Aug_CA_Blue_Fin\\WC_Recovered\\All-Status.csv'),                ##
            (1,'Aug_CA_Blue_Fin\\WC_Recovered\\All-Behavior.csv'),              ##
            (2,'Aug_CA_Blue_Fin\\WC_Recovered\\All-Histos.csv')                 ##
            ],
  '2014AK':[(0,'Nov_AK_Hump\\WC_Tx_Solved\\All-Status.csv'),                    ##
            (2,'Nov_AK_Hump\\WC_Tx_Solved\\All-Histos.csv')                     ##
            ],
  '2015HI':[(0,'Jan_HI_Hump\\WC_Tx_Solved\\All-Status.csv'),                    ##
            (2,'Jan_HI_Hump\\WC_Tx_Solved\\All-Histos.csv')                     ##
            ],
  '2015CA':[(0,'Jul_CA_Blue_Fin\\WC_Tx_Solved\\SPOT5\\All-Status.csv'),         ##
            (2,'Jul_CA_Blue_Fin\\WC_Tx_Solved\\SPOT5\\All-Histos.csv'),         ##
            (3,'Jul_CA_Blue_Fin\\WC_Tx_Solved\\MK10\\All-FastGPS.csv'),         ##
            (0,'Jul_CA_Blue_Fin\\WC_Tx_Solved\\MK10\\All-Status.csv'),          ##
            (1,'Jul_CA_Blue_Fin\\WC_Tx_Solved\\MK10\\All-Behavior.csv'),        ##
            (2,'Jul_CA_Blue_Fin\\WC_Tx_Solved\\MK10\\All-Histos.csv'),          ##
            (3,'Jul_CA_Blue_Fin\\WC_Recovered\\All-FastGPS.csv'),               ##
            (0,'Jul_CA_Blue_Fin\\WC_Recovered\\All-Status.csv'),                ##
            (1,'Jul_CA_Blue_Fin\\WC_Recovered\\All-Behavior.csv'),              ##
            (2,'Jul_CA_Blue_Fin\\WC_Recovered\\All-Histos.csv'),                ##
            (3,'Jul_CA_Blue_Fin\\WC_Recovered\\838\\838-FastGPS.csv')           ##
            ],
  '2015AK':[(0,'Nov_AK_Hump\\WC_Tx_Solved\\All-Status.csv'),                    ##
            (2,'Nov_AK_Hump\\WC_Tx_Solved\\All-Histos.csv'),                    ##
            (4,'Nov_AK_Hump\\Tel_Tx_Solved\\All-Status.csv'),                   ##
            (5,'Nov_AK_Hump\\Tel_Tx_Solved\\All-Dives.csv')                     ## Re-run Jan2019 -weird Dive times fixed
            ],
  '2016CA':[(0,'Jul_CA_Blue_Fin\\WC_Tx_Solved\\SPOT6\\All-Status.csv'),         ##
            (2,'Jul_CA_Blue_Fin\\WC_Tx_Solved\\SPOT6\\All-Histos.csv'),         ##
            (5,'Jul_CA_Blue_Fin\\Tel_Tx_Solved\\All-Dives.csv')                 ##
            ],
  '2016OR':[(4,'Sep_OR_Hump\\Tel_Tx_Solved\\All-Status.csv'),                   ##
            (5,'Sep_OR_Hump\\Tel_Tx_Solved\\All-Dives.csv')                     ##
             ],
  '2017CA':[(0,'Jul_CA_Blue_Fin_Hump\\WC_Tx_Solved\All-Status.csv'),            ##
            (2,'Jul_CA_Blue_Fin_Hump\\WC_Tx_Solved\\All-Histos.csv'),           ##
            (4,'Jul_CA_Blue_Fin_Hump\\Tel_Tx_Solved\\All-Status.csv'),          ##
            (5,'Jul_CA_Blue_Fin_Hump\\Tel_Tx_Solved\\All-Dives.csv')            ##
             ],
  '2017OR': [(5,'Sep_OR_Hump\\Tel_Tx_Solved\\All-Dives.csv')                    ##
             ],
  '2018HI': [(4,'Mar_HI_Hump\\Tel_Tx_Solved\\All-Status.csv'),                  ##
            (5,'Mar_HI_Hump\\Tel_Tx_Solved\\All-Dives.csv')                     ## (# means loaded)
            ],
  '2018PNW':[(3,'Aug_PNW_Hump\\WC_Tx_Solved\\4177\\4177-FastGPS.csv'),          ##
             (0,'Aug_PNW_Hump\\WC_Tx_Solved\\4177\\4177-Status.csv'),           ##
             (1,'Aug_PNW_Hump\\WC_Tx_Solved\\4177\\4177-Behavior.csv'),         ##
             (2,'Aug_PNW_Hump\\WC_Tx_Solved\\4177\\4177-Histos.csv'),           ##
             (0,'Aug_PNW_Hump\\WC_Tx_Solved\\5882\\5882-Status.csv'),           ##
             (2,'Aug_PNW_Hump\\WC_Tx_Solved\\5882\\5882-Histos.csv'),            ##
             (4,'Aug_PNW_Hump\\Tel_Tx_Solved\\All-Status.csv'),                 ##
             (5,'Aug_PNW_Hump\\Tel_Tx_Solved\\DM-Dives.csv'),                   ##
             (5,'Aug_PNW_Hump\\Tel_Tx_Solved\\DUR-Dives.csv')                   ##
             ],
  '2019HI':[(4,'Mar_HI_Hump\\Tel_Tx_Solved\\All-Status.csv'),                   ##
            (5,'Mar_HI_Hump\\Tel_Tx_Solved\\All-Dives.csv'),                    ##
            (4,'Mar_HI_Hump\\Tel_Tx_Solved\\Mote-Status.csv'),                  ##
            (5,'Mar_HI_Hump\\Tel_Tx_Solved\\Mote-Dives.csv')                    ##                           #
             ]
    }



# Telonics TDC  reports
#===============================================================================





"""         'broken_link'       :  'BrokenLink',
            'depth'             :  'Depth',
            'max_depth'         :  'MaxDepth',
            'zero_depth_offset' :  'ZeroDepthOffset',
            'light_level'       :  'LightLevel',
            'release_type'      :  'ReleaseType',
            'release_time'      :  'ReleaseTime',
            'initially_broken'  :  'InitiallyBroken',
            'burn_minutes'      :  'BurnMinutes',
            'release_depth'     :  'ReleaseDepth',
            'fastgps_power'     :  'FastGPSPower',
            'twic_power'        :  'TWICPower',
            'power_limit'       :  'PowerLimit' }

histo_limits = {'TAD20-1400_0.5':['20','100','200','300','400','500','600','700','800','900','1000','1200','1400','2007.5'],
                'TAD20-1400_1.0':['20','100','200','300','400','500','600','700','800','900','1000','1200','1400','4015'],
                'TAD25-400_1.0' :['25','50','75','100','125','150','175','200','225','250','275','300','400','4015'],
                'TAT6-60_2C'    :['6','8','10','12','14','16','18','20','22','24','26','60'],
                'TAT10-60_2C'   :['10','12','14','16','18','20','22','24','26','28','30','60'],
                'TAT-2-50_3C'   :['-2','0','3','6','9','12','15','18','21','24','27','30','33','50','164.75']
                }

2007-2008 = 'DeployID,Ptt,Instr,ReceptionDateTime,                      LocationQuality,Latitude,Longitude,     HauledOut,BrokenThermistor,BrokenLink,Transmits,Voltage,                                    Temperature,Depth,MaxDepth,PrematureRelease,                                 ReleaseTime,                            ReleaseDepth,Time Offset,PowerUsed,PowerLimit',
2009-2011? ??= 'DeployID,Ptt,DepthSensor,Instr,SW,RTC,Received,Time Offset,LocationQuality,Latitude,Longitude,Type,HauledOut,BrokenThermistor,BrokenLink,Transmits,BattVoltage,TransmitVoltage,TransmitCurrent,Temperature,Depth,MaxDepth,ZeroDepthOffset,LightLevel,NoDawnDusk,ReleaseType,ReleaseTime,InitiallyBroken,BurnMinutes,ReleaseDepth,FastGPSPower,TWICPower,PowerLimit,MinWetDry,MaxWetDry,WetDryThreshold,StatusWord,TransmitPower,Resets',
2013-2015?? = 'DeployID,Ptt,DepthSensor,Instr,SW,RTC,Received,Time Offset,LocationQuality,Latitude,Longitude,Type,HauledOut,BrokenThermistor,BrokenLink,Transmits,BattVoltage,TransmitVoltage,TransmitCurrent,Temperature,Depth,MaxDepth,ZeroDepthOffset,LightLevel,NoDawnDusk,ReleaseType,ReleaseTime,InitiallyBroken,BurnMinutes,ReleaseDepth,FastGPSPower,TWICPower,PowerLimit,MinWetDry,MaxWetDry,WetDryThreshold,StatusWord,TransmitPower,Resets,PreReleaseTilt,PreReleaseTiltSd,PreReleaseTiltCount,XmitQueue',

wcbehave_0 = 'DeployID,Ptt,DepthSensor,Source,Instr,Count,Start,End,What,Number,Shape,DepthMin,DepthMax,DurationMin,DurationMax,Number,Shape,DepthMin,DepthMax,DurationMin,DurationMax,Number,Shape,DepthMin,DepthMax,DurationMin,DurationMax,Shallow,Deep'

wchistos_0 = 'DeployID,Ptt,DepthSensor,Source,Instr,HistType,Date,Time Offset,Count,BadTherm,LocationQuality,Latitude,Longitude,NumBins,Sum,Bin1,Bin2,Bin3,Bin4,Bin5,Bin6,Bin7,Bin8,Bin9,Bin10,Bin11,Bin12,Bin13,Bin14,Bin15,Bin16,Bin17,Bin18,Bin19,Bin20,Bin21,Bin22,Bin23,Bin24,Bin25,Bin26,Bin27,Bin28,Bin29,Bin30,Bin31,Bin32,Bin33,Bin34,Bin35,Bin36,Bin37,Bin38,Bin39,Bin40,Bin41,Bin42,Bin43,Bin44,Bin45,Bin46,Bin47,Bin48,Bin49,Bin50,Bin51,Bin52,Bin53,Bin54,Bin55,Bin56,Bin57,Bin58,Bin59,Bin60,Bin61,Bin62,Bin63,Bin64,Bin65,Bin66,Bin67,Bin68,Bin69,Bin70,Bin71,Bin72'

wcfstgps_0 = 'Name,Day,Time,Count,Time Offset,LocNumber,Failures,Hauled Out,Satellites,                         Latitude,Longitude,Height,Bad Sats,Residual,Time Error,TWIC Power,Fastloc Power,Noise,Range Bits,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR'
wcfstgps_1 = 'Name,Day,Time,Count,Time Offset,LocNumber,Failures,Hauled Out,Satellites,InitLat,InitLon,InitTime,Latitude,Longitude,Height,Bad Sats,Residual,Time Error,TWIC Power,Fastloc Power,Noise,Range Bits,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR,Id,Range,Signal,Doppler,CNR'

import re
d_regex = {'blank': re.compile("\n"),
           'empty': re.compile("^,+"),
           'skip_0': re.compile("^;\sUnless\s.*"),
           'skip_1': re.compile("^;\sSN\s.*"),
           'wcstatus_0': re.compile("^(DeployID,Ptt,Instr,ReceptionDateTime).*(PowerLimit)$"),
           'wcstatus_1': re.compile("^(DeployID,Ptt,DepthSensor,Instr,SW).*(Resets)$"),
           'wcstatus_2': re.compile("^(DeployID,Ptt,DepthSensor,Instr,SW).*(XmitQueue)$"),
           'wcbehave_0': re.compile("^(DeployID,Ptt,DepthSensor,Source,Instr).*(Deep)$"),
           'wchistos_0': re.compile("^(DeployID,Ptt,DepthSensor,Source,Instr,HistType).*(Bin\d2)$"),
           'wcfstgps_0': re.compile("^Name,Day,Time,Count,Time Offset,LocNumber,Failures,Hauled Out,Satellites,Latitude.*"),
           'wcfstgps_1': re.compile("^Name,Day,Time,Count,Time Offset,LocNumber,Failures,Hauled Out,Satellites,InitLat.*"),
           }



"""