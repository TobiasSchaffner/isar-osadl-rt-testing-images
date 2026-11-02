#!/usr/bin/env python3
"""Memory-contention experiments on the VisionFive 2 (JH7110). Run as root.

  visionfive2-memlat-tools -l               list the tests
  visionfive2-memlat-tools [-o outdir]      run all tests
  visionfive2-memlat-tools [-o outdir] T... run only the tests T...

Every tool is called as ./<tool>, so each run works in a fresh directory with
links to the tools of this package, to cyclictest and to IsolBench's latency
benchmark. In a source checkout, the C tools are built there first. Results go
to outdir/<test>/ (default /tmp/memlat-results).

Each test keeps the command lines, files and output of the shell script it
replaced. Where a test used `set -e` (fig6, prefetch-1h and the run inside waymask), a failing step
aborts it, and the whole run unless it is nested; elsewhere failures are
ignored as before.
"""
import csv
import glob
import math
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from pathlib import Path
from statistics import median

# System paths
PROC = "/proc"
TRACING = ("/sys/kernel/tracing", "/sys/kernel/debug/tracing")
DEV_EVL = "/dev/evl"

HELP = """\
# Memory-contention experiments on the VisionFive 2 (JH7110). Run as root.
#
#   visionfive2-memlat-tools -l               list the tests
#   visionfive2-memlat-tools [-o outdir]      run all tests
#   visionfive2-memlat-tools [-o outdir] T... run only the tests T...
#
# The test scripts call every tool as ./<tool>, so each run works in a fresh
# directory with links to the tools of this package, to cyclictest and to
# IsolBench's latency benchmark. In a source checkout, the C tools are built
"""

CT = "-m -a 2 -t 1 -p 99 -i 200".split()   # cyclictest: one thread on isolated CPU 2
# L2 events (see data/memlat/l2pmu-sweep.txt): inner 1/12, 1/14, write-back
# 2/16; outer (memory side) 3/8, 3/14, 3/17
SELS = ["1001", "4001", "10002", "103", "4003", "20003"]
WAY_ALL = "ffff"
PF_DEFAULT = ("08014a0d", "0000c45e")      # basicCtrl, additionalCtrl after reset
HUGEPAGES = "1100"
PERIOD_US = 200
DEVNULL, STDOUT, PIPE = subprocess.DEVNULL, subprocess.STDOUT, subprocess.PIPE


class Abort(Exception):
    """A step failed in a test that ran under `set -e`; carries the exit status."""

    def __init__(self, status):
        super().__init__(status)
        self.status = status


# --- running programs, with the shell's redirects -------------------------

def sh(args, out=None, err=None, bg=False, check=False):
    """Run `args >out 2>err` (out/err: a path, DEVNULL or, for err, STDOUT;
    None keeps the console). bg returns the process, else the exit status."""
    files = [open(f, "w") if isinstance(f, str) else f for f in (out, err)]
    try:
        p = subprocess.Popen(args, stdout=files[0], stderr=files[1])
    except FileNotFoundError:
        print(f"{args[0]}: not found", file=sys.stderr, flush=True)
        if check:
            raise Abort(127)
        return 127
    finally:
        for f in files:
            if hasattr(f, "close"):
                f.close()
    if bg:
        return p
    return status(p, check)


def status(p, check):
    rc = p.wait()
    rc = 128 - rc if rc < 0 else rc
    if check and rc:
        raise Abort(rc)
    return rc


def wait(*procs):
    for p in procs:
        if p is not None:
            p.wait()


def lines(path):
    """The lines of a file as grep sees them (split at newlines only)."""
    text = Path(path).read_text(errors="surrogateescape")
    return text.split("\n")[:-1] if text.endswith("\n") else text.split("\n") if text else []


def grep(pattern, src, dst):
    """grep -E pattern src > dst"""
    with open(dst, "w", errors="surrogateescape") as f:
        try:
            f.writelines(l + "\n" for l in lines(src) if re.search(pattern, l))
        except OSError as e:
            print(f"grep: {src}: {e.strerror}", file=sys.stderr, flush=True)
            return 2
    return 0


def cat(src, dst):
    """cat src > dst; 1 if src could not be read, as cat."""
    with open(dst, "wb") as f:
        try:
            f.write(Path(src).read_bytes())
        except OSError as e:
            print(f"cat: {src}: {e.strerror}", file=sys.stderr, flush=True)
            return 1
    return 0


def put(path, text, mode="w"):
    """echo text > path"""
    with open(path, mode) as f:
        f.write(text)


def mkdir(path):
    os.makedirs(path, exist_ok=True)


def touch(path):
    Path(path).touch()


def stamp():
    """date +%s.%N"""
    ns = time.time_ns()
    return f"{ns // 10**9}.{ns % 10**9:09d}"


def cyclictest(secs, out):
    """Histogram of wake-up latency on isolated CPU 2."""
    sh(["./cyclictest", *CT, "-q", "-h", "1000", "-D", f"{secs}s"], out, STDOUT)


def vm(method, timeout, out, *extra, nbytes="1G", brief=True):
    """stress-ng --vm load on the two load CPUs, in the background."""
    return sh(["stress-ng", "--vm", "2", "--vm-bytes", nbytes, "--vm-method", method, *extra,
               "--timeout", timeout] + ["--metrics-brief"] * brief, out, STDOUT, bg=True)


