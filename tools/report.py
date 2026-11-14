#!/usr/bin/env python3
"""Recomputes every number used in Steps 3d, 4 and 5 of the report.

Usage (from the repository root):  python tools/report.py
Needs:  objdumps/objdump_O0.txt, objdump_O1.txt, objdump_v2_O0.txt
Writes: traces/trace.csv, trace_O1.csv, trace_v2.csv; caches/cache_first30.csv,
        cache_full.csv; results.txt; screenshots/design_space.png (needs matplotlib)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rvsim, cachesim

F_GHZ, T1, T2, NC, N = 1.8, 1, 20, 8, 42          # personal model parameters (assumptions)
TAU = 1 / F_GHZ                                    # ns
CPI = dict(alu=1, mul=3, load=1, store=1, branch=2)  # model CPI table of the brief
out = []
def p(s=""):
    print(s); out.append(s)

def write_trace(sim, syms, path):
    o0 = syms.get("mark_below") == 0x1035C and "v2" not in path
    with open(path, "w", newline="\n") as f:
        f.write("sira,RW,adres_hex,boyut,c_satiri,stack_mi\n")
        for i, (pc, rw, a, sz) in enumerate(sim.trace, 1):
            line = rvsim.c_line(pc, rvsim.LINES_O0) if o0 else 0
            f.write(f"{i},{rw},0x{a:08X},{sz},{line},{int(a >= 0x70000000)}\n")

def ts(H):
    return H * T1 + (1 - H) * (T1 + T2)

runs = {}
for d in ("traces", "caches", "screenshots"):
    os.makedirs(d, exist_ok=True)
for name, od, tr in (("O0", "objdumps/objdump_O0.txt", "traces/trace.csv"),
                     ("O1", "objdumps/objdump_O1.txt", "traces/trace_O1.csv"),
                     ("v2", "objdumps/objdump_v2_O0.txt", "traces/trace_v2.csv")):
    sim, syms = rvsim.run(od)
    write_trace(sim, syms, tr)
    trace = cachesim.read_trace(tr)
    runs[name] = (sim, syms, trace, cachesim.simulate(trace))

sim, syms, trace, c = runs["O0"]
p("== 4a trace (-O0) ==")
stack = sum(a >= 0x70000000 for _, a in trace)
g0 = syms["grades"]
arr = sum(g0 <= a < g0 + 4 * N for _, a in trace)
p(f"references {len(trace)}, loads {sum(r == 'R' for r, _ in trace)}, "
  f"stores {sum(r == 'W' for r, _ in trace)}, stack {stack}, grades[] {arr}, "
  f"other globals {len(trace) - stack - arr}")

p("\n== 4c/4d personal cache: 256 B, 8 B line, 2-way, 16 sets, LRU, write-back ==")
c30 = cachesim.simulate(trace, limit=30)
for label, r in (("first 30", c30), ("whole trace", c)):
    p(f"{label}: refs {r['refs']}, hits {r['hits']}, misses {r['misses']}, "
      f"H {r['H']:.4f}, memory writes {r['mem_writes']}, dirty lines left {r['dirty_left']}")
for path, r in (("caches/cache_first30.csv", c30), ("caches/cache_full.csv", c)):
    with open(path, "w", newline="\n") as f:
        f.write("sira,RW,adres_hex,tag_hex,set,word,sonuc,cikan_blok,daha_once_cachete\n")
        for row in r["rows"]:
            f.write(",".join(str(v) for v in row) + "\n")
wt = cachesim.simulate(trace, policy="wt")
p(f"write-through would need {wt['mem_writes']} memory writes; write-back needs "
  f"{c['mem_writes']} + {c['dirty_left']} final flushes")

p("\n== 4e design space (cache size 256 B) ==")
maps = [(n, cachesim.simulate(trace, 256, 8, w)) for n, w in
        (("Direct", 1), ("2-way", 2), ("4-way", 4), ("Fully assoc.", 0))]
lines = [(f"{l} B", cachesim.simulate(trace, 256, l, 2)) for l in (8, 16, 32, 64)]
for n, r in maps + lines:
    p(f"{n:13} hits {r['hits']:5} misses {r['misses']:4} H {r['H']:.4f}  T_s {ts(r['H']):.3f}")

p("\n== 4f ==")
Ts = ts(c["H"])
p(f"T_s = {c['H']:.4f}*{T1} + {1 - c['H']:.4f}*{T1 + T2} = {Ts:.4f} cycles; "
  f"speedup vs no cache = {T2}/{Ts:.4f} = {T2 / Ts:.2f}")

p("\n== 4g (main_v2.c) ==")
s2, y2, t2, c2 = runs["v2"]
res = lambda s, y: ([s.rd32(y['bucket'] + 4 * i) for i in range(5)], s.rd32(y['mean']),
                    s.rd32(y['below_count']), s.rd32(y['pass_count']))
p(f"Y7 before {res(sim, syms)}  after {res(s2, y2)}")
p(f"before: refs {c['refs']} misses {c['misses']} H {c['H']:.4f} T_s {Ts:.4f}")
p(f"after : refs {c2['refs']} misses {c2['misses']} H {c2['H']:.4f} T_s {ts(c2['H']):.4f}  Ic {s2.ic}")

p("\n== 5a ==")
perf = {}
for name in ("O0", "O1"):
    s, y, t, cc = runs[name]
    cyc = sum(CPI[k] * v for k, v in s.count.items())
    cpi = cyc / s.ic
    m = len(t) / s.ic
    k_c = ts(cc["H"])
    T_plain = cyc * TAU
    T_nc = s.ic * (cpi + m * T2) * TAU
    T_c = s.ic * (cpi + m * k_c) * TAU
    perf[name] = (T_plain, T_nc, T_c, cpi)
    p(f"-{name}: Ic {s.ic} {s.count}  CPI {cpi:.4f}  T {T_plain:.1f} ns  "
      f"MIPS {F_GHZ * 1000 / cpi:.1f}  m {m:.4f}  H {cc['H']:.4f} T_s {k_c:.4f}  "
      f"T(no cache) {T_nc:.1f} ns  T(cache) {T_c:.1f} ns")
p(f"speedup O0->O1 (cache) {perf['O0'][2] / perf['O1'][2]:.3f}; "
  f"(no memory effect) {perf['O0'][0] / perf['O1'][0]:.3f}")
p(f"speedup no cache -> cache (-O0) {perf['O0'][1] / perf['O0'][2]:.3f}")

# Amdahl: share of the second loop (0x102A8-0x10340 + mark_below) in T (cache, -O0)
cls_of = {}
code, _ = rvsim.load_objdump("objdumps/objdump_O0.txt")
probe = rvsim.Sim(code, syms["main"])
refs_pc = {}
for pc, rw, a, sz in sim.trace:
    refs_pc[pc] = refs_pc.get(pc, 0) + 1
def klass(w):
    op, f7 = w & 0x7F, w >> 25
    return ("load" if op == 0x03 else "store" if op == 0x23 else
            "branch" if op in (0x63, 0x6F, 0x67) else
            "mul" if op == 0x33 and f7 == 1 else "alu")
tot = par = 0.0
for pc, n in sim.per_pc.items():
    t = n * CPI[klass(code[pc])] + refs_pc.get(pc, 0) * Ts
    tot += t
    if 0x102A8 <= pc <= 0x10340 or pc >= 0x1035C:
        par += t
f = par / tot
p(f"Amdahl: parallel share f = {par:.1f}/{tot:.1f} = {f:.4f}; "
  f"speedup(Nc={NC}) = {1 / ((1 - f) + f / NC):.3f}; limit = {1 / (1 - f):.3f}")

p("\n== 3d ==")
data = N * 4
for hdr, ecrc in ((12, 0), (16, 4)):
    total = 1 + 2 + hdr + data + ecrc + 4 + 1
    p(f"PCIe: header {hdr}, ECRC {ecrc}: total {total} octets, efficiency "
      f"{data / total:.4f}, with 128b/130b {data / total * 128 / 130:.4f}")

open("results.txt", "w", newline="\n").write("\n".join(out) + "\n")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
    for ax, series, title in ((axes[0], maps, "Mapping (line = 8 B)"),
                              (axes[1], lines, "Line size (2-way)")):
        names = [n for n, _ in series]
        vals = [100 * r["H"] for _, r in series]
        ax.plot(names, vals, color="#2a78d6", linewidth=2, marker="o", markersize=8)
        for xi, v in enumerate(vals):
            below = xi == 0 and vals[1] > v      # keep the label clear of a rising line
            ax.text(xi, v - 0.4 if below else v + 0.35, f"{v:.2f}", ha="center",
                    va="top" if below else "bottom", fontsize=9, color="#222222")
        ax.margins(x=0.15)
        ax.set_title(title, fontsize=10, loc="left")
        ax.set_ylim(90, 100)
        ax.grid(axis="y", color="#dddddd", linewidth=0.8)
        ax.set_axisbelow(True)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(length=0, labelsize=9)
    axes[0].set_ylabel("Hit ratio H (%)", fontsize=9)
    fig.suptitle("Data cache design space, 256 B cache, -O0 trace (1755 references)",
                 fontsize=10, x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig("screenshots/design_space.png", dpi=150)
except ImportError:
    pass
