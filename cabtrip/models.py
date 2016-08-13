#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import time
import csv
import sys

import log
import datascience
import pandas

from peewee import Model, SqliteDatabase, InsertQuery, DecimalField, PrimaryKeyField, \
                   IntegerField, CharField, DoubleField, DateTimeField, fn

from matplotlib.path import Path

from . import config


dbname = "cabdata.db"
db = None
logfile = log.Log("cabtrip.log")
deeta = []
# initializing a sqllitedb
def init_database():
    global db
    if db is not None:
        return db
    db = SqliteDatabase(dbname)
    return db

class BaseModel(Model):
    class Meta:
        database = init_database()

    @classmethod
    def get_all(self):
        results = [m for m in self.select().dicts()]
        return results

class NeighborhoodCoordinates(BaseModel):
    coordinates_id = PrimaryKeyField(primary_key=True)
    neighborhood_id = IntegerField()
    latitude = DoubleField()
    longitude = DoubleField()
    

class Neighborhood(BaseModel):
    neighborhood_id = PrimaryKeyField(primary_key=True)
    boro_name = CharField()
    neighborhood_name = CharField()
    
    
class CabTrip(BaseModel):
    cab_id = IntegerField(primary_key=True)
    pickup_time = DateTimeField()
    pickup_long = DoubleField()
    pickup_lat = DoubleField()
    pickup_neighborhood = CharField(null=True)
    
    dropoff_time = DateTimeField()
    dropoff_long = DoubleField()
    dropoff_lat = DoubleField()
    dropoff_neighborhood = CharField(null=True)
    
    ride_distance = DecimalField()
    num_passenger = IntegerField()
    payment_type = IntegerField()
    tip_amount = DoubleField()
    fare_amount = DoubleField()

    # calculated fields
    trip_length_minutes = DoubleField()
    avg_speed = DoubleField()
    congestion_index = IntegerField(null=True)
	
    @classmethod
    def get_all(self):
        query = (CabTrip.select().dicts())

        cabs = []
        for p in query:
            cabs.append(p)

        return cabs

    @classmethod
    def build_where_statement(self, neighborhoodtype, ispickup):
        datatype = "dropoff"
        neighborhooddatatype = "dropoff"
        if (ispickup):
            datatype = "pickup"
            
        if (neighborhoodtype == 'Pick-up'):
            neighborhooddatatype = "pickup"

        return('WHERE {0}_time <= ? and {0}_time >= ? and {1}_neighborhood like ?'.format(datatype, neighborhooddatatype))
    
    @classmethod
    def get_records(self, neighborhood, neighborhoodtype, starttime, endtime, ispickup):
        query = None
        cabs = []
        datatype = "dropoff"
        if (ispickup):
            datatype = "pickup"
            
        
        #build the sql statement.  although we are doing string format, we are controlling the type of data that can be put there
        #to avoid sql injection.  the expressions does use parameterized sql
        sql = "select {0}_lat as latitude, {0}_long as longitude, congestion_index FROM cabtrip {1}".format(datatype, self.build_where_statement(neighborhoodtype, ispickup))
        query = CabTrip.raw(sql, endtime, starttime, '%{0}%'.format(neighborhood)).dicts()
        for p in query:
            cabs.append(p)


        # attempting to convert a dataframe from pandas to a dictionary that we can use.  not having much luck...            
        '''
        columns = ['cab_id', 'dropoff_lat', 'dropoff_long', 'congestion_index']

        
        
        test = (pandas
                .DataFrame((deeta.ix[(deeta['dropoff_time'] >= starttime) & \
                         (deeta['dropoff_time'] <= endtime)]), \
                           columns = columns))

        area_dict = dict(zip(test.dropoff_lat, test.dropoff_long, test.congestion_index))

        print(area_dict)
        #print(test.set_index('cab_id').to_dict())
        #print(test)
        print(len(test))
        print(len(query))
        '''
        return cabs

    @classmethod
    def get_average_time(self, startneighborhood, endneighborhood, starttime, endtime):
        query = None

        #build the sql statement.  although we are doing string format, we are controlling the type of data that can be put there
        #to avoid sql injection.  the expressions does use parameterized sql
        sql = "select avg(trip_length_minutes) FROM cabtrip WHERE pickup_neighborhood == 'Midtown' " \
              "and dropoff_neighborhood == 'Upper West Side' and pickup_time <= ? and pickup_time >= ?"
        average_time = CabTrip.raw(sql, endtime, starttime).scalar()

        if (average_time == None):
            return 0
        return average_time

    @classmethod
    def get_average_congestion(self, neighborhood, neighborhoodtype, starttime, endtime, ispickup):
        query = None

        #build the sql statement.  although we are doing string format, we are controlling the type of data that can be put there
        #to avoid sql injection.  the expressions does use parameterized sql
        sql = "select avg(congestion_index - 1) / 4 FROM cabtrip {0}".format(self.build_where_statement(neighborhoodtype, ispickup))
        congestion = CabTrip.raw(sql, endtime, starttime, '%{0}%'.format(neighborhood)).scalar()

        if (congestion == None):
            return 0
        return congestion

    @classmethod
    def get_average_tip(self, neighborhood, neighborhoodtype, starttime, endtime, ispickup):
        query = None

        #build the sql statement.  although we are doing string format, we are controlling the type of data that can be put there
        #to avoid sql injection.  the expressions does use parameterized sql
        sql = "select avg(tip_amount) FROM cabtrip {0} and payment_type == 1".format(self.build_where_statement(neighborhoodtype, ispickup))
        tipamount = CabTrip.raw(sql, endtime, starttime, '%{0}%'.format(neighborhood)).scalar()

        if (tipamount == None):
            return 0
        
        return tipamount

    @classmethod
    def get_tip_percentage(self, neighborhood, neighborhoodtype, starttime, endtime, ispickup):
        query = None

        #build the sql statement.  although we are doing string format, we are controlling the type of data that can be put there
        #to avoid sql injection.  the expressions does use parameterized sql
        sql = "select avg(tip_amount / fare_amount) FROM cabtrip {0} and payment_type == 1".format(self.build_where_statement(neighborhoodtype, ispickup))
        tippercentage = CabTrip.raw(sql, endtime, starttime, '%{0}%'.format(neighborhood)).scalar()

        if (tippercentage == None):
            return 0
        
        return tippercentage

    # hardcode neighborlist
    @classmethod
    def get_neighborhood(self):
        return [{'neighbor':"Financial District"},
                {'neighbor':"Lower Manhattan"},
                {'neighbor':"Midtown"},
                {'neighbor':"Upper West Side"},
                {'neighbor':"Upper East Side"},
                {'neighbor':"Harlem"},
                {'neighbor':"Upper Manhattan"}] 