def mode():
    return "evl" if os.path.exists(DEV_EVL) else "rt"


# --- L2 way masks and prefetchers -----------------------------------------

def hart_of(cpu):
    """Hart of Linux CPU cpu; the boot hart becomes CPU 0 and differs between boots."""
    p = None
    for l in lines(f"{PROC}/cpuinfo"):
        f = l.split()
        if f[:1] == ["processor"]:
            p = f[2] if len(f) > 2 else ""
        if len(f) > 2 and f[0] == "hart" and f[1] == ":" and p == str(cpu):
            return f[2]
    return None


def harts(*cpus):
    return [h for h in map(hart_of, cpus) if h is not None]


def set_mask(mask, *cpus):
    """waymask arguments limiting the data-side masters of cpus, 5*hart+8 and
    5*hart+9 (found by masking each of the 32 ids to one way, see waymask.c)."""
    return [a for c in cpus for i in (5 * int(hart_of(c)) + 8, 5 * int(hart_of(c)) + 9)
            for a in (str(i), mask)]


def restore():
    sh(["./waymask"] + [a for i in range(32) for a in (str(i), WAY_ALL)], DEVNULL)


def partition():
    """Ways 0-7 for CPUs 0-1 (load), 8-11 for CPU 2, 12-15 for CPU 3; prints the masks."""
    sh(["./waymask", *set_mask("00ff", 0, 1), *set_mask("0f00", 2), *set_mask("f000", 3)])


# --- tests -----------------------------------------------------------------

def probe_loop(end, path):
    """IsolBench's latency benchmark back to back until end; one
    "<unix time> <ns/access>" per 64 MB walk."""
    with open(path, "w") as f:
        while time.time_ns() // 10**9 < end:
            try:
                p = subprocess.run(["./latency", "-m", "65536", "-c", "3", "-i", "1"],
                                   stdout=PIPE, stderr=DEVNULL, text=True)
                ns = "\n".join(re.findall(r"^average ([0-9.]*) ns", p.stdout, re.M))
            except FileNotFoundError:
                ns = ""
            f.write(f"{stamp()} {ns}\n")
            f.flush()


def run_memlat(mode, secs, out, stress="--vm 2 --vm-bytes 1G"):
    """Correlate wake-up latency on isolated CPU 2 with DRAM access latency on
    isolated CPU 3 under memory load (cf. Section VII). out should be on tmpfs:
    SD writes would block the probe. Aborts on the first failing step."""
    tmp = os.environ.get("STRESS_TMP") or "/root/stress-tmp"   # SD card: --hdd loads the MMC
    mkdir(out)
    mkdir(tmp)
    sh(["uname", "-a"], f"{out}/uname", check=True)
    put(f"{out}/stressor", stress + "\n")
    if cat(f"{PROC}/cmdline", f"{out}/cmdline"):
        raise Abort(1)
    end = time.time_ns() // 10**9 + secs
    probe = threading.Thread(target=probe_loop, args=(end, f"{out}/memlat.txt"), daemon=True)
    probe.start()
    load = sh(["stress-ng", *stress.split(), "--temp-path", tmp, "--timeout", f"{secs + 5}s",
               "--metrics-brief"], f"{out}/stress.txt", STDOUT, bg=True)
    put(f"{out}/start", stamp() + "\n")
    if mode == "evl":
        sh(["latmus", "-m", "--user", "-p", "200", "-P", "99", "-c", "2", "-T", str(secs)],
           f"{out}/lat.txt", STDOUT, check=True)
    elif mode == "rt":
        sh(["cyclictest", *CT, "-v", "-D", f"{secs}s"], f"{out}/lat.txt", STDOUT, check=True)
    wait(load)
    probe.join()
    shutil.rmtree(tmp, ignore_errors=True)


def sweep_methods(secs, out, extra=""):
    """Each stress-ng vm method alone: DRAM probe (CPU 3), cyclictest (CPU 2), IPIs."""
    p = subprocess.run(["stress-ng", "--vm-method", "x"], stdout=PIPE, stderr=STDOUT, text=True)
    methods = [m for l in p.stdout.split("\n") for m in re.sub(r".*choices are: ", "", l, count=1).split()]
    mkdir(out)
    for m in methods:
        if m == "all":
            continue
        d = f"{out}/{m}"
        mkdir(d)
        grep("IPI", f"{PROC}/interrupts", f"{d}/irq-before")
        probe = sh(["./memlat-probe", "3", str(secs)], f"{d}/memlat.txt", bg=True)
        load = vm(m, f"{secs + 2}s", f"{d}/stress.txt", *extra.split())
        cyclictest(secs, f"{d}/lat.txt")
        wait(probe, load)
        grep("IPI", f"{PROC}/interrupts", f"{d}/irq-after")
    touch(f"{out}/done")


