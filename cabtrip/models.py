#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import time
import csv
import sys

import log

from peewee import Model, SqliteDatabase, InsertQuery, DecimalField, PrimaryKeyField, \
                   IntegerField, CharField, DoubleField, DateTimeField, fn

from matplotlib.path import Path

from . import config


db = None
logfile = log.Log("cabtrip.log")

# initializing a sqllitedb
def init_database():
    global db
    if db is not None:
        return db
    db = SqliteDatabase("cabdata.db")
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
    congestion_index = IntegerField(null=True)
	
    @classmethod
    def get_all(self):
        query = (CabTrip.select().dicts())

        cabs = []
        for p in query:
            cabs.append(p)

        return cabs

    @classmethod
    def get_records(self, neighborhood, starttime, endtime, ispickup):
        query = None
        cabs = []
        if (ispickup):
            query = (CabTrip
                     .select(CabTrip.pickup_lat.alias('latitude'), CabTrip.pickup_long.alias('longitude'))
                     .where(#(CabTrip.pickup_neighborhood == neighborhood or neighborhood == "") &
                         (CabTrip.pickup_time.between(starttime, endtime))).dicts())
            
            
        else:
            query = (CabTrip
                     .select(CabTrip.dropoff_lat.alias('latitude'), CabTrip.dropoff_long.alias('longitude'))
                     .where(#(CabTrip.dropoff_neighborhood == neighborhood or neighborhood == "") &
                         (CabTrip.dropoff_time.between(starttime, endtime))).dicts())

        print(type(query[0]))
        for p in query:
                cabs.append(p)
        return cabs

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

    @classmethod
    def get_average_tip(self, neighborhood, starttime, endtime):
        query = None
        cabs = []
        tipamount = (CabTrip
                 .select(fn.AVG(CabTrip.tip_amount))
                 .where(#(CabTrip.pickup_neighborhood == neighborhood or neighborhood == "") &
                     (CabTrip.payment_type == 1) &
                     (CabTrip.pickup_time.between(starttime, endtime)))
                 .scalar())
        return tipamount
    
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
    
    if (float_lat <= 40.713919):
        return("Financial District")
    elif(float_lat <= 40.746310):
        return ("Lower Manhattan")
    elif(float_lat <= 40.763345):
        return ("Midtown")
    elif(float_lat <= 40.799870):
        if (float_long <= -73.957729):
            return ("Upper EastSide")
        else:
            return ("Upper WestSide")
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
    with open('cabdata.csv') as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader) # skip header row
        # speeds up the insert process significantly
        cabtrips = []
        with db.atomic():
            for row in datareader:
                pickuptime = convert_str_to_date(row[1])
                dropofftime = convert_str_to_date(row[2])
                # to speed up inserts, we create an array first and insert a giant list of it in bulk
                if (isvalid_cabtrip_record(row) and isvalid_trip_time(pickuptime, dropofftime)):
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
                                   "pickup_neighborhood": get_static_neighborhood(row[6],row[5]),\
                                   "dropoff_neighborhood": get_static_neighborhood(row[10],row[9]),\
                                   "trip_length_minutes": (dropofftime-pickuptime).total_seconds() / 60,\
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
