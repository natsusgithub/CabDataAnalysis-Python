#Eric Sobolewski
#8/6/2016
#
#
import sqlite3
import pandas
import matplotlib
import matplotlib.pyplot as plt
matplotlib.style.use('ggplot')

conn=sqlite3.connect('cabdata.db')
#c=conn.cursor()

#frame=c.execute('SELECT * FROM cab')
##for row in c.execute('SELECT count(*) FROM cabtrip where \
##    pickup_long=0 \
##    or pickup_lat=0 \
##    or dropoff_long=0 \
##    or dropoff_lat=0'):
##    print(row)

##for row in c.execute('SELECT count(id) FROM cabtrip'):
##    print(row)
##
##for row in c.execute('SELECT MIN(pickup_time) FROM cabtrip'):
##    print(row)
##
##for row in c.execute('SELECT dropoff_time - pickup_time FROM cabtrip LIMIT 20'):
##    print(row)
deeta=[]
deeta=pandas.read_sql('SELECT id, dropoff_time, ride_distance,\
                      pickup_time FROM cabtrip\
                      where \
                      pickup_long!=0 \
                      and pickup_lat!=0 \
                      and dropoff_long!=0 \
                      and dropoff_lat!=0\
                      and ride_distance!=0\
                      and pickup_time<>dropoff_time\
                      LIMIT 100000000',
                      conn, index_col=None, coerce_float=True, \
                      params=None, parse_dates=None, columns=None,\
                      chunksize=None)

deeta.dropoff_time=deeta.dropoff_time.astype('datetime64[ns]')
deeta.pickup_time=deeta.pickup_time.astype('datetime64[ns]')

deeta.ridetime=deeta.dropoff_time-deeta.pickup_time
deeta['ridetime']=deeta.dropoff_time-deeta.pickup_time

time = pandas.DatetimeIndex(deeta['ridetime'])
deeta['ridetime_m']=time.hour * 60 + time.minute
deeta=deeta[deeta.ridetime_m !=0]
deeta['avg_speed']= deeta.ride_distance/deeta.ridetime_m*60

deeta.avg_speed.mean()
deeta.avg_speed.std()
deeta.avg_speed.max()
deeta.avg_speed.min()

##deeta['cost_per_min']=COST/deeta.ridetime_m
##deeta['tip_per_min']=TIP/deeta.ridetime_m
##deeta['cost_per_m']=COST/deeta.ride_distance  
##deeta['cost_per_m']=TIP/deeta.ridetime_m
##
#
#Save the data, or DON'T (TAKES A WHILE)
#
cols=['id','ridetime_m','avg_speed']
deeta.to_csv('deeta.csv', sep=',',columns=cols, index=False, header=True)
'''

deeta.ridetime=deeta.ridetime.astype('str')
deeta['ridetime'].str.split(':').apply(lambda x: int(x[0]) * 60 + int(x[1]))

'''
