#!/usr/bin/python
# -*- coding: utf-8 -*-

from flask import Flask, jsonify, render_template, request
from flask.json import JSONEncoder
from flask_compress import Compress

from . import config
from .models import CabTrip

compress = Compress()

# the magic that happens that allows us to run the web application locally
class CabDataSample(Flask):
    def __init__(self, import_name, **kwargs):
        super(CabDataSample, self).__init__(import_name, **kwargs)
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
        startrow = request.args.get('startrow')
        fetch = request.args.get('numrecords')
        d['cabs'] = CabTrip.get_range(startrow, fetch)
        return jsonify(d)

    def get_loc(self):
        d = {}
        d['lat'] = config['ORIGINAL_LATITUDE']
        d['lng'] = config['ORIGINAL_LONGITUDE']

        return jsonify(d)
