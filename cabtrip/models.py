#!/usr/bin/python
# -*- coding: utf-8 -*-

import time
import csv
import sys

from peewee import Model, SqliteDatabase, InsertQuery,\
                   IntegerField, CharField, DoubleField

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
    
class CabTrip(BaseModel):
    # properties for demo purposes we would load the following
    # id
    # pickuplong
    # pickuplat
    # dropofflong
    # dropofflat
    # ridedistance
    # pickuptime
    # dropofftime
    # numpassenger
    # paymenttype
    # tipamount
    # fareamount
    id = IntegerField(primary_key=True)
    latitude = DoubleField()
    longitude = DoubleField()
    
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

# this will be configurable where we can pass arguments on whether to reload
# the data or to use whatever is in Sqlite
def load_data():
    cabs = []
    index = 1
    starttime = time.time()
    # we wouldn't do this in production.  This will reinsert the csv file
    # use a smaller csv file (1000 count or less)
    q = CabTrip.delete()
    q.execute()
    with open('cabdata.csv') as csvfile:
        datareader = csv.reader(csvfile)

        next(datareader)
        for row in datareader:
            CabTrip.create(id = index, latitude = row[6], longitude=row[5])
            index += 1 # creates the primary key
            if (((time.time() - starttime) % 60.0) > 1):
                __progressbar(index)
                starttime = time.time()
    __progressbar(index)
    print('completed!')

def create_tables(db):
    db.connect()
    db.create_tables([CabTrip,TypePayment], safe=True)
    db.close()
