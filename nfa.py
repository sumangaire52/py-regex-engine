RE_REPEAT_LIMIT = 10

def nfa_make(node, start, end, id2node):
    if node is None:
        start.append((None, end))
    elif node == 'dot':
        start.append(('dot', end))
    elif isinstance(node, str):
        start.append((node, end))
    elif node[0] == 'cat':
        # connect the two subgraphs via a middle node
        middle = []
        id2node[id(middle)] = middle
        nfa_make(node[1], start, middle, id2node)
        nfa_make(node[2], middle, end, id2node)
    elif node[0] == 'split':
        # connect with both subgraphs
        nfa_make(node[1], start, end, id2node)
        nfa_make(node[2], start, end, id2node)
    elif node[0] == 'repeat':
        nfa_make_repeat(node, start, end, id2node)
    else:
        assert not 'reachable'


def nfa_make_repeat(node, start, end, id2node):
    # unpack
    _, node, rmin, rmax = node
    rmax = min(rmax, RE_REPEAT_LIMIT)
    # the door_in only leads to the subgraph,
    # it is necessary for repetitions to work.
    door_in = []
    # the door_out leads to either the door_in or the end.
    door_out = ('boss', door_in, end, rmin, rmax)
    id2node[id(door_in)] = door_in
    id2node[id(door_out)] = door_out
    # the subgraph between the door_in and the door_out
    nfa_make(node, door_in, door_out, id2node)
    # links from the start node
    start.append((None, door_in))
    if rmin == 0:
        start.append((None, end))


def re_full_match_nfa(node, text):
    # build the graph
    start, end = [], []
    id2node = {id(start): start, id(end): end}
    nfa_make(node, start, end, id2node)
    # explore and expand the initial position set
    node_set = {(id(start), ())}
    nfa_expand(node_set, id2node)
    for ch in text:
        # move to the next position set
        node_set = nfa_step(node_set, ch, id2node)
        nfa_expand(node_set, id2node)
    return (id(end), ()) in node_set


def nfa_step(node_set, ch, id2node):
    assert len(ch) == 1
    next_nodes = set()
    for node, kv in node_set:
        node = id2node[node]
        # only normal nodes since bosses were handled by the nfa_expand.
        assert not isinstance(node, tuple), 'unexpected boss'
        for cond, dst in node:
            if cond == 'dot' or cond == ch:
                next_nodes.add((id(dst), kv))
    return next_nodes


def nfa_expand(node_set, id2node):
    start = list(node_set)
    while start:
        new_nodes = []
        for node, kv in start:
            node = id2node[node]
            if isinstance(node, tuple) and node[0] == 'boss':
                # a boss, replace it with the outcome
                node_set.remove((id(node), kv))
                for dst, kv in nfa_boss(node, kv):
                    new_nodes.append((id(dst), kv))
            else:
                # explore new nodes via free links
                for cond, dst in node:
                    if cond is None:
                        new_nodes.append((id(dst), kv))

        # newly added nodes will be used for the next iteration
        start = []
        for state in new_nodes:
            if state not in node_set:
                node_set.add(state)
                start.append(state)


def nfa_boss(node, kv):
    _, door_in, end, rmin, rmax = node
    key = id(door_in)   # this is unique for identifying the boss
    kv, cnt = kv_increase(kv, key)
    if cnt < rmax:
        # repeat the level again
        yield (door_in, kv)
    if rmin <= cnt <= rmax:
        # pass the level
        yield (end, kv_delete(kv, key))


def kv_increase(kv, key):
    kv = dict(kv)
    val = kv.get(key, 0) + 1
    kv[key] = val
    return tuple(sorted(kv.items())), val

def kv_delete(kv, key):
    return tuple((k, v) for k, v in kv if k != key)