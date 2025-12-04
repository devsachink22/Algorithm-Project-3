import datetime as dt
from data_models import BASE_MPG, MAX_SPEED, MAX_HOURS_PER_DAY
import heapq

# Compute real distance + slope angle
def edge_real_distance(map_d_miles, sea_A_ft, sea_B_ft):
    if map_d_miles == 0:
        return 0.0, 0.0

    elevation_diff_miles = (sea_B_ft - sea_A_ft) / 5280.0
    if map_d_miles <= 0:
        return map_d_miles, 0.0

    tan_theta = elevation_diff_miles / map_d_miles
    real_distance = map_d_miles * (1.0 + tan_theta)
    return real_distance, tan_theta

# Adjust MPG based on slope
def adjusted_mpg(tan_theta):
    """
    Realistic MPG model:
    - Uphill: tanθ > 0 → mpg decreases
    - Downhill: tanθ < 0 → mpg increases
    """
    factor = (1 + tan_theta)
    if factor <= 0:
        return BASE_MPG  # avoid negative or zero mpg
    return BASE_MPG / factor


# Dijkstra shortest path (fallback)
def shortest_path_distance(graph, src, dst):
    n = len(graph.adj)
    INF = float("inf")
    dist = [INF] * n
    dist[src] = 0.0

    pq = [(0.0, src)]

    while pq:
        d, cur = heapq.heappop(pq)
        if d > dist[cur]:
            continue
        if cur == dst:
            return d

        for nbr, w in graph.adj[cur]:
            nd = d + w
            if nd < dist[nbr]:
                dist[nbr] = nd
                heapq.heappush(pq, (nd, nbr))

    return float("inf")



# Simulate trip with day splitting & dynamic MPG
def simulate_trip(
    cities,
    graph,
    weather_risk,
    route_cities,
    start_date: dt.date,
):
    total_real_distance = 0.0
    total_gallons = 0.0
    total_hours = 0.0

    daily_risk = []
    daily_hours = []
    daily_distance = []
    daily_gallons = []
    daily_mpg = []

    current_date = start_date
    hours_today = 0.0
    risk_today = 0.0
    dist_today = 0.0
    gallons_today = 0.0

    for i in range(len(route_cities) - 1):
        u = route_cities[i]
        v = route_cities[i + 1]

        # map distance (from adjacency)
        map_d = None
        for nbr, w in graph.adj[u]:
            if nbr == v:
                map_d = w
                break
        if map_d is None:
            map_d = shortest_path_distance(graph, u, v)

        # real distance + slope
        real_d, tan_theta = edge_real_distance(
            map_d, cities[u].sea_level_ft, cities[v].sea_level_ft
        )

        mpg_now = adjusted_mpg(tan_theta)
        gallons = real_d / mpg_now
        time_h = real_d / MAX_SPEED

        # Day splitting (strict 8-hour limit)
        while hours_today + time_h > MAX_HOURS_PER_DAY:
            remain = MAX_HOURS_PER_DAY - hours_today

            proportion = remain / time_h

            # partial allocation
            hours_today = MAX_HOURS_PER_DAY
            dist_portion = real_d * proportion
            gal_portion = gallons * proportion

            dist_today += dist_portion
            gallons_today += gal_portion

            r_u = weather_risk.get((u, current_date), 1.0)
            r_v = weather_risk.get((v, current_date), 1.0)
            risk_today += (r_u + r_v) / 2.0

            # close the day
            daily_hours.append((current_date, hours_today))
            daily_risk.append((current_date, risk_today))
            daily_distance.append((current_date, dist_today))
            daily_gallons.append((current_date, gallons_today))
            daily_mpg.append(
                (current_date, dist_today / gallons_today if gallons_today > 0 else None)
            )

            # move to next day
            current_date += dt.timedelta(days=1)
            hours_today = 0.0
            risk_today = 0.0
            dist_today = 0.0
            gallons_today = 0.0

            # remaining segment
            real_d -= dist_portion
            gallons -= gal_portion
            time_h -= remain

        # add remaining time normally
        hours_today += time_h
        total_hours += time_h

        r_u = weather_risk.get((u, current_date), 1.0)
        r_v = weather_risk.get((v, current_date), 1.0)
        risk_today += (r_u + r_v) / 2.0

        dist_today += real_d
        gallons_today += gallons

        total_real_distance += real_d
        total_gallons += gallons

    # Finish last day
    daily_hours.append((current_date, hours_today))
    daily_risk.append((current_date, risk_today))
    daily_distance.append((current_date, dist_today))
    daily_gallons.append((current_date, gallons_today))
    daily_mpg.append(
        (current_date, dist_today / gallons_today if gallons_today > 0 else None)
    )

    total_risk = sum(r for _, r in daily_risk)
    overall_mpg = (
        total_real_distance / total_gallons if total_gallons > 0 else None
    )

    return {
        "total_distance_miles": total_real_distance,
        "total_gallons": total_gallons,
        "total_hours": total_hours,
        "total_risk": total_risk,
        "overall_mpg": overall_mpg,
        "daily_hours": daily_hours,
        "daily_risk": daily_risk,
        "daily_distance": daily_distance,
        "daily_gallons": daily_gallons,
        "daily_mpg": daily_mpg,
        "end_date": current_date,
    }



# Best travel date (min total risk)
def best_travel_date(
    cities,
    graph,
    weather_risk,
    route_cities,
    start_window=dt.date(2025, 11, 1),
    end_window=dt.date(2025, 11, 30),
):

    best_date = None
    best_result = None

    d = start_window
    while d <= end_window:
        result = simulate_trip(cities, graph, weather_risk, route_cities, d)

        if result["end_date"] > end_window:
            d += dt.timedelta(days=1)
            continue

        if best_result is None or result["total_risk"] < best_result["total_risk"]:
            best_result = result
            best_date = d

        d += dt.timedelta(days=1)

    if best_result is None:
        raise ValueError("Route cannot be completed in the window.")

    return best_date, best_result