from datetime import datetime, timedelta
import time

import log
from cabtrip.location import PickupLocation, DropoffLocation
from peewee import Model, SqliteDatabase, InsertQuery, DecimalField, PrimaryKeyField, \
                   IntegerField, CharField, DoubleField, DateTimeField, fn

from . import config

dbname = config['DATABASE']
logfile = log.Log(config['LOG_FILE'], False, config['SILENT_LOG'])
db = None
                  
# general basemodel that is needed to be shared with the other ORM classes
class BaseModel(Model):
    class Meta:
        if (db is not None):
            database = db
        else:
            db = SqliteDatabase(dbname)
            database = db

# the coordinates in lat and long that makes up a neighborhood
class NeighborhoodCoordinates(BaseModel):
    coordinates_id = PrimaryKeyField(primary_key=True)
    neighborhood_id = IntegerField()
    latitude = DoubleField()
    longitude = DoubleField()
    
# the neighborhood of the city (not being used due to speed issue)
class Neighborhood(BaseModel):
    neighborhood_id = PrimaryKeyField(primary_key=True)
    boro_name = CharField()
    neighborhood_name = CharField()
    
# the main cabtrip data.  This will also include calculations in the db to address performance issues
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

    # where statement so that we are not reusing the same code...
    @classmethod
    def build_where_statement(self, neighborhoodtype, ispickup):
        datatype = "dropoff"
        neighborhooddatatype = "dropoff"
        if (ispickup):
            datatype = "pickup"
            
        if (neighborhoodtype == 'Pick-up'):
            neighborhooddatatype = "pickup"

        return('WHERE {0}_time <= ? and {0}_time >= ? and {1}_neighborhood like ?'.format(datatype, neighborhooddatatype))

    # the main query that returns a list of lat and long to build the markers in the view
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

        for q in query:
            cabs.append(q)
        return cabs

    # method that returns that average time of the filtered dataset
    @classmethod
    def get_average_time(self, startneighborhood, endneighborhood, starttime, endtime):
        query = None

        #build the sql statement.  although we are doing string format, we are controlling the type of data that can be put there
        #to avoid sql injection.  the expressions does use parameterized sql
        sql = "select avg(trip_length_minutes) FROM cabtrip WHERE pickup_neighborhood == ? " \
              "and dropoff_neighborhood == ? and pickup_time <= ? and pickup_time >= ?"
        average_time = CabTrip.raw(sql, startneighborhood, endneighborhood, endtime, starttime).scalar()

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
    def get_average_cost(self, startneighborhood, endneighborhood, starttime, endtime):
        query = None

        #build the sql statement.  although we are doing string format, we are controlling the type of data that can be put there
        #to avoid sql injection.  the expressions does use parameterized sql
        sql = "select avg(fare_amount + tip_amount) FROM cabtrip WHERE pickup_neighborhood == ? " \
              "and dropoff_neighborhood == ? and pickup_time <= ? and pickup_time >= ?"
        avgcost = CabTrip.raw(sql, startneighborhood, endneighborhood, endtime, starttime).scalar()

        if (avgcost == None):
            return 0
        
        return avgcost

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


