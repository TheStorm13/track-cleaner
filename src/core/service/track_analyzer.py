from haversine import haversine, Unit

class TrackAnalyzer:

    def haversine_distance(self, lat1, lon1, lat2, lon2):
        return haversine((lat1, lon1), (lat2, lon2), unit=Unit.METERS)