def locality(out, part):
    """L2 controller or DDR controller? aggr on CPUs 0 and 1 with way
    partitioning; per configuration L2 events, the latency of a resident
    256 KB and of a 64 MB working set on CPU 3, and cyclictest on CPU 2.
     1: l2res-*: aggressor buffer fits into its L2 ways: L2 traffic, no DRAM;
        ddr-w-B-R: 64 MB buffer, blocks of B bytes, R Mlines/s per core (0 =
        unthrottled). Same rate, larger B: same L2 misses and write-backs but
        better DRAM row locality.
     2: what makes stress-ng prime-1 (stride 61 bytes, a nearly sequential
        read-modify-write sweep) worse than aggr at the same DRAM traffic:
        buffer size, re-mapping the buffer every round (no --vm-keep).
     3: buffer size of the sequential aggressor.
     4: a 64 MB sequential aggressor confined to one physical 512 MB chunk.
     5: TLB misses vs. DRAM footprint: 1 GB on 2 MB huge pages, and 1 GB of
        virtual address space aliasing 64 MB of memory.
     6: length of physically contiguous runs on huge pages: scattered blocks
        of 64 B to 2 MB, unthrottled and at a fixed rate.
     7: reads versus writes in long contiguous runs (huge pages), write rate.
     8: long and short runs with the aggressors' L2 prefetchers disabled.
     9: stress-ng prime-1 with the load cores' prefetchers at default,
        disabled, and with lower MSHR thresholds (additionalCtrl.qFullnessThrd,
        default 14/16)."""
    nr = f"{PROC}/sys/vm/nr_hugepages"

    def run(name, load):
        d = f"{out}/{name}"
        mkdir(d)
        jobs = load(d)
        time.sleep(2)
        grep(r"^ *(IPI|[0-9]+):", f"{PROC}/interrupts", f"{d}/irq-before.txt")
        grep(r"^(pgfault|pgfree|nr_tlb)", f"{PROC}/vmstat", f"{d}/vmstat-before.txt")
        sh(["./l2pmu", "5", *SELS], f"{d}/l2pmu.txt")
        sh(["./memlat-dist", "3", "0.25", "10"], f"{d}/dist-256k.txt")
        sh(["./memlat-dist", "3", "64", "10"], f"{d}/dist-64mb.txt")
        cyclictest(45, f"{d}/lat.txt")
        grep(r"^ *(IPI|[0-9]+):", f"{PROC}/interrupts", f"{d}/irq-after.txt")
        grep(r"^(pgfault|pgfree|nr_tlb)", f"{PROC}/vmstat", f"{d}/vmstat-after.txt")
        wait(*jobs)

    def pair(buf_kb, block, rate, mode, *mem):
        return lambda d: [sh(["./aggr", str(c), str(buf_kb), str(block), str(rate), "75", mode, *mem],
                             f"{d}/aggr-{c}.txt", bg=True) for c in (0, 1)]

    def stress(method, nbytes, *extra):
        return lambda d: [vm(method, "75s", f"{d}/stress.txt", *extra, nbytes=nbytes)]

    def hugepages():
        put(nr, HUGEPAGES + "\n")
        cat(nr, f"{out}/nr_hugepages")

    mkdir(out)
    pf_harts = None
    try:
        grep("^(processor|hart)", f"{PROC}/cpuinfo", f"{out}/cpuinfo")
        partition()
        sh(["./waymask"], f"{out}/waymask.txt")
        if part == 2:
            run("stress-prime1", stress("prime-1", "1G"))
            run("stress-prime1-keep", stress("prime-1", "1G", "--vm-keep"))
            run("stress-prime1-64m", stress("prime-1", "64M"))
            run("stress-prime1-64m-keep", stress("prime-1", "64M", "--vm-keep"))
            run("stress-write64", stress("write64", "1G"))
            run("ddr-w-1g-65536-0", pair(1048576, 65536, 0, "w"))
        elif part == 3:
            for kb in (65536, 131072, 262144, 524288, 1048576):
                run(f"ddr-w-size-{kb}", pair(kb, 65536, 0, "w"))
        elif part == 4:
            for r in (2, 3, 8, 9):
                run(f"ddr-w-region-{r}", pair(1048576, 4096, 0, "w", f"region:{r}:65536"))
            run("ddr-w-region-2-repeat", pair(1048576, 4096, 0, "w", "region:2:65536"))
        elif part == 5:
            hugepages()
            run("ddr-w-1g-4k", pair(1048576, 65536, 0, "w"))
            run("ddr-w-1g-huge", pair(1048576, 65536, 0, "w", "huge"))
            run("ddr-w-1g-alias64m", pair(1048576, 65536, 0, "w", "alias:65536"))
            run("ddr-w-64m-4k", pair(65536, 65536, 0, "w"))
            run("ddr-w-64m-huge", pair(65536, 65536, 0, "w", "huge"))
            put(nr, "0\n")
        elif part == 6:
            run("ddr-w-64m-4k-65536-0", pair(65536, 65536, 0, "w"))
            hugepages()
            for b in (64, 4096, 65536, 2097152):
                run(f"ddr-w-huge-{b}-0", pair(1048576, b, 0, "w", "huge"))
            for b in (64, 4096, 65536):
                run(f"ddr-w-huge-{b}-3.5", pair(1048576, b, 3.5, "w", "huge"))
            put(nr, "0\n")
        elif part == 7:
            hugepages()
            run("ddr-r-huge-65536-0", pair(1048576, 65536, 0, "r", "huge"))
            run("ddr-s-huge-65536-0", pair(1048576, 65536, 0, "s", "huge"))
            for r in (1, 2, 4, 6):
                run(f"ddr-w-huge-65536-{r}", pair(1048576, 65536, r, "w", "huge"))
            put(nr, "0\n")
        elif part in (8, 9):
            if part == 8:       # stress-ng (part 9) needs the memory as 4 KB pages
                put(nr, HUGEPAGES + "\n")
            cat(nr, f"{out}/nr_hugepages")
            sh(["./pfctl"], f"{out}/pf-default.txt")
            pf_harts = harts(0, 1)

            def pf(d, basic, additional):
                for h in pf_harts:
                    sh(["./pfctl", h, basic, additional], DEVNULL)
                sh(["./pfctl"], f"{d}/pf.txt")

            if part == 9:
                for cfg in ("08014a0d:0000c45e", "08014a0c:0000c45e", "08014a0d:0000c458",
                            "08014a0d:0000c454", "08014a0d:0000c452"):
                    d = f"{out}/stress-prime1-pf-{cfg}"
                    mkdir(d)
                    pf(d, *cfg.split(":"))
                    run(f"stress-prime1-pf-{cfg}", stress("prime-1", "1G"))
            else:
                for b in (2097152, 65536, 4096):
                    for name, basic in (("pfoff", "08014a0c"), ("pfon", "08014a0d")):
                        d = f"{out}/ddr-w-huge-{b}-0-{name}"
                        mkdir(d)
                        pf(d, basic, PF_DEFAULT[1])
                        run(f"ddr-w-huge-{b}-0-{name}", pair(1048576, b, 0, "w", "huge"))
                put(nr, "0\n")
        else:
            run("idle", lambda d: [sh(["sleep", "75"], bg=True)])
            run("stress-prime1", stress("prime-1", "1G"))
            run("l2res-w", pair(256, 64, 0, "w"))
            run("l2res-r", pair(256, 64, 0, "r"))
            for m in ("w", "r"):
                run(f"ddr-{m}-64-0", pair(65536, 64, 0, m))
            for b in (64, 256, 1024, 4096, 65536):
                run(f"ddr-w-{b}-3.5", pair(65536, b, 3.5, "w"))
            run("ddr-r-4096-3.5", pair(65536, 4096, 3.5, "r"))
            run("ddr-r-64-3.5", pair(65536, 64, 3.5, "r"))
            run("ddr-w-65536-0", pair(65536, 65536, 0, "w"))
        touch(f"{out}/done")
    finally:
        restore()
        for h in pf_harts or ():
            sh(["./pfctl", h, *PF_DEFAULT], DEVNULL)


