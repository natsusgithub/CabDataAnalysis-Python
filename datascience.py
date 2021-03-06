# datascience class to show plots/graphs and perform some analysis
# this class is used when importing the data.

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

        return deeta
        
        
    def get_speed_index_quantiles(self):
        global quants

        quants=deeta[(deeta.avg_speed<50) & (deeta.ridetime_m>1)].avg_speed.quantile([0.2, 0.4, 0.6, 0.8])
        return quants

    def get_plot_speed(self):

        deeta.describe()

        deeta[(deeta.avg_speed<50) & (deeta.ridetime_m>1)].avg_speed.hist(bins=50, color='r')
        plt.show()
        deeta[(deeta.avg_speed<50) & (deeta.ridetime_m>1)].describe()

        deeta[(deeta.avg_speed<50) & (deeta.ridetime_m>1) & (deeta.ridetime_m<80)].ridetime_m.hist(bins=40, color='r')
        plt.show()
        deeta[(deeta.avg_speed<50) & (deeta.ridetime_m>1) & (deeta.ridetime_m<80)].describe()
        
        deeta[(deeta.avg_speed<50) & (deeta.ridetime_m>1)].avg_speed.hist(bins=50, color='r')
        plt.axvline(quants[0.2], color='b',linewidth=3)
        plt.axvline(quants[0.4], color='b', linewidth=3)
        plt.axvline(quants[0.6], color='b', linewidth=3)
        plt.axvline(quants[0.8], color='b', linewidth=3)
        plt.show()

                
        

        
        
