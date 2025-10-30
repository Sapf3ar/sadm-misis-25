
from typing import List, Tuple, Dict
def main(s: str, e: str) -> Tuple[
    List[List[bool]],
    List[List[bool]],
    List[List[bool]],
    List[List[bool]],
    List[List[bool]]
]:
    edges_raw = []
    s = (s or "").strip()
    if s:
        for line in s.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            u, v = parts[0].strip(), parts[1].strip()
            edges_raw.append((u, v))
    nodes_set = set()
    for u, v in edges_raw:
        nodes_set.add(u)
        nodes_set.add(v)
    nodes_set.add(e)

    def _is_int_like(x: str) -> bool:
        try:
            int(x)
            return True
        except Exception:
            return False

    nodes = sorted(nodes_set, key=lambda x: int(x))

    index: Dict[str, int] = {node: i for i, node in enumerate(nodes)}
    n = len(nodes)

    def _zeros() -> List[List[bool]]:
        return [[False] * n for _ in range(n)]

    parent = _zeros()      
    child = _zeros()      
    ancestor = _zeros()  
    descendant = _zeros() 
    sibling = _zeros()   

    adj: List[List[int]] = [[] for _ in range(n)]   
    rev_adj: List[List[int]] = [[] for _ in range(n)]

    for u_label, v_label in edges_raw:
        u = index[u_label]
        v = index[v_label]
        parent[u][v] = True
        child[v][u] = True
        adj[u].append(v)
        rev_adj[v].append(u)

    for u in range(n):
        stack = list(adj[u])
        seen = [False] * n
        for v0 in stack:
            seen[v0] = True
        while stack:
            v = stack.pop()
            ancestor[u][v] = True  
            for w in adj[v]:
                if not seen[w]:
                    seen[w] = True
                    stack.append(w)

    for i in range(n):
        for j in range(n):
            if ancestor[i][j]:
                descendant[j][i] = True

    for p in range(n):
        children = adj[p]
        if len(children) >= 2:
            for i in range(len(children)):
                a = children[i]
                for j in range(len(children)):
                    if i == j:
                        continue
                    b = children[j]
                    sibling[a][b] = True

    return parent, child, ancestor, descendant, sibling
