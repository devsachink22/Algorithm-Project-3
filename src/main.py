import random
import datetime as dt
import os
import csv
from data_models import (
    load_cities,
    load_graph,
    load_weather_risk,
    name_to_id,
    BASE_MPG,
    MAX_SPEED,
    MAX_HOURS_PER_DAY,
)
from travel_logic import best_travel_date
from performance_monitor import PerformanceMonitor

perf = PerformanceMonitor()
perf_stats = []

# Utility: Convert city ID → name
def id_to_name(cities, cid):
    return cities[cid].name

def print_all_cities(cities):
    print("\nAVAILABLE CITIES")
    for cid, city in cities.items():
        print(f"{cid:2d} → {city.name}")


# Display route names
def print_route_with_names(label, route, cities):
    print(f"\n{label} VISIT ORDER")
    print("City IDs:   ", route)
    names = [id_to_name(cities, cid) for cid in route]
    print("City Names: ", names)

# Travel Summary Output
def print_travel_info(label, cities, graph, weather_risk, route):
    print(f"\n{label} Travel Info")

    try:
        best_date, result = best_travel_date(
            cities, graph, weather_risk, route,
            start_window=dt.date(2025, 11, 1),
            end_window=dt.date(2025, 11, 30),
        )
    except ValueError as e:
        print("Unable to find a feasible start date within November 2025.")
        print("Reason:", e)
        return

    names = [id_to_name(cities, cid) for cid in route]
    print("Route (Names):")
    print(" → ".join(names))

    print("\nAssumptions / Constraints:")
    print(f"  Max speed (mph): {MAX_SPEED}")
    print(f"  Max driving hours/day: {MAX_HOURS_PER_DAY}")
    print(f"  Base MPG (flat ground): {BASE_MPG}")

    print("\nBest start date:", best_date)
    print("Total distance (miles): ", round(result["total_distance_miles"], 2))
    print("Total gas (gallons): ", round(result["total_gallons"], 2))
    print("Total driving hours: ", round(result["total_hours"], 2))

    if result["overall_mpg"] is not None:
        print("Overall MPG: ", round(result["overall_mpg"], 2))
    else:
        print("Overall MPG: N/A")

    print("Total travel risk: ", round(result["total_risk"], 2))
    print("Trip end date: ", result["end_date"])

    # Daily breakdown
    print("\nDaily Breakdown:")
    print("Date\t\tHours\tDistance\tGallons\t\tMPG\tRisk")

    daily_hours = dict(result["daily_hours"])
    daily_risk = dict(result["daily_risk"])
    daily_distance = dict(result["daily_distance"])
    daily_gallons = dict(result["daily_gallons"])
    daily_mpg = dict(result["daily_mpg"])

    all_dates = sorted(daily_hours.keys())

    for d in all_dates:
        h = daily_hours[d]
        dist = daily_distance[d]
        gal = daily_gallons[d]
        mpg = daily_mpg[d]
        r = daily_risk[d] if d in daily_risk else 0

        print(f"{d}:  {h:5.2f}h   {dist:7.2f}mi   {gal:6.2f}gal   "
              f"{(mpg if mpg else 0):5.2f}mpg   {r:4.2f}")

# BFS tree route builder
def reconstruct_tree_route(parent, start):
    route = [start]
    children = {}
    for v, p in enumerate(parent):
        if p != -1:
            children.setdefault(p, []).append(v)

    def dfs_tree(u):
        for v in children.get(u, []):
            route.append(v)
            dfs_tree(v)

    dfs_tree(start)
    return route

# Option 1 — User selects a city
def option_1_any_city_bfs_dfs():
    cities = load_cities()
    graph = load_graph(cities)
    weather_risk = load_weather_risk()

    # Print all cities first
    print_all_cities(cities)

    # Ask user for city name
    city_name = input("Enter start city name exactly as shown: ")
    start_id = name_to_id(cities, city_name)

    # BFS
    dist_bfs, parent_bfs = graph.bfs(start_id)
    bfs_route = reconstruct_tree_route(parent_bfs, start_id)
    stats_bfs = perf.profile(graph.bfs, args=[start_id])
    dist_bfs, parent_bfs = stats_bfs["result"]
    perf.print_stats("BFS", stats_bfs)
    perf_stats.append({
        "algorithm": "BFS",
        **stats_bfs
    })

    # DFS
    dfs_route = graph.dfs_recursive(start_id)
    stats_dfs = perf.profile(graph.dfs_recursive, args=[start_id])
    dfs_route = stats_dfs["result"]
    perf.print_stats("DFS", stats_dfs)
    perf_stats.append({
        "algorithm": "DFS",
        **stats_dfs
    })

    # Print routes
    print_route_with_names("BFS", bfs_route, cities)
    print_route_with_names("DFS", dfs_route, cities)

    # Travel results
    print_travel_info("BFS", cities, graph, weather_risk, bfs_route)
    print_travel_info("DFS", cities, graph, weather_risk, dfs_route)

