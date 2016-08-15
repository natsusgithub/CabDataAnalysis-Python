# example of inheritance of pickup and dropoff locations

class Location:
    def __init__(self, lat, long, congestion_index, neighborhood = ""):
        self.latitude = lat
        self.longitude = long
        self.congestion_index = congestion_index 
        self.neighborhood = neighborhood
 
    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude

    def get_neighborhood(self):
        return self.neighborhood

    def __str__(self):
        return ("location: ({0},{1}) neighborhood:{2}").format(self.latitude, self.longitude, self.neighborhood)

class PickupLocation:
    def __init__(self, lat, long, congestion_index, neighborhood = ""):
        Location.__init__(self, lat, long, neighborhood)
        self.type = "pickup"

    def get_type(self):
        return self.type

class DropoffLocation:
    def __init__(self, lat, long, congestion_index, neighborhood = ""):
        Location.__init__(self, lat, long, neighborhood)
        self.type = "dropoff"

    def get_type(self):
        return self.type

