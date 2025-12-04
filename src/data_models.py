import csv
import datetime as dt
from dataclasses import dataclass
from graph_algorithms import Graph

@dataclass
class City:
    city_id: int
    name: str
    state: str
    sea_level_ft: float  # elevation

BASE_MPG = 45.0  # same sea level
MAX_SPEED = 75.0  # mph
MAX_HOURS_PER_DAY = 8.0

def load_cities(path="data/cities.csv"):
    cities = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = int(row["city_id"])
            cities[cid] = City(
                cid,
                row["city_name"],
                row["state"],
                float(row["sea_level_ft"]),
            )
    return cities

def load_graph(cities, path="data/edges.csv"):
    g = Graph(len(cities))
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            u = int(row["from_id"])
            v = int(row["to_id"])
            d = float(row["map_distance_miles"])
            g.add_edge(u, v, d, undirected=True)
    return g

def load_weather_risk(path="data/weather_nov2025.csv"):
    """
    You create this CSV with either:
    - raw conditions + convert to risk, or
    - direct risk column.
    Example header:
    city_id,date,condition,risk
    0,2025-11-01,Sunny,1
    """
    risk = {}
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = int(row["city_id"])
            date = dt.date.fromisoformat(row["date"])
            r = float(row["risk"])
            risk[(cid, date)] = r
    return risk

def name_to_id(cities, city_name):
    city_name = city_name.lower()
    for cid, c in cities.items():
        if c.name.lower() == city_name:
            return cid
    raise ValueError(f"City {city_name} not found")