def prefetch_evl(out, secs):
    """Prefetcher throttling under EVL with the load-matrix measurement (C2):
    memrate and vm with the L2 prefetchers of the housekeeping harts limited
    to 2/16 of the L2 MSHRs, measured exactly as in the load matrix
    (cyclictest command line, latmus behind the wrapper, CPUs 0-3). Before
    that, 5 min of each load at the default (14/16) and at 2/16 for the load
    throughput, without measurement. Aborts on the first failing step and
    restores the default on exit."""
    loads = {"memrate": ["--memrate", "2"], "vm": ["--vm", "2", "--vm-bytes", "1G"]}
    mkdir(out)
    sh(["uname", "-a"], f"{out}/uname", check=True)
    if cat(f"{PROC}/cmdline", f"{out}/cmdline"):
        raise Abort(1)
    hs = harts(0, 1)

    def pf(additional, dst):
        for h in hs:
            sh(["./pfctl", h, PF_DEFAULT[0], additional], DEVNULL, check=True)
        sh(["./pfctl"], dst, check=True)

    try:
        for load in loads:
            for t in ("c45e", "c452"):      # throughput reference: default and 2/16
                d = f"{out}/tput-{load}-{t}"
                mkdir(d)
                pf(f"0000{t}", f"{d}/pf.txt")
                sh(["stress-ng", *loads[load], "--timeout", "300s", "--metrics-brief"],
                   f"{d}/stress.txt", STDOUT, check=True)
        for load in loads:                  # measured runs at 2/16
            d = f"{out}/lat-{load}-c452"
            mkdir(d)
            pf("0000c452", f"{d}/pf.txt")
            put(f"{d}/start", f"{time.time_ns() // 10**9}\n")
            job = sh(["stress-ng", *loads[load], "--timeout", f"{secs + 5}s", "--metrics-brief"],
                     f"{d}/stress.txt", STDOUT, bg=True)
            sh(["cyclictest", "-m", "-p", "98", "-i", "200", "-h", "1000", "-q", "-a", "0-3", "-t", "4",
                "-D", f"{secs}s"], f"{d}/hist.txt", STDOUT, check=True)
            wait(job)
        put(f"{out}/done", "done\n")
    finally:
        pf(PF_DEFAULT[1], f"{out}/pf-restored.txt")


