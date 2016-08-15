# database model that takes care of the loading

from datetime import datetime, timedelta
import time
import csv
import sys
from peewee import SqliteDatabase

import datascience
import log
from cabtrip.models import CabTrip, Neighborhood, NeighborhoodCoordinates
from . import config

dbname = config['DATABASE']
db = None
logfile = log.Log(config['LOG_FILE'], False, config['SILENT_LOG'])

# initializing a sqllitedb
def init_database():
    global db
    
    if db is not None:
        return db
    db = SqliteDatabase(dbname)
    return db

# helper to display a progress bar
def __progressbar(i):
        if (not logfile.silent):
            loadicon = "|" # potentially have an animated icon.  static for now

            # write to the same row
            sys.stdout.write('\r')
            sys.stdout.write(loadicon + " " + str(i) + " rows inserted...")
            sys.stdout.flush()
        

#converts string formatted in 1/1/2001 0:00:00 notation
def convert_str_to_date(value):
    
    try:
        # this is the default format of the datetime field
        return datetime.strptime(value, "%m/%d/%Y %H:%M")
       
    except ValueError:
        # this is another format that some of the datasets use
        # try a different format 2001/1/1 00:00:00
        
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


# method that will update the neighborhoods based on the polynomial points
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

# get the neighborhood name based on the polynomial.  Too long to run right now...    
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

# check and exclude triptimes that are invalid
def isvalid_trip_time(starttime, endtime):
    trip_time = endtime - starttime
    if (trip_time.total_seconds() <= 0 or (trip_time.total_seconds() / 60) > 720):
        return False
    return True

# main method that loads the cabtrip data
def load_cabtrips(db, inputFile):
    starttime = time.time()
    index = 1
    cabtrips = []
    
    with open(inputFile) as csvfile:
        datareader = csv.reader(csvfile)
        next(datareader) # skip header row
        # speeds up the insert process significantly
        cabtrips = [] # reset the cabtrips.  this is used to generate a list for bulk inserts

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
                                   #calculated fields... this is added here to reduce the time needed to run
                                   "trip_length_minutes": triplengthminutes ,\
                                   "avg_speed": float(row[4]) / triplengthminutes * 60   
                                 })

                    # bulk insert every 60 rows.  (can't do more because there is a limit of how much you can pass through peewee
                    if (index % 60 == 0):
                        CabTrip.insert_many(cabtrips).execute()
                        cabtrips = [] # reset the array

                    # give a nice status message every minute of the number of rows being inserted
                    if (((time.time() - starttime) % 60.0) > 1):
                        __progressbar(index)
                        starttime = time.time()
                    index += 1

        # there may be more records that didn't get added because we are updating every 60 records.
        if (len(cabtrips) > 0):
            CabTrip.insert_many(cabtrips).execute()
            
    # last progress bar message to bring the count up to the length of the inserted records
    __progressbar(index)
    logfile.record("load completed! {0} record(s)".format(index))
    return index

# this is a method that will perform calculations that would drive the data science.  Currently we are only
# taking care of the quantiles of the speed.  We could potentially expand this to perform other calculations
def apply_data_science_cabtrips():
    logfile.record("Apply calculations...")
    datasci = datascience.datascience_utilities(dbname)
    deeta = datasci.read_all_data()
    quants = datasci.get_speed_index_quantiles()

    # update congestion index based on the calculated quants
    logfile.record("Update records that fall within quantile 0.2...")
    CabTrip.update(congestion_index = 1).where((CabTrip.avg_speed < quants[0.2])).execute()
    logfile.record("Update records that fall within quantile 0.4...")
    CabTrip.update(congestion_index = 2).where((CabTrip.avg_speed < quants[0.4]) & (CabTrip.avg_speed >= quants[0.2])).execute()
    logfile.record("Update records that fall within quantile 0.6...")
    CabTrip.update(congestion_index = 3).where((CabTrip.avg_speed < quants[0.6]) & (CabTrip.avg_speed >= quants[0.4])).execute()
    logfile.record("Update records that fall within quantile 0.8...")
    CabTrip.update(congestion_index = 4).where((CabTrip.avg_speed < quants[0.8]) & (CabTrip.avg_speed >= quants[0.6])).execute()
    logfile.record("Update records that fall above quantile 0.8...")
    CabTrip.update(congestion_index = 5).where((CabTrip.avg_speed >= quants[0.8])).execute()

#not being used... this is loaded with the load_neighborhoods method but speed is an issue here
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

#not being used... this takes too long to run
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
def load_data(db, inputFile):
    logfile.record("Loading cab data (about 380,000 records total in default file)...")
    load_cabtrips(db, inputFile)
    logfile.record("Generating calculations to database...")
    apply_data_science_cabtrips()

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
