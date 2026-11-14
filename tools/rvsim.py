#!/usr/bin/env python3
"""Minimal RV32IM simulator for the CMPE3209 project (no dependencies).

Loads the program from an `objdump -d` text file (address + hex word per
line), runs it from <main> the way Ripes does (sp = 0x7ffffff0, ra = 0),
and stops when main returns. Produces:
  * the data address trace (every load and store)  -> trace CSV
  * dynamic instruction counts per class (ALU, multiply, load, store,
    branch/jump)                                    -> printed
  * the values of the global result variables       -> printed

Usage:
  python tools/rvsim.py objdump_O0.txt --trace trace.csv
  python tools/rvsim.py objdump_O1.txt
"""
import argparse, re, sys

SP_INIT = 0x7FFFFFF0          # Ripes initial stack pointer
M32 = 0xFFFFFFFF

def sx(v, bits):
    v &= (1 << bits) - 1
    return v - (1 << bits) if v >> (bits - 1) else v

def s32(v):
    return sx(v, 32)

def load_objdump(path):
    code, syms = {}, {}
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.match(r"^([0-9a-f]{8}) <(\w+)>:", line)
        if m:
            syms[m.group(2)] = int(m.group(1), 16)
        m = re.match(r"^\s+([0-9a-f]+):\s+([0-9a-f]{8})\s", line)
        if m:
            code[int(m.group(1), 16)] = int(m.group(2), 16)
        for a, n in re.findall(r"# ([0-9a-f]+) <(\w+)>", line):
            syms.setdefault(n, int(a, 16))
    return code, syms

# C line of each -O0 instruction address range (from asm_O0.s / objdump_O0.txt)
LINES_O0 = [(0x10094,12),(0x100A4,13),(0x100B0,14),(0x100EC,15),(0x100F0,17),
 (0x100F8,18),(0x10118,19),(0x1014C,20),(0x10168,21),(0x10178,23),(0x10184,24),
 (0x10198,26),(0x101A4,27),(0x101C4,29),(0x101D0,30),(0x101F0,32),(0x101FC,33),
 (0x1021C,35),(0x10228,36),(0x10248,39),(0x10264,17),(0x1027C,43),(0x102A0,45),
 (0x102A8,46),(0x102DC,47),(0x102FC,48),(0x10318,49),(0x1032C,45),(0x10344,52),
 (0x1034C,53),(0x1035C,55),(0x10374,56),(0x10380,57),(0x1038C,59),(0x10390,60)]

def c_line(pc, table):
    line = 0
    for a, l in table:
        if pc >= a:
            line = l
    return line