def waymask_test(out):
    """Does L2 way partitioning protect the isolated cores from prime-1
    traffic? memlat-dist (CPU 3) and cyclictest (CPU 2) with default and with
    partitioned way masks, then the 600 s --vm run of fig6, partitioned."""
    def run(name):
        d = f"{out}/{name}"
        mkdir(d)
        sh(["./waymask"], f"{d}/waymask.txt")
        load = vm("prime-1", "110s", f"{d}/stress.txt")
        time.sleep(5)
        sh(["./memlat-dist", "3", "1", "20"], f"{d}/dist-1mb.txt")
        sh(["./memlat-dist", "3", "64", "20"], f"{d}/dist-64mb.txt")
        cyclictest(45, f"{d}/lat.txt")
        wait(load)

    mkdir(out)
    try:
        grep("^(processor|hart)", f"{PROC}/cpuinfo", f"{out}/cpuinfo")
        restore()
        sh(["./waymask"], f"{out}/waymask-default.txt")
        # master-id check: CPU 3 limited to one way (128 KB) must slow a 1 MB
        # working set to DRAM latency; if not, the id mapping is wrong
        sh(["./memlat-dist", "3", "1", "10"], f"{out}/id-default-1mb.txt")
        sh(["./waymask", *set_mask("0001", 3)], DEVNULL)
        sh(["./memlat-dist", "3", "1", "10"], f"{out}/id-oneway-1mb.txt")
        restore()
        restore()   # twice, as waymask-test.sh did
        run("prime1-default")
        partition()
        run("prime1-partitioned")
        # the figure's load (--vm-method all), partitioned
        partition()
        try:
            run_memlat("rt", 600, f"{out}/vm-partitioned", "--vm 2 --vm-bytes 1G")
        except Abort:
            pass
        touch(f"{out}/done")
    finally:
        restore()


def memreg_sweep(secs, out, method, event, poll, *budgets):
    """Dose-response of wake-up latency (CPU 2) to regulating the load cores:
    memreg on CPUs 0 and 1 with each budget per 1 ms period ("none": no
    regulator, "inf": regulator polls but never throttles). event: l2=SEL (L2
    counter budget) or time (budget = run time in us)."""
    mkdir(out)
    for b in budgets:
        d = f"{out}/{method}-{b}"
        mkdir(d)
        jobs = [vm(method, f"{secs + 4}s", f"{d}/stress.txt")]
        if b != "none":
            jobs += [sh(["./memreg", str(c), "1000000000" if b == "inf" else b, "1000", poll,
                         str(secs + 2), event], f"{d}/memreg-{c}.txt", bg=True) for c in (0, 1)]
        time.sleep(2)
        cyclictest(secs, f"{d}/lat.txt")
        wait(*jobs)
    touch(f"{out}/done")


def l2pmu_sweep(path):
    """Identify L2 PMU events: count each mask bit 8..39 of event sets 1..3 for
    1 s, idle and under stress-ng prime-1 (scattered writes) and read64."""
    def sweep(label):
        for s in (1, 2, 3):
            for b in range(8, 40, 4):
                sels = [f"{1 << (b + k - 8):x}{s:02x}" for k in range(4)]
                p = subprocess.run(["./l2pmu", "1", *sels], stdout=PIPE, text=True)
                f.writelines(f"{label} {l}" for l in re.findall(r"[^\n]*\n|[^\n]+$", p.stdout))
                f.flush()

    with open(path, "w") as f:
        sweep("idle")
        for m in ("prime-1", "read64"):
            load = vm(m, "35s", DEVNULL, brief=False)
            time.sleep(3)
            sweep(m)
            wait(load)


EVENTS = ("timer:hrtimer_start timer:hrtimer_expire_entry timer:hrtimer_expire_exit "
          "irq:irq_handler_entry irq:irq_handler_exit irq:softirq_entry irq:softirq_exit "
          "sched:sched_waking sched:sched_wakeup sched:sched_switch "
          "raw_syscalls:sys_enter raw_syscalls:sys_exit ipi:ipi_send_cpu ipi:ipi_send_cpumask").split()


def trace_spike(thresh_us, out, stress, secs):
    """ftrace events on CPU 2 until cyclictest sees a wake-up above thresh_us
    under the given stressor; leaves the trace in out/trace.txt."""
    t = TRACING[0]
    mkdir(out)
    put(f"{t}/tracing_on", "0\n")
    put(f"{t}/trace", "\n")
    put(f"{t}/current_tracer", "nop\n")
    put(f"{t}/trace_clock", "mono\n")         # same clock as hrtimer expiry values
    put(f"{t}/tracing_cpumask", "f\n")        # all CPUs: IPI senders live on 0-1
    put(f"{t}/buffer_size_kb", "16384\n")
    put(f"{t}/set_event", "\n")
    for e in EVENTS:
        put(f"{t}/set_event", e + "\n", "a")
    probe = sh(["./memlat-probe", "3", str(secs)], f"{out}/memlat.txt", bg=True)
    load = None if stress == "none" else sh(["stress-ng", *stress.split(), "--timeout", f"{secs}s"],
                                             f"{out}/stress.txt", STDOUT, bg=True)
    time.sleep(2)
    put(f"{t}/tracing_on", "1\n")
    sh(["./cyclictest", *CT, "-b", str(thresh_us), "--tracemark", "-D", f"{secs}s"],
       f"{out}/lat.txt", STDOUT)
    put(f"{t}/tracing_on", "0\n")
    sh(["pkill", "stress-ng"])
    sh(["pkill", "memlat-probe"])
    wait(probe, load)
    cat(f"{t}/trace", f"{out}/trace.txt")
    put(f"{t}/set_event", "\n")
    put(f"{t}/trace", "\n")


