import math
import requests


# Multiple Overpass servers
# Agar pehla server fail hota hai to automatically
# next server try kiya jayega.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter"
]


HIGHWAY_TYPES = {
    "motorway",
    "motorway_link",
    "trunk",
    "trunk_link",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
    "unclassified",
    "residential",
    "living_street",
    "service"
}


HIGHWAY_ROADS = {
    "motorway",
    "motorway_link",
    "trunk",
    "trunk_link",
    "primary",
    "primary_link"
}


SERVICE_ROADS = {
    "service"
}


def haversine(lat1, lon1, lat2, lon2):

    R = 6371000

    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        +
        math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(a))


def road_length(geometry):

    total = 0

    for i in range(len(geometry) - 1):

        p1 = geometry[i]
        p2 = geometry[i + 1]

        total += haversine(
            p1["lat"],
            p1["lon"],
            p2["lat"],
            p2["lon"]
        )

    return total


def calculate_curvature(geometry):

    if len(geometry) < 3:
        return 0.001

    total_angle = 0

    for i in range(1, len(geometry) - 1):

        a = geometry[i - 1]
        b = geometry[i]
        c = geometry[i + 1]

        angle1 = math.atan2(
            b["lat"] - a["lat"],
            b["lon"] - a["lon"]
        )

        angle2 = math.atan2(
            c["lat"] - b["lat"],
            c["lon"] - b["lon"]
        )

        difference = abs(angle2 - angle1)

        if difference > math.pi:
            difference = 2 * math.pi - difference

        total_angle += difference

    length = road_length(geometry)

    if length <= 0:
        return 0.001

    return total_angle / length


def point_to_segment_distance(
    lat,
    lon,
    a,
    b
):

    lat_scale = 111320

    lon_scale = 111320 * math.cos(
        math.radians(lat)
    )

    px = lon * lon_scale
    py = lat * lat_scale

    ax = a["lon"] * lon_scale
    ay = a["lat"] * lat_scale

    bx = b["lon"] * lon_scale
    by = b["lat"] * lat_scale

    dx = bx - ax
    dy = by - ay

    if dx == 0 and dy == 0:

        return math.sqrt(
            (px - ax) ** 2 +
            (py - ay) ** 2
        )

    t = (
        (px - ax) * dx +
        (py - ay) * dy
    ) / (dx * dx + dy * dy)

    t = max(0, min(1, t))

    nearest_x = ax + t * dx
    nearest_y = ay + t * dy

    return math.sqrt(
        (px - nearest_x) ** 2 +
        (py - nearest_y) ** 2
    )


def distance_from_road(
    latitude,
    longitude,
    geometry
):

    minimum = float("inf")

    for i in range(len(geometry) - 1):

        distance = point_to_segment_distance(
            latitude,
            longitude,
            geometry[i],
            geometry[i + 1]
        )

        minimum = min(
            minimum,
            distance
        )

    return minimum


def parse_number(value):

    if value is None:
        return None

    try:

        value = str(value)

        number = ""

        for char in value:

            if char.isdigit() or char == ".":
                number += char

            elif number:
                break

        return float(number) if number else None

    except Exception:

        return None


def default_lanes(highway_class):

    if highway_class in {
        "motorway",
        "trunk",
        "primary"
    }:

        return 2.0

    return 1.0


def default_speed(highway_class):

    defaults = {
        "motorway": 100,
        "motorway_link": 60,
        "trunk": 80,
        "trunk_link": 60,
        "primary": 60,
        "primary_link": 50,
        "secondary": 50,
        "secondary_link": 40,
        "tertiary": 40,
        "tertiary_link": 40,
        "residential": 30,
        "living_street": 20,
        "service": 20,
        "unclassified": 30
    }

    return float(
        defaults.get(
            highway_class,
            30
        )
    )


def classify_osm_road(highway_class):

    if highway_class in HIGHWAY_ROADS:
        return "highway"

    if highway_class in SERVICE_ROADS:
        return "service_road"

    return "local_road"


def get_nearest_road(
    latitude,
    longitude
):

    query = f"""
    [out:json][timeout:10];

    way["highway"]
    (around:100,{latitude},{longitude});

    out geom;
    """

    # --------------------------------------------------
    # Try multiple Overpass servers
    # --------------------------------------------------

    data = None
    last_error = None

    for overpass_url in OVERPASS_URLS:

        try:

            print(
                f"Trying Overpass server: "
                f"{overpass_url}"
            )

            response = requests.post(
                overpass_url,
                data=query,
                headers={
                    "User-Agent":
                        "MapMatchingStudentProject/1.0"
                },
                timeout=20
            )

            response.raise_for_status()

            data = response.json()

            print(
                f"Overpass server successful: "
                f"{overpass_url}"
            )

            break

        except Exception as error:

            print(
                f"Overpass server failed: "
                f"{overpass_url}"
            )

            print(
                f"Error: {error}"
            )

            last_error = error

    # --------------------------------------------------
    # If all Overpass servers failed
    # --------------------------------------------------

    if data is None:

        raise Exception(
            f"All Overpass servers failed. "
            f"Last error: {last_error}"
        )

    # --------------------------------------------------
    # Process roads
    # --------------------------------------------------

    roads = []

    for element in data.get("elements", []):

        tags = element.get("tags", {})
        geometry = element.get("geometry", [])

        highway_class = tags.get("highway")

        if (
            highway_class not in HIGHWAY_TYPES
            or len(geometry) < 2
        ):
            continue

        distance = distance_from_road(
            latitude,
            longitude,
            geometry
        )

        roads.append(
            (
                distance,
                element
            )
        )

    # --------------------------------------------------
    # No road found
    # --------------------------------------------------

    if not roads:
        return None

    # --------------------------------------------------
    # Select nearest road
    # --------------------------------------------------

    roads.sort(
        key=lambda item: item[0]
    )

    distance, road = roads[0]

    tags = road.get("tags", {})
    geometry = road.get("geometry", [])

    highway_class = tags.get(
        "highway",
        "unknown"
    )

    # --------------------------------------------------
    # Lanes
    # --------------------------------------------------

    lanes = parse_number(
        tags.get("lanes")
    )

    if lanes is None:

        lanes = default_lanes(
            highway_class
        )

    # --------------------------------------------------
    # Maximum speed
    # --------------------------------------------------

    max_speed = parse_number(
        tags.get("maxspeed")
    )

    if max_speed is None:

        max_speed = default_speed(
            highway_class
        )

    # --------------------------------------------------
    # Road length
    # --------------------------------------------------

    length = road_length(
        geometry
    )

    # --------------------------------------------------
    # Road width
    # --------------------------------------------------

    width = parse_number(
        tags.get("width")
    )

    if width is None:

        width = lanes * 3.5

    # --------------------------------------------------
    # Curvature
    # --------------------------------------------------

    curvature = calculate_curvature(
        geometry
    )

    # --------------------------------------------------
    # Final road information
    # --------------------------------------------------

    return {

        "road_name": tags.get(
            "name",
            "Unnamed Road"
        ),

        "highway_class": highway_class,

        "road_type": classify_osm_road(
            highway_class
        ),

        "distance": distance,

        "road_length": length,

        "lanes": lanes,

        "max_speed": max_speed,

        "road_width": width,

        "curvature": curvature
    }