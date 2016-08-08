#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
import time
import csv
import sys

from peewee import Model, SqliteDatabase, InsertQuery, DecimalField, \
                   IntegerField, CharField, DoubleField, DateTimeField, fn

from geopy.geocoders import Nominatim

from . import config


db = None

# initializing a sqllitedb
def init_database():
    global db
    if db is not None:
        return db
    db = SqliteDatabase("cabdata.db")
    print("SqliteDatabase created!")
    return db

class BaseModel(Model):
    class Meta:
        database = init_database()

    @classmethod
    def get_all(self):
        results = [m for m in self.select().dicts()]
        return results

class TypePayment(BaseModel):
    # properties
    # code
    # description
    code = IntegerField(primary_key=True)
    description = CharField()

    @classmethod
    def get_all(self):
        results = [m for m in self.select().dicts()]
        return results

    # get one row
    def find(self, code):
        return self.get(self.code == code)

class Neighborhood(BaseModel):
    city = CharField()
    state = CharField()
    lat = DecimalField()
    long = DecimalField()
    zipcode = CharField()
    
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

    congestion_index = IntegerField(null=True)
	
    @classmethod
    def get_all(self):
        query = (CabTrip.select().dicts())

        cabs = []
        for p in query:
            cabs.append(p)

        return cabs

    @classmethod
    def get_range(self, startindex, fetch):
        query = (CabTrip
                 .select(CabTrip.pickup_lat, CabTrip.pickup_long, CabTrip.dropoff_lat, CabTrip.dropoff_long)
                 .where((CabTrip.cab_id >= startindex) & (CabTrip.cab_id < (startindex + fetch))).dicts())
        cabs = []
        for p in query:
            cabs.append(p)
        print(len(cabs))
        return cabs

# helper to display a progress bar
def __progressbar(i):
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


def get_neighborhood(db, lat, long):
    #db.
        
    #neighborhood = Neighborhood.get((round(Neighborhood.lat, 2) == round(float(lat),2)), (round(
     return "1"   

def load_cabtrips(db):
    starttime = time.time()
    index = 1
    cabtrips = []
    print("loading cab data...")
    with open('cabdata.csv') as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader) # skip header row
        # speeds up the insert process significantly
        cabtrips = []
        with db.atomic():
            for row in datareader:
                # to speed up inserts, we create an array first and insert a giant list of it in bulk
                cabtrips.append({
                               "cab_id": index, \
                               "pickup_time": convert_str_to_date(row[1]), \
                               "pickup_lat": row[6], \
                               "pickup_long": row[5], \
                               "dropoff_time": convert_str_to_date(row[2]), \
                               "dropoff_lat": row[10], \
                               "dropoff_long": row[9], \
                               "ride_distance": row[4], \
                               "num_passenger": row[3], \
                               "payment_type": row[11], \
                               "tip_amount": row[15], \
                               "fare_amount": row[12], \
                               #"pickup_neighborhood": get_neighborhood(row[6],row[5])
                                 })
                               
                if (index % 80 == 0):
                    CabTrip.insert_many(cabtrips).execute()
                    cabtrips = []
                    
                if (((time.time() - starttime) % 60.0) > 1):
                    __progressbar(index)
                    starttime = time.time()
                index += 1
        if (len(cabtrips) > 0):
            CabTrip.insert_many(cabtrips).execute()
    __progressbar(index)
    print('completed!')
    return index

def load_neighborhoods(db):
    starttime = time.time()
    index = 1
    neighborhoods = []
    print("loading neighborhood data...")
    with open('zipcode.csv') as zipcodefile:
        datareader = csv.reader(zipcodefile, delimiter=',', quotechar='"')
        with db.atomic():
            for row in datareader:
                # only care about NY
                if (len(row) > 0):
                    if (row[2] == 'NY'):
                        neighborhoods.append({"city": row[1], \
                                              "state": row[2], \
                                              "zipcode": row[0], \
                                              "lat": row[3], \
                                              "long": row[4]})
                        
                        if (index % 100 == 0):
                            Neighborhood.insert_many(neighborhoods).execute()
                            neighborhoods = []
                        
                        if (((time.time() - starttime) % 60.0) > 1):
                            __progressbar(index)
                            starttime = time.time()
                        index += 1
        if (len(neighborhoods) > 0):
            Neighborhood.insert_many(neighborhoods).execute()
    __progressbar(index)
    print('completed!')
    return index

# this will be configurable where we can pass arguments on whether to reload
# the data or to use whatever is in Sqlite
def load_data(db):
    load_neighborhoods(db)

    load_cabtrips(db)

   # update_neighborhood()
    


   

def drop_tables(db):
    db.connect()
    db.drop_tables([CabTrip, TypePayment, Neighborhood], safe=True)
    db.close()

def create_tables(db):
    db.connect()
    db.create_tables([CabTrip,TypePayment,Neighborhood], safe=True)
    db.close()