# helper to display a progress bar
def __progressbar(i):

        if (not logfile.silent):
            loadicon = "|" # potentially have an animated icon.  static for now

            # write to the same row
            sys.stdout.write('\r')
            sys.stdout.write(loadicon + " " + str(i) + " rows inserted...")
            sys.stdout.flush()
        

#converts string formatted in 1/1/2001 0:00
def convert_str_to_date(item):
    #retdate = datetime.now()
    try:
        return datetime.strptime(item, "%m/%d/%Y %H:%M")
       
    except ValueError:
        # try a different format 2001/1/1 00:00:00
        return datetime.strptime(item, "%Y-%m-%d %H:%M:%S")
    #return retdate

def update_neighborhood():
    
    index = 0
    for n in Neighborhood.select():
        __progressbar(index)
        (CabTrip
        .update(pickup_neighborhood = n.zipcode)
        .where(
            CabTrip.pickup_neighborhood.is_null(True),
            fn.Round(CabTrip.pickup_lat,2) == fn.Round(n.lat,2),
            fn.Round(CabTrip.pickup_long,2) == fn.Round(n.long,2)
         )).execute()
        index += 1

# static neighborhood because the other method will take too long
def get_static_neighborhood(lat, long):
    float_lat = float(lat)
    float_long = float(long)
    if (float_long < -74.021587):
        return("New Jersey")
    elif (float_lat <= 40.698267):
        return ("Brooklyn")
    elif (float_lat <= 40.744843 and float_long >= -73.966656):
        return ("Williamsburg")
    elif (float_lat <= 40.713919):
        return("Financial District")
    elif(float_lat <= 40.746310):
        return ("Lower Manhattan")
    elif(float_lat <= 40.763345):
        return ("Midtown")
    elif(float_lat <= 40.799870):
        if (float_long >= -73.957729):
            return ("Upper East Side")
        else:
            return ("Upper West Side")
    elif(float_lat <=40.823126):
        return("Harlem")
    elif(float_lat <= 40.837544):
        return("Upper Manhattan")
    else:
        return("")
    
def get_neighborhood(lat, long):
    neighborhoodlist = Neighborhood.select()
    for neighborhood in neighborhoodlist:
        query = (NeighborhoodCoordinates
        .select(NeighborhoodCoordinates.latitude, NeighborhoodCoordinates.longitude)
        .where(NeighborhoodCoordinates.neighborhood_id == neighborhood.neighborhood_id))
        shape = []
        for s in query:
            shape.append((s.latitude, s.longitude))
        codes = []
        codes.append(Path.MOVETO)

        for i in range(len(shape)-2):
            codes.append(Path.LINETO)
        codes.append(Path.CLOSEPOLY)

        path = Path(shape, codes)
        if (path.contains_point((float(lat), float(long)))):
            return neighborhood.neighborhood_name

    return ""   

# check and exclude records that are invalid
def isvalid_cabtrip_record(row):
    # checks if any of the locations are 0 lat or 0 long
    if (row[6] == "0") or (row[5] == "0") or (row[9] == "0") or (row[10] == "0"):
        return False

    return True

def isvalid_trip_time(starttime, endtime):
    trip_time = endtime - starttime
    if (trip_time.total_seconds() <= 0 or (trip_time.total_seconds() / 60) > 720):
        return False
    return True

