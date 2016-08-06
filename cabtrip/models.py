#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
import time
import csv
import sys

from peewee import Model, SqliteDatabase, InsertQuery,\
                   IntegerField, CharField, DoubleField, DateTimeField

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
    lat = DoubleField()
    long = DoubleField()
    zipcode = CharField()
    
class CabTrip(BaseModel):
    pickup_time = DateTimeField()
    pickup_long = DoubleField()
    pickup_lat = DoubleField()
    pickup_neighborhood = CharField(null=True)
    
    dropoff_time = DateTimeField()
    dropoff_long = DoubleField()
    dropoff_lat = DoubleField()
    dropoff_neighborhood = CharField(null=True)
    
    ride_distance = DoubleField()
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
    for n in Neighborhood.select():
        (CabTrip
        .update(pickup_neighborhood = n.zipcode)
        .where(
            n.lat == str(CabTrip.pickup_lat)[:5],
            n.long == str(CabTrip.pickup_long)[:6]
         )).execute()
        (CabTrip
        .update(dropoff_neighborhood = n.zipcode)
        .where(
            n.lat == str(CabTrip.dropoff_lat)[:5],
            n.long == str(CabTrip.dropoff_long)[:6]
         )).execute()

def get_neighborhood(lat, long):
    try:
        for n in Neighborhood.select().where((str(Neighborhood.lat) in lat), (str(Neighborhood.long) in long)):
            return n.city
    except ValueError:
        return None        
    return None

# this will be configurable where we can pass arguments on whether to reload
# the data or to use whatever is in Sqlite
def load_data(db):
    cabs = []
    index = 1
    starttime = time.time()
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

    index = 1
    print("loading cab data...")
    with open('cabdata.csv') as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader) # skip header row
        # speeds up the insert process significantly
        cabtrips = []
        with db.atomic():
            for row in datareader:
                # to speed up inserts, we create an array first and insert a giant list of it in bulk
                cabtrips.append({"pickup_time": convert_str_to_date(row[1]), \
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
    print('updating neighborhoods...')
    #update_neighborhood()
    
    

def create_tables(db):
    db.connect()
    db.create_tables([CabTrip,TypePayment,Neighborhood], safe=True)
    db.close()
