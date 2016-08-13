#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, render_template, request
from flask.json import JSONEncoder
from flask_compress import Compress
from datetime import datetime, timedelta

from . import config
import log
from .models import CabTrip


compress = Compress()
logfile = log.Log("cabtrip.log")

# the magic that happens that allows us to run the web application locally
class CabData(Flask):
    def __init__(self, import_name, **kwargs):
        super(CabData, self).__init__(import_name, **kwargs)
        compress.init_app(self)
        self.json_encoder = JSONEncoder
        self.route("/", methods=['GET'])(self.fullmap)
        self.route("/raw_data", methods=['GET'])(self.raw_data)
        self.route("/get_loc", methods=['GET'])(self.get_loc)

    # this will load googlemaps data from the API
    def fullmap(self):
        return render_template('map.html',
                               lat=config['ORIGINAL_LATITUDE'],
                               lng=config['ORIGINAL_LONGITUDE'],
                               gmaps_key=config['GMAPS_KEY'],
                               is_fixed="inline"
                               )

    # raw data that is called asyncronously.  Have to limit the amount of data
    # that is passed through here.  Will probably change this to load in batches
    def raw_data(self):
        d = {}
        date = request.args.get('date')
        time = request.args.get('time')
        neighborhood = request.args.get('neighborhood')
        ispickup = request.args.get("ispickup")

        starttime = datetime.strptime("{0} {1}".format(date, time), "%m/%d/%Y %I:%M %p")
        endtime = starttime + timedelta(minutes=config['MINUTE_BLOCK'])
        
        d['cabs'] = CabTrip.get_records(neighborhood, starttime, endtime, ispickup.lower() == "true")
        tipamount = CabTrip.get_average_tip(neighborhood, starttime, endtime)
        d['avgtip'] = '{:20,.2f}'.format(tipamount)
        d['neighborhoods'] = CabTrip.get_neighborhood()

        logfile.record(("retrieved {0} cab trip data, {1} avg tip").format(len(d['cabs']), d['avgtip']))
        
        if (bool(ispickup)):
            d['marker_type'] = "pickup"
        else:
            d['marker_type'] = "dropoff"
        return jsonify(d)

    def get_loc(self):
        d = {}
        d['lat'] = config['ORIGINAL_LATITUDE']
        d['lng'] = config['ORIGINAL_LONGITUDE']

        return jsonify(d)