def load_cabtrips(db):
    starttime = time.time()
    index = 1
    cabtrips = []
    with open('cabdata_20150701.csv') as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader) # skip header row
        # speeds up the insert process significantly
        cabtrips = []
        with db.atomic():
            for row in datareader:
                pickuptime = convert_str_to_date(row[1])
                dropofftime = convert_str_to_date(row[2])
                pickupneighborhood = get_static_neighborhood(row[6],row[5])
                dropoffneighborhood = get_static_neighborhood(row[10],row[9])
                triplengthminutes = (dropofftime-pickuptime).total_seconds() / 60
                # to speed up inserts, we create an array first and insert a giant list of it in bulk
                if (isvalid_cabtrip_record(row)
                    and isvalid_trip_time(pickuptime, dropofftime)
                    and (pickupneighborhood != "" or dropoffneighborhood != "")):
                    cabtrips.append({
                                   "cab_id": index, \
                                   "pickup_time": pickuptime, \
                                   "pickup_lat": row[6], \
                                   "pickup_long": row[5], \
                                   "dropoff_time": dropofftime, \
                                   "dropoff_lat": row[10], \
                                   "dropoff_long": row[9], \
                                   "ride_distance": row[4], \
                                   "num_passenger": row[3], \
                                   "payment_type": row[11], \
                                   "tip_amount": row[15], \
                                   "fare_amount": row[12], \
                                   "pickup_neighborhood": pickupneighborhood,\
                                   "dropoff_neighborhood": dropoffneighborhood,\
                                   "trip_length_minutes": triplengthminutes ,\
                                   "avg_speed": float(row[4]) / triplengthminutes * 60   
                                     })
                    index += 1
                               
                    if (index % 60 == 0):
                        CabTrip.insert_many(cabtrips).execute()
                        cabtrips = []
                        
                    if (((time.time() - starttime) % 60.0) > 1):
                        __progressbar(index)
                        starttime = time.time()
                
        if (len(cabtrips) > 0):
            CabTrip.insert_many(cabtrips).execute()
    __progressbar(index)
    logfile.record("load completed! {0} record(s)".format(index))
    return index

def apply_data_science_cabtrips():
    global deeta
    logfile.record("Apply calculations")
    datasci = datascience.datascience_utilities(dbname)
    deeta = datasci.read_all_data()
    quants = datasci.get_speed_index_quantiles()

    # update congestion index based on the calculated quants
    CabTrip.update(congestion_index = 1).where((CabTrip.avg_speed < quants[0.2])).execute()
    CabTrip.update(congestion_index = 2).where((CabTrip.avg_speed < quants[0.4]) & (CabTrip.avg_speed >= quants[0.2])).execute()
    CabTrip.update(congestion_index = 3).where((CabTrip.avg_speed < quants[0.6]) & (CabTrip.avg_speed >= quants[0.4])).execute()
    CabTrip.update(congestion_index = 4).where((CabTrip.avg_speed < quants[0.8]) & (CabTrip.avg_speed >= quants[0.6])).execute()
    CabTrip.update(congestion_index = 5).where((CabTrip.avg_speed >= quants[0.8])).execute()
    

def load_coordinates(neighborhood_id, str_coordinates):
    coordinateslist = str_coordinates.split(',')
    arraylist = []
    index = 1
    with db.atomic():
        for coordinate in coordinateslist:
            point = coordinate.strip().split(' ')
            arraylist.append({"neighborhood_id":neighborhood_id, \
                              "latitude": point[1], \
                              "longitude": point[0]})
            if (index % 80 == 0):
                    NeighborhoodCoordinates.insert_many(arraylist).execute()
                    arraylist = []
            index += 1
        if (len(arraylist) > 0):
            NeighborhoodCoordinates.insert_many(arraylist).execute()

def load_neighborhoods(db):
    starttime = time.time()
    index = 1
    neighborhoods = []
    logfile.record("loading neighborhood data...")
    with open('nynta.csv') as neighborhoodfile:
        maxInt = sys.maxsize
        while True:
            try:
                csv.field_size_limit(maxInt)
                break
            except OverflowError:
                maxInt = int(maxInt/10)
        
        csv.field_size_limit(maxInt)
        datareader = csv.reader(neighborhoodfile, delimiter=',', quotechar='"')
        next(datareader)
        
        for row in datareader:
            __progressbar(index)
            index += 1
            neighborhood = Neighborhood(boro_name = row[2],\
                                      neighborhood_name = row[5])
            neighborhood.save()
            load_coordinates(neighborhood.neighborhood_id, row[0]
                             .replace(")","")
                             .replace("MULTIPOLYGON", "")
                             .replace("(","").strip())
    logfile.record('completed!')

# this will be configurable where we can pass arguments on whether to reload
# the data or to use whatever is in Sqlite
def load_data(db):
    logfile.record("Loading cab data...")
    load_cabtrips(db)
    
def drop_tables(db):
    db.connect()
    db.drop_tables([CabTrip, Neighborhood, NeighborhoodCoordinates], safe=True)
    logfile.record("Database tables dropped!")
    db.close()

def create_tables(db):
    db.connect()
    db.create_tables([CabTrip, Neighborhood, NeighborhoodCoordinates], safe=True)
    logfile.record("Database tables created!")
    db.close()