# --- summaries ---------------------------------------------------------------

def hist(text):
    """cyclictest -h: (bins {us: count}, max_us, overflows)."""
    bins, mx, ovf = {}, None, 0
    for l in text.splitlines():
        f = l.split()
        if l.startswith("# Max Latencies:"):
            mx = int(f[-1])
        elif l.startswith("# Histogram Overflows:"):
            ovf = int(f[-1])
        elif len(f) == 2 and f[0].isdigit():
            bins[int(f[0])] = int(f[1])
    return bins, mx, ovf


def pct(bins, ovf, q):
    total = sum(bins.values()) + ovf
    acc = 0
    for us in sorted(bins):
        acc += bins[us]
        if acc >= q * total:
            return us
    return float("inf")


def lat_per_second(text):
    """latmus prints one RTD line per second; cyclictest -v prints every sample
    (thread: index: latency), binned here into seconds by its 200 us period."""
    if "RTD|" in text:
        return [float(l.split("|")[3]) for l in text.splitlines() if l.startswith("RTD|")]
    per = 1_000_000 // PERIOD_US
    out = []
    for l in text.splitlines():
        f = l.replace(":", " ").split()
        if len(f) != 3 or not all(x.isdigit() for x in f):
            continue
        s = int(f[1]) // per
        out.extend([0.0] * (s + 1 - len(out)))
        out[s] = max(out[s], float(f[2]))
    return out


def mem_per_second(text, start):
    out = {}
    for l in text.split("\n"):
        if l.strip():
            t, ns = map(float, l.split())
            out[math.floor(t - start)] = ns
    return out


def memlat_rows(d):
    """(time_s, lat_max_us, memlat_ns) of a run_memlat directory. memlat.txt has
    wall-clock stamps, binned against the run's start stamp; alignment is to
    about 1 s (latmus warm-up), the probe's own resolution."""
    d = Path(d)
    start = float(d.joinpath("start").read_text())
    lat = lat_per_second(d.joinpath("lat.txt").read_text())
    mem = mem_per_second(d.joinpath("memlat.txt").read_text(), start)
    return [(s, v, mem[s]) for s, v in enumerate(lat) if s in mem]


def memlat_csv(d, f):
    f.write("time_s,lat_max_us,memlat_ns\n")
    for s, v, m in memlat_rows(d):
        f.write(f"{s},{v},{m}\n")


def ipi(text):
    """{name: (cpu2, cpu3)} from /proc/interrupts IPI rows."""
    out = {}
    for l in text.splitlines():
        f = l.split()
        out[f[0].rstrip(":")] = (int(f[3]), int(f[4]))
    return out


def bogo_rate(text):
    for l in text.splitlines():
        f = l.split()
        if "metrc:" in f and "vm" in f:
            return float(f[f.index("vm") + 5])   # bogo ops/s (real time)
    return 0.0


def sweep_summary(root, f):
    """One row per stress-ng vm method."""
    w = csv.writer(f)
    w.writerow(["method", "mem_med_ns", "mem_max_ns", "lat_p99_us", "lat_p999_us", "lat_max_us",
                "n_over_100us", "ipi_cpu2", "ipi_cpu3", "bogo_ops_s"])
    for d in sorted(p for p in Path(root).iterdir() if p.is_dir()):
        mem = [float(l.split()[1]) for l in (d / "memlat.txt").read_text().splitlines() if l.strip()]
        bins, mx, ovf = hist((d / "lat.txt").read_text())
        b, a = ipi((d / "irq-before").read_text()), ipi((d / "irq-after").read_text())
        di = [sum(a[k][c] - b[k][c] for k in a) for c in (0, 1)]
        w.writerow([d.name, round(median(mem)), round(max(mem)), pct(bins, ovf, 0.99),
                    pct(bins, ovf, 0.999), mx,
                    sum(v for us, v in bins.items() if us > 100) + ovf, di[0], di[1],
                    bogo_rate((d / "stress.txt").read_text())])


def locality_summary(root, f):
    """One table row per locality configuration."""
    f.write("config            " + " ".join(f"{s:>7}" for s in SELS)
            + "  Ml/s  256k-p50 p99  64m-p50 p99  ct-max >100\n")
    for d in sorted(p for p in Path(root).iterdir() if (p / "lat.txt").exists()):
        pmu = dict(re.findall(r"sel 0x(\w+): (\d+)", (d / "l2pmu.txt").read_text()))
        ev = " ".join(f"{int(pmu.get(s, 0)) / 5e6:7.2f}" for s in SELS)   # M/s
        rate = sum(float((a.read_text().split() or [0])[0]) for a in d.glob("aggr-*.txt"))
        dist = [re.search(r"p50 (\d+) p99 (\d+)", (d / n).read_text()).groups()
                for n in ("dist-256k.txt", "dist-64mb.txt")]
        bins, mx, _ = hist((d / "lat.txt").read_text())
        if mx is None:
            mx = max((us for us, n in bins.items() if n), default=0)
        over = sum(n for us, n in bins.items() if us > 100)
        f.write(f"{d.name:17} {ev} {rate:5.1f}  {dist[0][0]:>7} {dist[0][1]:>4}"
                f"  {dist[1][0]:>7} {dist[1][1]:>4}  {mx:>6} {over:>4}\n")


