#Eric Sobolewski
#8/6/2016
#
#

import sqlite3
import matplotlib
import pandas
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')



class datascience_utilities:


    deeta=[]
    quants=[]
    def __init__(self, database):
        self.conn = sqlite3.connect(database)

    def read_all_data(self):
        global deeta, quants
        deeta=pandas.read_sql('SELECT cab_id, dropoff_time, ride_distance, tip_amount, \
                      pickup_time, dropoff_long, dropoff_lat, trip_length_minutes  \
                      FROM cabtrip\
                      where \
                      pickup_long!=0 \
                      and pickup_lat!=0 \
                      and dropoff_long!=0 \
                      and dropoff_lat!=0\
                      and ride_distance!=0\
                      and pickup_time<>dropoff_time\
                      LIMIT 100000000',
                      self.conn, index_col=None, coerce_float=True, \
                      params=None, parse_dates=None, columns=None,\
                      chunksize=None)
        
        deeta.dropoff_time=deeta.dropoff_time.astype('datetime64[ns]')
        deeta.pickup_time=deeta.pickup_time.astype('datetime64[ns]')

        deeta.ridetime=deeta.dropoff_time-deeta.pickup_time
        deeta['ridetime']=deeta.dropoff_time-deeta.pickup_time

        time = pandas.DatetimeIndex(deeta['ridetime'])
        deeta['ridetime_m']=time.hour * 60 + time.minute
        deeta['avg_speed'] = deeta.ride_distance/deeta['ridetime_m']*60

        quants = self.get_speed_index_quantiles()

        '''
        deeta['congestion_index'] = 1
        deeta.congestion_index[(deeta.avg_speed < quants[0.4])&(deeta.avg_speed >= quants[0.2])] = 2
        deeta.congestion_index[(deeta.avg_speed < quants[0.6])&(deeta.avg_speed >= quants[0.4])] = 3
        deeta.congestion_index[(deeta.avg_speed < quants[0.8])&(deeta.avg_speed >= quants[0.6])] = 4
        deeta.congestion_index[(deeta.avg_speed >= quants[0.8])] = 5
        '''
        return deeta
        
        
    def get_speed_index_quantiles(self):
        global quants
        # Hardcoding the quantiles
        quants=deeta[(deeta.avg_speed<50) & (deeta.ridetime_m>1)].avg_speed.quantile([0.2, 0.4, 0.6, 0.8])
        return quants

    def get_congestion_index(self, key):
        avgspeed = deeta.avg_speed[deeta.cab_id == key].any()
        if (avgspeed < quants[0.2]):
            return 1
        if (avgspeed < quants[0.4]):
            return 2
        if (avgspeed < quants[0.6]):
            return 3
        if (avgspeed < quants[0.8]):
            return 4
        if (avgspeed >= quants[0.8]):
            return 5
                
        

        
        
