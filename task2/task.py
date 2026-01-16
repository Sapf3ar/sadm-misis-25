from typing import List, Tuple
import csv
from io import StringIO
import math


def main(s: str, e: str) -> Tuple[float, float]:
    """
    Args:
        s: CSV-строка ребер вида "parent,child\nparent,child\n..."
        e: Идентификатор корня (параметр оставлен в API; на расчеты не влияет)

    Returns:
        Tuple[float, float]: (энтропия, нормированная сложность), округление до 1 знака
    """
    csv_iter = csv.reader(StringIO(s.strip()))
    arc_list = []
    node_set = set()

    # Парсинг ребер и сбор множества вершин
    for cols in csv_iter:
        if len(cols) == 2:
            src, dst = cols[0].strip(), cols[1].strip()
            arc_list.append((src, dst))
            node_set.add(src)
            node_set.add(dst)

    ordered_nodes = sorted(node_set)
    node_count = len(ordered_nodes)
    idx_of = {name: pos for pos, name in enumerate(ordered_nodes)}

    # Пять булевых матриц отношений:
    # R1: parent -> child
    # R2: child -> parent
    # R3: ancestor -> descendant
    # R4: descendant -> ancestor
    # R5: sibling <-> sibling
    rel_r1 = [[False] * node_count for _ in range(node_count)]
    rel_r2 = [[False] * node_count for _ in range(node_count)]
    rel_r3 = [[False] * node_count for _ in range(node_count)]
    rel_r4 = [[False] * node_count for _ in range(node_count)]
    rel_r5 = [[False] * node_count for _ in range(node_count)]

    # Индексы для обходов по дереву/лесу
    kids_of = {name: [] for name in node_set}
    parent_of = {name: None for name in node_set}
    for src, dst in arc_list:
        kids_of[src].append(dst)
        parent_of[dst] = src

    # R1: прямые дуги parent->child
    for src, dst in arc_list:
        a, b = idx_of[src], idx_of[dst]
        rel_r1[a][b] = True

    # R2: обратные дуги child->parent
    for src, dst in arc_list:
        a, b = idx_of[src], idx_of[dst]
        rel_r2[b][a] = True

    def get_all_descendants(node, visited=None):
        """
        Возвращает множество всех достижимых потомков (транзитивно).
        visited нужен для защиты от циклов.
        """
        if visited is None:
            visited = set()
        if node in visited:
            return set()
        visited.add(node)

        out = set()
        for child in kids_of[node]:
            out.add(child)
            out |= get_all_descendants(child, visited)
        return out

    # R3: транзитивное отношение предок->потомок
    for name in node_set:
        i = idx_of[name]
        for descendant in get_all_descendants(name):
            j = idx_of[descendant]
            rel_r3[i][j] = True

    # R4: транзитивное отношение потомок->предок (через цепочку родителей)
    for name in node_set:
        j = idx_of[name]
        up = parent_of[name]
        while up is not None:
            i = idx_of[up]
            rel_r4[j][i] = True
            up = parent_of[up]

    # R5: отношения между сиблингами (общий родитель, разные вершины)
    groups_by_parent = {}
    for name in node_set:
        p = parent_of[name]
        if p is not None:
            groups_by_parent.setdefault(p, []).append(name)

    for group in groups_by_parent.values():
        for u in group:
            for v in group:
                if u != v:
                    rel_r5[idx_of[u]][idx_of[v]] = True

    relations = [rel_r1, rel_r2, rel_r3, rel_r4, rel_r5]

    # l[rel][j] = сколько i таких, что relation[i][j] == True
    in_counts = [[0] * node_count for _ in range(5)]
    for ridx, rel in enumerate(relations):
        for col in range(node_count):
            in_counts[ridx][col] = sum(1 for row in range(node_count) if rel[row][col])

    denom = node_count - 1

    entropy_sum = 0.0
    for col in range(node_count):
        for ridx in range(5):
            val = in_counts[ridx][col]
            prob = val / denom if denom > 0 else 0
            if prob > 0:
                entropy_sum += -prob * math.log2(prob)

    scale = 1.0 / (math.e * math.log(2))
    ref_entropy = scale * node_count * denom
    norm_score = entropy_sum / ref_entropy if ref_entropy > 0 else 0.0

    return (round(entropy_sum, 1), round(norm_score, 1))


if __name__ == "__main__":
    csv_data = "1,2\n1,3\n3,4\n3,5"
    result = main(csv_data, "1")
    print(f"Энтропия: {result[0]}, Нормированная сложность: {result[1]}")

