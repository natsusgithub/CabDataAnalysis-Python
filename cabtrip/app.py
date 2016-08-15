# Application that serves as a layer between the front-end and the model

from flask import Flask, jsonify, render_template, request
from flask.json import JSONEncoder
from flask_compress import Compress
from datetime import datetime, timedelta

from . import config
import log
from .models import CabTrip

import datascience

compress = Compress()
logfile = log.Log(config["LOG_FILE"])

# the magic that happens that allows us to run the web application
class CabData(Flask):
    def __init__(self, import_name, **kwargs):
        super(CabData, self).__init__(import_name, **kwargs)
        compress.init_app(self)
        self.json_encoder = JSONEncoder
        self.route("/", methods=['GET'])(self.fullmap)
        self.route("/raw_data", methods=['GET'])(self.raw_data)
        self.route("/get_loc", methods=['GET'])(self.get_loc)
        self.route("/load_graphs", methods=['POST'])(self.load_graphs)

    # this will load googlemaps data from the API
    def fullmap(self):
        return render_template('map.html',
                               lat=config['ORIGINAL_LATITUDE'],
                               lng=config['ORIGINAL_LONGITUDE'],
                               gmaps_key=config['GMAPS_KEY'],
                               minute_block=config['MINUTE_BLOCK'],
                               is_fixed="inline"
                               )

    # method that we are not using right now but will load basic matplotlib graphs
    def load_graphs(self):
        datasci = datascience.datascience_utilities(config["DATABASE"])
        deeta = datasci.read_all_data()
        quants = datasci.get_speed_index_quantiles()
        datasci.get_plot_speed()
        return []

    # raw data that is called asyncronously.  Have to limit the amount of data
    # that is passed through here.  Will probably change this to load in batches
    def raw_data(self):
        d = {}
        # querystring arguments
        date = request.args.get('date')
        time = request.args.get('time')
        neighborhood = request.args.get('neighborhood')
        neighborhoodtype = request.args.get('neighborhoodtype')
        ispickup = request.args.get("ispickup")
        starttime = datetime.strptime("{0} {1}".format(date, time), "%m/%d/%Y %I:%M %p")
        endtime = starttime + timedelta(minutes=config['MINUTE_BLOCK'])

        # call methods to load data and get calculations
        d['cabs'] = CabTrip.get_records(neighborhood, neighborhoodtype, starttime, endtime, ispickup.lower() == "true")
        tipamount = CabTrip.get_average_tip(neighborhood, neighborhoodtype, starttime, endtime, ispickup)
        congestion = CabTrip.get_average_congestion(neighborhood, neighborhoodtype, starttime, endtime, ispickup)
        avgtimeminutes =  CabTrip.get_average_time('Midtown', 'Upper West Side', starttime, endtime)
        tippercentage = CabTrip.get_tip_percentage(neighborhood, neighborhoodtype, starttime, endtime, ispickup)
        avgcost = CabTrip.get_average_cost('Midtown', 'Upper West Side', starttime, endtime)
        d['avgtip'] = '{:20,.2f}'.format(tipamount)
        d['avgcost'] = '{:20,.2f}'.format(avgcost)
        d['percentagetip'] = '{0:.0f}%'.format(tippercentage * 100)
        d['percentcongestion'] = '{0:.0f}%'.format((1-congestion) * 100)
        d['avgtimeminutes'] = '{0:.0f} minutes'.format(avgtimeminutes)

        logfile.record(("retrieved {0} cab trip data, "\
                        "{1} avg tip, {2} tip percentage, "\
                        "{3} avg congestion, {4} avg time minutes, "\
                        "{5} avg cost").format(len(d['cabs']), \
                            tipamount, tippercentage, \
                            congestion, avgtimeminutes, avgcost))
        
        if (bool(ispickup)):
            d['marker_type'] = "pickup"
        else:
            d['marker_type'] = "dropoff"

        # return the jsonifyed data
        return jsonify(d)

    def get_loc(self):
        d = {}
        d['lat'] = config['ORIGINAL_LATITUDE']
        d['lng'] = config['ORIGINAL_LONGITUDE']

        return jsonify(d)
