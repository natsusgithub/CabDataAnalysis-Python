#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import time

from threading import Thread
# from flask_cors import CORS

from cabtrip import config
from cabtrip.app import CabDataSample
#from cabtrip.search import create_search_threads, search_loop
from cabtrip.models import init_database, create_tables, CabTrip, load_data


if __name__ == '__main__':

    db = init_database()
    create_tables(db)
    load_data(db)

    # hardcoded central park location to default google maps initial view
    position = [40.783129, -73.965206]

    print("Starting location at", position)
    
    config['ORIGINAL_LATITUDE'] = position[0]
    config['ORIGINAL_LONGITUDE'] = position[1]
    config['GMAPS_KEY'] = 'AIzaSyDEEvXvhoUgKWam-XAYVo-YhxjWdBbn5Fc'
    
    app = CabDataSample(__name__)

    config['ROOT_PATH'] = app.root_path

    app.run(threaded=False, use_reloader=False, debug=True, host="127.0.0.1", port="5000")
    
