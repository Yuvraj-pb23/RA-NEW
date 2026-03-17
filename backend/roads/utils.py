import gpxpy

def parse_gpx(file_path):
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    points = []
    total_length = 0

    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append({
                    "lat": point.latitude,
                    "lng": point.longitude
                })

            total_length += segment.length_2d()

    return {
        "points": points,
        "length_km": total_length / 1000
    }
