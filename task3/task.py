import re
import json
import heapq


def sanitize_json(text: str) -> str:
    prev = None
    cur = text
    while prev != cur:
        prev = cur
        cur = re.sub(r",\s*([\]}])", r"\1", cur)
    return cur.strip()


def normalize_ranking(ranking):
    out = []
    seen = set()
    for entry in ranking:
        group = entry if isinstance(entry, list) else [entry]
        block = []
        for v in group:
            seen.add(v)
            block.append(v)
        out.append(block)
    return out


def cluster_positions(groups):
    pos = {}
    for i, g in enumerate(groups):
        for x in g:
            pos[x] = i
    return pos


def not_worse_matrix(groups, items):
    pos = cluster_positions(groups)
    n = len(items)
    index = {x: i for i, x in enumerate(items)}
    mat = [[0] * n for _ in range(n)]
    for a in items:
        ia = index[a]
        pa = pos[a]
        row = mat[ia]
        for b in items:
            row[index[b]] = 1 if pa <= pos[b] else 0
    return mat


def contradiction_kernel(mat_a, mat_b, items):
    n = len(items)
    pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            a_ij, a_ji = mat_a[i][j], mat_a[j][i]
            b_ij, b_ji = mat_b[i][j], mat_b[j][i]

            a_i_lt_j = (a_ij == 1 and a_ji == 0)
            a_j_lt_i = (a_ji == 1 and a_ij == 0)
            b_i_lt_j = (b_ij == 1 and b_ji == 0)
            b_j_lt_i = (b_ji == 1 and b_ij == 0)

            if (a_i_lt_j and b_j_lt_i) or (a_j_lt_i and b_i_lt_j):
                pairs.append([items[i], items[j]])
    return pairs


def transitive_closure(adj):
    n = len(adj)
    reach = [row[:] for row in adj]
    for k in range(n):
        rk = reach[k]
        for i in range(n):
            if reach[i][k]:
                ri = reach[i]
                for j in range(n):
                    if rk[j] and not ri[j]:
                        ri[j] = 1
    return reach


def merge_equivalences(eq_star, items):
    n = len(items)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def unite(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            if eq_star[i][j] and eq_star[j][i]:
                unite(i, j)

    comps = {}
    for i in range(n):
        r = find(i)
        comps.setdefault(r, []).append(items[i])

    groups = [sorted(v) for v in comps.values()]
    groups.sort(key=lambda g: g[0])
    return groups


def cluster_compare(left, right, rel, index):
    saw_lr = False
    saw_rl = False
    for x in left:
        ix = index[x]
        for y in right:
            iy = index[y]
            if rel[ix][iy] == 1 and rel[iy][ix] == 0:
                saw_lr = True
            elif rel[iy][ix] == 1 and rel[ix][iy] == 0:
                saw_rl = True
            if saw_lr and saw_rl:
                return 0
    if saw_lr and not saw_rl:
        return 1
    if saw_rl and not saw_lr:
        return -1
    return 0


def topo_sort_clusters(groups, rel, index):
    m = len(groups)
    graph = [set() for _ in range(m)]
    indeg = [0] * m

    for i in range(m):
        for j in range(i + 1, m):
            cmpv = cluster_compare(groups[i], groups[j], rel, index)
            if cmpv == 1:
                graph[i].add(j)
            elif cmpv == -1:
                graph[j].add(i)

    for u in range(m):
        for v in graph[u]:
            indeg[v] += 1

    heap = []
    for i in range(m):
        if indeg[i] == 0:
            heapq.heappush(heap, (groups[i][0], i))

    order = []
    while heap:
        _, u = heapq.heappop(heap)
        order.append(u)
        for v in graph[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                heapq.heappush(heap, (groups[v][0], v))

    if len(order) != m:
        order = sorted(range(m), key=lambda i: groups[i][0])

    return [groups[i] for i in order]


def main(json_a: str, json_b: str) -> str:
    raw_a = json.loads(sanitize_json(json_a))
    raw_b = json.loads(sanitize_json(json_b))

    groups_a = normalize_ranking(raw_a)
    groups_b = normalize_ranking(raw_b)

    items = sorted({x for g in groups_a for x in g})
    n = len(items)
    index = {x: i for i, x in enumerate(items)}

    mat_a = not_worse_matrix(groups_a, items)
    mat_b = not_worse_matrix(groups_b, items)

    core = contradiction_kernel(mat_a, mat_b, items)

    rel = [[mat_a[i][j] & mat_b[i][j] for j in range(n)] for i in range(n)]

    for u, v in core:
        iu, iv = index[u], index[v]
        rel[iu][iv] = 1
        rel[iv][iu] = 1

    eq = [[rel[i][j] & rel[j][i] for j in range(n)] for i in range(n)]
    for i in range(n):
        eq[i][i] = 1

    eq_star = transitive_closure(eq)
    merged = merge_equivalences(eq_star, items)
    ordered = topo_sort_clusters(merged, rel, index)

    packed = [g[0] if len(g) == 1 else g for g in ordered]
    return json.dumps(packed, ensure_ascii=False, separators=(",", ":"))


if __name__ == "__main__":
    A = "[1,[2,3],4,[5,6,7],8,9,10]"
    B = "[[1,2],[3,4,5],6,7,9,[8,10]]"
    print(main(A, B))