EV = re.compile(r"^\s*(\S.*?)-(\d+)\s+\[(\d+)\]\s+\S+\s+([\d.]+):\s+(\w+):\s*(.*)$")


def parse(lines):
    for l in lines:
        m = EV.match(l)
        if m:
            comm, pid, cpu, ts, ev, args = m.groups()
            yield int(pid), int(cpu), round(float(ts) * 1e6, 3), ev, args


def cycles(events, pid):
    """Split every cyclictest wake-up on CPU 2 into stages. Per cycle (timer
    armed with expiry E by the measuring thread):
      irq    = timer irq_handler_entry - E          (interrupt delivery/entry)
      wake   = sched_wakeup - irq_handler_entry     (handler up to wake-up)
      switch = sched_switch to the thread - wakeup
      ret    = sys_exit of the thread - switch      (back to user space)
      total  = sys_exit - E
    'other' lists foreign activity on CPU 2 inside [E, sys_exit]: other
    hrtimer callbacks, softirqs, non-timer irqs, other tasks switched in."""
    cur = None
    for p, cpu, t, ev, a in events:
        if cpu != 2:
            continue
        if ev == "hrtimer_start" and p == pid and "hrtimer_wakeup" in a:
            cur = {"E": int(re.search(r"expires=(\d+)", a).group(1)) / 1000, "other": set()}
            continue
        if cur is None:
            continue
        if ev == "irq_handler_entry" and "riscv-timer" in a and "irq" not in cur:
            cur["irq_at"] = t
        elif ev == "hrtimer_expire_entry" and "now" not in cur and "hrtimer_wakeup" in a \
                and int(re.search(r"now=(\d+)", a).group(1)) / 1000 >= cur["E"] and "irq_at" in cur:
            cur["now"] = int(re.search(r"now=(\d+)", a).group(1)) / 1000
            cur["irq"] = cur["irq_at"]
        elif ev == "hrtimer_expire_entry":
            cur["other"].add(re.search(r"function=(\w+)", a).group(1))
        elif ev == "irq_handler_entry" and "riscv-timer" not in a:
            cur["other"].add(a.split("name=")[1].replace(" ", "_"))
        elif ev == "softirq_entry":
            cur["other"].add("softirq_" + a.split("action=")[1].rstrip("]"))
        elif ev == "sched_wakeup" and f"pid={pid} " in a and "irq" in cur:
            cur.setdefault("wake", t)
        elif ev == "sched_switch":
            nxt = int(re.search(r"next_pid=(\d+)", a).group(1))
            if nxt == pid and "wake" in cur:
                cur.setdefault("switch", t)
            elif nxt not in (0, pid):
                cur["other"].add("task_" + re.search(r"next_comm=(\S+)", a).group(1))
        elif ev == "sys_exit" and p == pid and "switch" in cur:
            c = cur
            cur = None
            yield {"E": c["E"], "irq": c["irq"] - c["E"], "wake": c["wake"] - c["irq"],
                   "switch": c["switch"] - c["wake"], "ret": t - c["switch"],
                   "total": t - c["E"], "other": "+".join(sorted(c["other"]))}


def cycles_csv(d, f):
    try:
        ids = [w for l in lines(f"{d}/lat.txt") if l.startswith("# Thread Ids:")
               for w in l[len("# Thread Ids:"):].split()]
    except OSError as e:
        print(f"sed: can't read {d}/lat.txt: {e.strerror}", file=sys.stderr, flush=True)
        ids = []
    f.write("E_us,irq,wake,switch,ret,total,other\n")
    with open(f"{d}/trace.txt") as t:
        for c in cycles(parse(t), int(ids[0])):
            f.write(f"{c['E']:.3f},{c['irq']:.1f},{c['wake']:.1f},{c['switch']:.1f},"
                    f"{c['ret']:.1f},{c['total']:.1f},{c['other']}\n")


# --- the tests and the command line -----------------------------------------

def part(p):
    return lambda o: locality(o, p)


