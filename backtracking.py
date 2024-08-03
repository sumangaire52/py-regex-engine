RE_REPEAT_LIMIT=10

def match_backtrack(node, text, idx):
    if node is None:
        yield idx   # empty string
    elif node == 'dot':
        if idx < len(text):
            yield idx + 1
    elif isinstance(node, str):
        assert len(node) == 1   # single char
        if idx < len(text) and text[idx] == node:
            yield idx + 1
    elif node[0] == 'cat':
        # the `yield from` is equivalent to:
        # for idx1 in match_backtrack_concat(node, text, idx):
        #     yield idx1
        yield from match_backtrack_concat(node, text, idx)
    elif node[0] == 'split':
        yield from match_backtrack(node[1], text, idx)
        yield from match_backtrack(node[2], text, idx)
    elif node[0] == 'repeat':
        yield from match_backtrack_repeat(node, text, idx)
    else:
        assert not 'reachable'


def match_backtrack_concat(node, text, idx):
    met = set()
    for idx1 in match_backtrack(node[1], text, idx):
        if idx1 in met:
            continue    # duplication
        met.add(idx1)
        yield from match_backtrack(node[2], text, idx1)


def match_backtrack_repeat(node, text, idx):
    _, node, rmin, rmax = node
    rmax = min(rmax, RE_REPEAT_LIMIT)
    # the output is buffered and reversed later
    output = []
    if rmin == 0:
        # don't have to match anything
        output.append(idx)
    # positions from the previous step
    start = {idx}
    # try every possible repetition number
    for i in range(1, rmax + 1):
        found = set()
        for idx1 in start:
            for idx2 in match_backtrack(node, text, idx1):
                found.add(idx2)
                if i >= rmin:
                    output.append(idx2)
        # TODO: bail out if the only match is of zero-length
        if not found:
            break
        start = found
    # repetition is greedy, output the most repetitive match first.
    yield from reversed(output)


def re_full_match_bt(node, text):
    for idx in match_backtrack(node, text, 0):
        # idx is the size of the matched prefix
        if idx == len(text):
            # NOTE: the greedy aspect of regexes seems to be irrelevant
            #       if we are only accepting the fully matched text.
            return True
    return False