# Location

class Location:
    def __init__(self, lat, long, neighborhood = ""):
        self.latitude = lat
        self.longitude = long
        self.neighborhood = neighborhood

    def get_latitude(self):
        return self.latitude

    def get_longitude(self):
        return self.longitude

    def get_neighborhood(self):
        return self.neighborhood

    def __str__(self):
        return ("location: ({0},{1}) neighborhood:{2}").format(self.latitude, self.longitude, self.neighborhood)

        
                 