LOCALITY = ("summary.txt", locality_summary)
# name, image in the paper, description, run(outdir), (summary file, summary(outdir, file))
TESTS = [
    ("fig6", "EVL or PREEMPT_RT", "Fig. 6: wake-up latency vs. IsolBench memory latency, 600 s under --vm",
     lambda o: run_memlat(mode(), 600, o), ("memlat.csv", memlat_csv)),
    ("vm-methods", "PREEMPT_RT", "the 35 methods of stress-ng --vm, 45 s each",
     lambda o: sweep_methods(45, o), ("summary.csv", sweep_summary)),
    ("aggressor-1", "PREEMPT_RT", "controlled aggressor: L2-resident and DRAM traffic, block sizes", part(1), LOCALITY),
    ("aggressor-2", "PREEMPT_RT", "prime-1 variants: buffer size, --vm-keep", part(2), LOCALITY),
    ("aggressor-3", "PREEMPT_RT", "aggressor buffer size", part(3), LOCALITY),
    ("aggressor-4", "PREEMPT_RT", "aggressor confined to one 512 MB DRAM region (not in the paper)", part(4), LOCALITY),
    ("aggressor-5", "PREEMPT_RT", "TLB misses vs. DRAM footprint (not in the paper)", part(5), LOCALITY),
    ("aggressor-6", "PREEMPT_RT", "scattered blocks of 64 B to 2 MB on huge pages", part(6), LOCALITY),
    ("aggressor-7", "PREEMPT_RT", "reads vs. writes in long runs, write rate", part(7), LOCALITY),
    ("prefetch-off", "PREEMPT_RT", "block sizes with the aggressors' L2 prefetchers disabled", part(8), LOCALITY),
    ("fig7", "EVL or PREEMPT_RT", "Fig. 7: L2 prefetcher threshold sweep under prime-1", part(9), LOCALITY),
    ("prefetch-1h", "EVL", "memrate and vm of the load matrix at 2/16, 1 h each",
     lambda o: prefetch_evl(o, 3600), None),
    ("waymask", "PREEMPT_RT", "L2 way partitioning under prime-1", waymask_test, None),
    ("memreg-250us", "PREEMPT_RT", "polling regulator, 250 us polling, budgets 12000-3000",
     lambda o: memreg_sweep(45, o, "prime-1", "l2=10002", "250", "none", "12000", "5000", "3000"), None),
    ("memreg-50us", "PREEMPT_RT", "polling regulator, 50 us polling, budgets 15000-2500",
     lambda o: memreg_sweep(45, o, "prime-1", "l2=10002", "50", "none", "15000", "10000", "5000",
                            "2500", "inf"), None),
    ("l2pmu", "any", "identify the L2 event counters (write-backs of dirty lines)",
     lambda o: l2pmu_sweep(f"{o}/l2pmu.txt"), None),
    ("ftrace", "kernel with ftrace", "ftrace of a wake-up above 100 us under prime-1",
     lambda o: trace_spike(100, o, "--vm 2 --vm-bytes 1G --vm-method prime-1", 300),
     ("cycles.csv", cycles_csv)),
]


def tracing():
    """ftrace is available if a trace file exists, after mounting tracefs if needed."""
    if not os.path.exists(f"{TRACING[0]}/trace"):
        subprocess.run(["mount", "-t", "tracefs", "nodev", TRACING[0]], stderr=DEVNULL)
    return any(os.path.exists(f"{t}/trace") for t in TRACING)


def prepare(work):
    """Fill the work directory with links to the tools, cyclictest and IsolBench's latency."""
    tooldir = os.path.dirname(os.path.realpath(__file__))
    for f in sorted(os.listdir(tooldir)):
        if not f.startswith("."):
            os.symlink(f"{tooldir}/{f}", f"{work}/{f}")
    os.chdir(work)
    for c in sorted(glob.glob("*.c")):
        if not os.path.exists(c[:-2]):
            sh(["gcc", "-O2", "-Wall", "-o", c[:-2], c], check=True)
    cyc = shutil.which("cyclictest")
    if not cyc:
        print("ln: failed to create symbolic link 'cyclictest' -> '': No such file or directory",
              file=sys.stderr, flush=True)
        raise Abort(1)
    for target, link in ((cyc, "cyclictest"), (shutil.which("isolbench-latency"), "latency")):
        if target:
            if os.path.lexists(link):
                os.remove(link)
            os.symlink(target, link)
    if not shutil.which("isolbench-latency"):
        print("warning: isolbench-latency not found; fig6, waymask and memreg need it",
              file=sys.stderr, flush=True)


def run_test(t, out):
    name, _, _, run, summary = t
    if name == "ftrace" and not tracing():
        print(f"== {name} skipped: the kernel has no ftrace (CONFIG_FTRACE)", file=sys.stderr, flush=True)
        return
    o = f"{out}/{name}"
    mkdir(o)
    print(f"== {name} -> {o}", flush=True)
    run(o)
    if summary:
        try:
            with open(f"{o}/{summary[0]}", "w") as f:
                summary[1](o, f)
        except Exception:
            traceback.print_exc()
            print(f"warning: summary of {name} failed", file=sys.stderr, flush=True)


def main(argv):
    out = "/tmp/memlat-results"
    if argv[:1] == ["-l"]:
        print(f"{'TEST':<13} {'IMAGE IN THE PAPER':<24} DESCRIPTION")
        for n, i, d, _, _ in TESTS:
            print(f"{n:<13} {i:<24} {d}")
        return 0
    if argv[:1] == ["-o"]:
        if len(argv) < 2 or not argv[1]:
            return 1
        out = os.path.realpath(argv[1])
        if not os.path.isdir(os.path.dirname(out)):     # readlink -f fails
            return 1
        argv = argv[2:]
    elif argv[:1] in (["-h"], ["--help"]):
        print(HELP, end="")
        return 0
    byname = {t[0]: t for t in TESTS}
    for want in argv:
        if want not in byname:
            print(f"unknown test: {want} (see -l)", file=sys.stderr)
            return 1
    if os.geteuid() != 0:
        print("run as root", file=sys.stderr)
        return 1
    # SIGTERM restores the L2 setup like Ctrl-C, through the finally clauses
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(128 + signal.SIGTERM))
    work = tempfile.mkdtemp(prefix="memlat-work.")
    try:
        prepare(work)
        for t in [byname[w] for w in argv] or TESTS:
            run_test(t, out)
    except Abort as e:
        return e.status
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