# Option 2 — Random sampled cities
def option_2_random_cities_and_algorithms():
    cities = load_cities()
    graph = load_graph(cities)
    weather_risk = load_weather_risk()

    # Print all cities
    print_all_cities(cities)

    city_ids = list(cities.keys())
    k = random.randint(10, 20)
    sampled = random.sample(city_ids, k)

    print(f"\nRandomly selected {k} cities (IDs):", sampled)

    start = sampled[0]

    # Algorithms
    dist_bfs, parent_bfs = graph.bfs(start)
    dfs_order = graph.dfs_recursive(start)
    mst_prim, w_prim = graph.prim_mst(start)
    mst_kruskal, w_kruskal = graph.kruskal_mst()
    dist_bf, parent_bf = graph.bellman_ford(start)

    print("\nAlgorithms on sampled cities")

    print("BFS distance (hops):")
    for cid in sampled:
        print(f"  {cid}: {dist_bfs[cid]}")

    print("\nBellman-Ford weighted distances:")
    for cid in sampled:
        print(f"  {cid}: {dist_bf[cid]}")

    print("\nPrim MST total weight:", w_prim)
    print("Kruskal MST total weight:", w_kruskal)

    # BFS
    stats_bfs = perf.profile(graph.bfs, args=[start])
    dist_bfs, parent_bfs = stats_bfs["result"]
    perf.print_stats("BFS", stats_bfs)
    perf_stats.append({
        "algorithm": "BFS",
        **stats_bfs
    })

    # DFS
    stats_dfs = perf.profile(graph.dfs_recursive, args=[start])
    dfs_route = stats_dfs["result"]
    perf.print_stats("DFS", stats_dfs)
    perf_stats.append({
        "algorithm": "DFS",
        **stats_dfs
    })

    # Prim
    stats_prim = perf.profile(graph.prim_mst, args=[start])
    mst_prim, w_prim = stats_prim["result"]
    perf.print_stats("PRIM MST", stats_prim)
    perf_stats.append({
        "algorithm": "PRIM MST",
        **stats_prim
    })

    # Kruskal
    stats_kruskal = perf.profile(graph.kruskal_mst)
    mst_kruskal, w_kruskal = stats_kruskal["result"]
    perf.print_stats("KRUSKAL MST", stats_kruskal)
    perf_stats.append({
        "algorithm": "KRUSKAL MST",
        **stats_kruskal
    })

    # Bellman–Ford
    stats_bf = perf.profile(graph.bellman_ford, args=[start])
    dist_bf, parent_bf = stats_bf["result"]
    perf.print_stats("BELLMAN-FORD", stats_bf)
    perf_stats.append({
        "algorithm": "BELLMAN-FORD",
        **stats_bf
    })

    # Build BFS-based travel route
    bfs_route = reconstruct_tree_route(parent_bfs, start)
    travel_route = [cid for cid in bfs_route if cid in sampled]

    print("\nTravel route (IDs):", travel_route)

    print_travel_info("Random-Sampled BFS", cities, graph, weather_risk, travel_route)

# Program Menu
def main():
    while True:
        print("\nTravel Graph Project")
        print("1. Any city name → BFS/DFS travel & distance")
        print("2. Random 10–20 cities → algorithms + travel summary")
        print("3. Save Performance Logs for different graphic algorithms & exit")

        choice = input("Select an option: ").strip()
        if choice == "1":
            option_1_any_city_bfs_dfs()
        elif choice == "2":
            option_2_random_cities_and_algorithms()
        elif choice == "3":
            if perf_stats:
                perf.export_to_csv("graphic_algorithms_performance.csv", perf_stats)
            break
        else:
            print("Invalid choice. Try again.\n")

if __name__ == "__main__":
    main()