# main application that loads the data and runs the server

import os
import sys, getopt
import time
import log

from cabtrip import config
from cabtrip.app import CabData
from cabtrip.models import CabTrip
from cabtrip.database import init_database, create_tables, drop_tables, load_data, apply_data_science_cabtrips

# description of some few options.  (this makes it easy to reload the data)
def usage():
    print("-d --datafile\tThe csv file of cab data to import.  Default:{0}".format(config["INPUT_FILE"]))
    print("-o --overwrite\tDefault:False Will rerun the dataload process if the database exists")

def main():

    # hardcoded central park location to default google maps initial view
    position = [40.783129, -73.965206]
 
    # the configuration information that we will use to send to 
    config['ORIGINAL_LATITUDE'] = position[0]
    config['ORIGINAL_LONGITUDE'] = position[1]
    config['GMAPS_KEY'] = 'AIzaSyDEEvXvhoUgKWam-XAYVo-YhxjWdBbn5Fc'
    config['MINUTE_BLOCK'] = 15
    config['SILENT_LOG'] = False
    config['INPUT_FILE'] = 'cabdata_20150701.csv'
    config['RELOAD'] = False
    
    app = CabData(__name__)

    
    argv = sys.argv[1:]
 
    reload = False
    inputFile = config['INPUT_FILE'] 
    try:
        opts, args = getopt.getopt(argv, "dho", ["datafile=", "help", "silent", "overwrite"])
    except getopt.GetoptError as err:
        print(err)
        sys.exit(2)
    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-d", "--datafile"):
            inputFile = a
        elif o in ("-o", "--overwrite"):
            config["RELOAD"] = True
            reload = True
        else:
            assert False, "unhandled option"

    db = init_database()
    if ((not CabTrip.table_exists()) or reload):
        drop_tables(db)
        create_tables(db)
        load_data(db, inputFile)

    

    config['ROOT_PATH'] = app.root_path
    print("Starting location at", position)
    
    app.run(threaded=False, use_reloader=False, debug=True, host="127.0.0.1", port="5000")
    
if __name__ == '__main__':
    main()
    
