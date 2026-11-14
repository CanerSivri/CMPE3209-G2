#!/usr/bin/env python3
"""Data cache simulator for the CMPE3209 project (no dependencies).

Model (brief, Sec. 2 and Step 4): only data references are simulated;
LRU replacement in associative caches; write-allocate on a write miss;
write-back (a memory write happens only when a dirty line is evicted) or
write-through (every store is a memory write).

Usage:
  python tools/cachesim.py trace.csv                         personal config, whole trace
  python tools/cachesim.py trace.csv --limit 30 --detail cache_first30.csv --state
  python tools/cachesim.py trace.csv --detail cache_full.csv
  python tools/cachesim.py trace.csv --sweep                 4e design space
  python tools/cachesim.py trace.csv --size 256 --line 16 --ways 4 --policy wb
"""
import argparse
import csv


def read_trace(path):
    with open(path, newline="") as f:
        return [(r["RW"], int(r["adres_hex"], 16)) for r in csv.DictReader(f)]


def simulate(trace, size=256, line=8, ways=2, policy="wb", limit=None):
    """ways = 0 means fully associative. Returns totals, per-reference rows, final state."""
    lines = size // line
    if ways == 0:
        ways = lines
    sets = lines // ways
    cache = [[] for _ in range(sets)]   # per set: [tag, dirty] entries, least recently used first
    seen = set()                        # blocks that have been in the cache before
    hits = misses = mem_writes = 0
    rows = []
    for n, (rw, addr) in enumerate(trace[:limit], 1):
        block = addr // line
        s, tag, word = block % sets, block // sets, addr % line
        entry = next((e for e in cache[s] if e[0] == tag), None)
        evicted = "-"
        if entry is not None:
            hits += 1
            result = "Hit"
            cache[s].remove(entry)
        else:
            misses += 1
            result = "Miss"
            if len(cache[s]) == ways:   # set is full: evict the least recently used line
                old_tag, old_dirty = cache[s].pop(0)
                evicted = f"0x{(old_tag * sets + s) * line:08X}"
                if old_dirty:
                    evicted += " (dirty)"
                    if policy == "wb":
                        mem_writes += 1
            entry = [tag, False]
        if rw == "W":
            if policy == "wt":
                mem_writes += 1
            else:
                entry[1] = True
        cache[s].append(entry)          # most recently used goes last
        rows.append((n, rw, f"0x{addr:08X}", f"0x{tag:07X}", s, word, result, evicted,
                     "yes" if block in seen else "no"))
        seen.add(block)
    total = hits + misses
    return dict(refs=total, hits=hits, misses=misses, H=hits / total,
                mem_writes=mem_writes, sets=sets, ways=ways, line=line,
                cache=cache, rows=rows,
                dirty_left=sum(e[1] for st in cache for e in st))


def print_state(r):
    print("set way valid tag        dirty LRU(0=least recent) block")
    for s, st in enumerate(r["cache"]):
        for order, (tag, dirty) in enumerate(st):
            base = (tag * r["sets"] + s) * r["line"]
            print(f"{s:3} {order:3}   1   0x{tag:07X}  {int(dirty)}     {order}"
                  f"                   0x{base:08X}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trace")
    ap.add_argument("--size", type=int, default=256)
    ap.add_argument("--line", type=int, default=8)
    ap.add_argument("--ways", type=int, default=2, help="1 = direct, 0 = fully associative")
    ap.add_argument("--policy", choices=["wb", "wt"], default="wb")
    ap.add_argument("--limit", type=int, help="only the first N references")
    ap.add_argument("--detail", help="write one row per reference to this CSV")
    ap.add_argument("--state", action="store_true", help="print the cache contents at the end")
    ap.add_argument("--sweep", action="store_true", help="design space of Step 4e")
    args = ap.parse_args()
    trace = read_trace(args.trace)

    if args.sweep:
        print("mapping series (line = %d B)" % args.line)
        for name, w in (("direct", 1), ("2-way", 2), ("4-way", 4), ("fully assoc.", 0)):
            r = simulate(trace, args.size, args.line, w, args.policy)
            print(f"  {name:13} hit {r['hits']:5} miss {r['misses']:4} H {r['H']:.4f}")
        print("line size series (%d-way)" % args.ways)
        for ln in (8, 16, 32, 64):
            r = simulate(trace, args.size, ln, args.ways, args.policy)
            print(f"  {ln:3} B         hit {r['hits']:5} miss {r['misses']:4} H {r['H']:.4f}")
        return

    r = simulate(trace, args.size, args.line, args.ways, args.policy, args.limit)
    print(f"cache {args.size} B, line {args.line} B, {r['ways']}-way, {r['sets']} sets, "
          f"{'write-back' if args.policy == 'wb' else 'write-through'}, LRU, write-allocate")
    print(f"references {r['refs']}, hits {r['hits']}, misses {r['misses']}, H = {r['H']:.4f}")
    print(f"memory writes {r['mem_writes']}"
          + (f" (+ {r['dirty_left']} dirty lines still in the cache at the end)"
             if args.policy == "wb" else ""))
    if args.state:
        print_state(r)
    if args.detail:
        with open(args.detail, "w", newline="\n") as f:
            f.write("sira,RW,adres_hex,tag_hex,set,word,sonuc,cikan_blok,daha_once_cachete\n")
            for row in r["rows"]:
                f.write(",".join(str(v) for v in row) + "\n")
        print("detail written to", args.detail)


if __name__ == "__main__":
    main()
