# CMPE3209 Computer Organization — Term Project: C to Silicon

| | |
|---|---|
| Student | Caner Sivri |
| Student number | 5001230018 (`SID` in the program: 1230018 — last 9 digits, since 5001230018 > 2³¹ − 1) |
| Task | G2 — Exam Grade Distribution |
| ISA | RISC-V RV32IM |
| Compiler | riscv64-unknown-elf-gcc <version> |
| Simulator | Ripes v2.3.1 (single-cycle processor, RV32IM) |

## How to build and run

1. In Ripes, choose the single-cycle RV32IM processor.
2. Set the compiler to `riscv64-unknown-elf-gcc` with these arguments:
   `-march=rv32im -mabi=ilp32 -O0 -nostdlib -Wl,--no-relax`
   (`-Wl,--no-relax` stops the linker from accessing globals through `gp`,
   which Ripes initialises to its own value.)
3. Open `main.c` in the Ripes editor (input type: C) and run.
4. Read the results in the Memory tab at the addresses below.
