from collections import deque
import heapq

class Graph:
    """
    Weighted graph (undirected by default).
    Vertices are 0 - n-1.
    """
    def __init__(self, n_vertices: int):
        self.n = n_vertices
        self.adj = [[] for _ in range(n_vertices)]  # adj[u] = [(v, weight), ...]
        self.edges = []  # (u, v, weight)

    def add_edge(self, u: int, v: int, w: float = 1.0, undirected: bool = True):
        self.adj[u].append((v, w))
        self.edges.append((u, v, w))
        if undirected:
            self.adj[v].append((u, w))
            self.edges.append((v, u, w))

    # 1) BFS
    def bfs(self, start: int):
        INF = float("inf")
        dist = [INF] * self.n
        parent = [-1] * self.n
        visited = [False] * self.n

        q = deque([start])
        visited[start] = True
        dist[start] = 0

        while q:
            u = q.popleft()
            for v, _ in self.adj[u]:
                if not visited[v]:
                    visited[v] = True
                    dist[v] = dist[u] + 1  # in number of edges (unweighted)
                    parent[v] = u
                    q.append(v)

        return dist, parent

    # 2) DFS
    def dfs_recursive(self, start: int):
        visited = [False] * self.n
        order = []

        def _dfs(u: int):
            visited[u] = True
            order.append(u)
            for v, _ in self.adj[u]:
                if not visited[v]:
                    _dfs(v)

        _dfs(start)
        return order

    def dfs_iterative(self, start: int):
        visited = [False] * self.n
        order = []
        stack = [start]

        while stack:
            u = stack.pop()
            if not visited[u]:
                visited[u] = True
                order.append(u)
                for v, _ in reversed(self.adj[u]):
                    if not visited[v]:
                        stack.append(v)
        return order

    # 3) Prim's MST
    def prim_mst(self, start: int = 0):
        visited = [False] * self.n
        mst_edges = []
        total_weight = 0.0

        heap = [(0.0, -1, start)]  # (weight, from, to)

        while heap:
            w, u, v = heapq.heappop(heap)
            if visited[v]:
                continue
            visited[v] = True

            if u != -1:
                mst_edges.append((u, v, w))
                total_weight += w

            for nxt, wt in self.adj[v]:
                if not visited[nxt]:
                    heapq.heappush(heap, (wt, v, nxt))

        if len(mst_edges) != self.n - 1:
            print("Warning: graph may not be fully connected.")
        return mst_edges, total_weight

    # 4) Kruskal's MST
    def kruskal_mst(self):
        parent = list(range(self.n))
        rank = [0] * self.n

        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb:
                return False
            if rank[ra] < rank[rb]:
                parent[ra] = rb
            elif rank[ra] > rank[rb]:
                parent[rb] = ra
            else:
                parent[rb] = ra
                rank[ra] += 1
            return True

        # deduplicate undirected edges
        unique_edges = {}
        for u, v, w in self.edges:
            a, b = min(u, v), max(u, v)
            key = (a, b)
            if key not in unique_edges or w < unique_edges[key]:
                unique_edges[key] = w

        sorted_edges = sorted(
            [(u, v, w) for (u, v), w in unique_edges.items()],
            key=lambda x: x[2]
        )

        mst_edges = []
        total_weight = 0.0

        for u, v, w in sorted_edges:
            if union(u, v):
                mst_edges.append((u, v, w))
                total_weight += w

        return mst_edges, total_weight

    # 5) Bellman-Ford
    def bellman_ford(self, source: int):
        INF = float("inf")
        dist = [INF] * self.n
        parent = [-1] * self.n
        dist[source] = 0.0

        # relax edges |V| - 1 times
        for _ in range(self.n - 1):
            updated = False
            for u, v, w in self.edges:
                if dist[u] != INF and dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    parent[v] = u
                    updated = True
            if not updated:
                break

        # check negative cycles
        for u, v, w in self.edges:
            if dist[u] != INF and dist[u] + w < dist[v]:
                raise ValueError("Negative-weight cycle detected")

        return dist, parent

if __name__ == "__main__":
    # tiny demo
    g = Graph(5)
    g.add_edge(0, 1, 2)
    g.add_edge(0, 2, 4)
    g.add_edge(1, 2, 1)
    g.add_edge(1, 3, 7)
    g.add_edge(2, 4, 3)
    g.add_edge(3, 4, 1)
    print("BFS:", g.bfs(0))
    print("DFS recursive:", g.dfs_recursive(0))
    print("Prim MST:", g.prim_mst(0))
    print("Kruskal MST:", g.kruskal_mst())
    print("Bellman-Ford:", g.bellman_ford(0))