class Sim:
    def __init__(self, code, entry):
        self.code, self.pc = code, entry
        self.x = [0] * 32
        self.x[2] = SP_INIT
        self.mem = {}                       # byte-addressed data memory
        self.trace = []                     # (pc, 'R'/'W', addr, size)
        self.count = dict(alu=0, mul=0, load=0, store=0, branch=0)
        self.per_pc = {}                    # pc -> executions
        self.ic = 0

    def rd32(self, a):
        return sum(self.mem.get(a + i, 0) << (8 * i) for i in range(4))

    def wr32(self, a, v):
        for i in range(4):
            self.mem[a + i] = (v >> (8 * i)) & 0xFF

    def step(self):
        pc, x = self.pc, self.x
        w = self.code[pc]
        op, rd, f3 = w & 0x7F, (w >> 7) & 31, (w >> 12) & 7
        rs1, rs2, f7 = (w >> 15) & 31, (w >> 20) & 31, w >> 25
        a, b = x[rs1], x[rs2]
        npc, res, cls = pc + 4, None, "alu"
        if op == 0x37:   res = w & 0xFFFFF000                       # lui
        elif op == 0x17: res = (pc + (w & 0xFFFFF000)) & M32        # auipc
        elif op == 0x6F:                                            # jal
            imm = sx(((w >> 31) << 20) | (((w >> 12) & 0xFF) << 12) |
                     (((w >> 20) & 1) << 11) | (((w >> 21) & 0x3FF) << 1), 21)
            res, npc, cls = pc + 4, (pc + imm) & M32, "branch"
        elif op == 0x67:                                            # jalr
            res, npc, cls = pc + 4, (a + sx(w >> 20, 12)) & M32 & ~1, "branch"
        elif op == 0x63:                                            # branches
            imm = sx(((w >> 31) << 12) | (((w >> 7) & 1) << 11) |
                     (((w >> 25) & 0x3F) << 5) | (((w >> 8) & 0xF) << 1), 13)
            t = {0: a == b, 1: a != b, 4: s32(a) < s32(b), 5: s32(a) >= s32(b),
                 6: a < b, 7: a >= b}[f3]
            if t: npc = (pc + imm) & M32
            cls = "branch"
        elif op == 0x03 and f3 == 2:                                # lw
            addr = (a + sx(w >> 20, 12)) & M32
            res, cls = self.rd32(addr), "load"
            self.trace.append((pc, "R", addr, 4))
        elif op == 0x23 and f3 == 2:                                # sw
            addr = (a + sx(((w >> 25) << 5) | rd, 12)) & M32
            self.wr32(addr, b); cls = "store"
            self.trace.append((pc, "W", addr, 4))
        elif op == 0x13:                                            # op-imm
            imm = sx(w >> 20, 12); sh = (w >> 20) & 31
            res = {0: a + imm, 1: a << sh, 2: int(s32(a) < imm),
                   3: int(a < (imm & M32)), 4: a ^ imm,
                   5: (s32(a) >> sh) if f7 == 0x20 else (a >> sh),
                   6: a | imm, 7: a & imm}[f3] & M32
        elif op == 0x33 and f7 == 1:                                # M extension
            sa, sb = s32(a), s32(b)
            def div(p, q): return -1 if q == 0 else int(abs(p) // abs(q)) * (1 if (p < 0) == (q < 0) else -1)
            def rem(p, q): return p if q == 0 else p - q * div(p, q)
            res = {0: sa * sb, 1: (sa * sb) >> 32, 2: (sa * b) >> 32,
                   3: (a * b) >> 32, 4: div(sa, sb),
                   5: M32 if b == 0 else a // b, 6: rem(sa, sb),
                   7: a if b == 0 else a % b}[f3] & M32
            cls = "mul"
        elif op == 0x33:                                            # op
            sh = b & 31
            res = {0: (a - b) if f7 == 0x20 else (a + b), 1: a << sh,
                   2: int(s32(a) < s32(b)), 3: int(a < b), 4: a ^ b,
                   5: (s32(a) >> sh) if f7 == 0x20 else (a >> sh),
                   6: a | b, 7: a & b}[f3] & M32
        else:
            raise SystemExit(f"unsupported instruction {w:08x} at {pc:#x}")
        if res is not None and op not in (0x63, 0x23) and rd:
            x[rd] = res & M32
        self.count[cls] += 1
        self.per_pc[pc] = self.per_pc.get(pc, 0) + 1
        self.ic += 1
        self.pc = npc

def run(path):
    code, syms = load_objdump(path)
    sim = Sim(code, syms["main"])
    while sim.pc in code:                   # main returns to ra = 0 -> stop
        sim.step()
        if sim.ic > 5_000_000:
            raise SystemExit("did not terminate")
    return sim, syms

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("objdump")
    ap.add_argument("--trace", help="write the data address trace to this CSV")
    args = ap.parse_args()
    sim, syms = run(args.objdump)
    c = sim.count
    print(f"Ic = {sim.ic}")
    print("classes: ALU {alu}, multiply {mul}, load {load}, store {store}, "
          "branch/jump {branch}".format(**c))
    print(f"data references = {len(sim.trace)} "
          f"(R {sum(t[1]=='R' for t in sim.trace)}, W {sum(t[1]=='W' for t in sim.trace)})")
    if "bucket" in syms:
        print("bucket =", [sim.rd32(syms["bucket"] + 4 * i) for i in range(5)],
              "mean =", sim.rd32(syms["mean"]),
              "below_count =", sim.rd32(syms["below_count"]),
              "pass_count =", sim.rd32(syms["pass_count"]))
    if args.trace:
        is_o0 = syms.get("mark_below") == 0x1035C
        with open(args.trace, "w", newline="\n") as f:
            f.write("sira,RW,adres_hex,boyut,c_satiri,stack_mi\n")
            for i, (pc, rw, addr, size) in enumerate(sim.trace, 1):
                line = c_line(pc, LINES_O0) if is_o0 else 0
                f.write(f"{i},{rw},0x{addr:08X},{size},{line},{int(addr >= 0x70000000)}\n")
        print("trace written to", args.trace)

if __name__ == "__main__":
    main()
