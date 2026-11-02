/*
 * Polling memory-bandwidth regulator for one CPU (MemGuard budget, MemPol
 * polling; the JH7110 has no counter-overflow interrupt).
 *
 * A SCHED_FIFO thread pinned to CPU counts per-CPU PMU events and, once
 * BUDGET events were spent in the current PERIOD, spins until the period
 * ends. Spinning touches no memory and keeps lower-priority tasks (the load)
 * off the CPU. Overshoot is bounded by one poll interval plus the thread's
 * own wake-up latency. Events are U74 raw events (class | mask << 8):
 * 0x202 D-cache miss/MMIO, 0x402 D-cache writeback; their sum is budgeted.
 * BUDGET 0 only counts and prints events per period every second.
 * OpenSBI on the VisionFive 2 maps no hardware events, so these count
 * nothing there. Event "l2=SEL" instead programs selector SEL into counter 0
 * of the L2 cache controller (0x2010000, selectors at 0x2000, counters at
 * 0x3000) and budgets that counter through /dev/mem. It counts the traffic
 * of all cores, so the instances on all regulated CPUs see the same count
 * and throttle together; periods are aligned to the clock for that reason.
 * Event "time" budgets run time in microseconds (a duty-cycle throttle).
 *
 * usage: memreg cpu budget period_us poll_us seconds [event_hex... | l2=SEL | time]
 */
#include "jh7110.h"
#include <linux/perf_event.h>
#include <sys/resource.h>
#include <sys/syscall.h>

#define MAXEV 4

int main(int argc, char **argv)
{
	if (argc < 6) {
		fprintf(stderr, "usage: memreg cpu budget period_us poll_us seconds [event_hex...]\n");
		return 1;
	}
	int cpu = atoi(argv[1]);
	uint64_t budget = strtoull(argv[2], 0, 0);
	int64_t period = atoll(argv[3]) * 1000, poll = atoll(argv[4]) * 1000;
	int64_t secs = atoll(argv[5]), end = now_ns() + secs * 1000000000LL;
	const char *dflt[] = { "202", "402" };
	int nev = argc > 6 ? argc - 6 : 2, fd[MAXEV];
	int timed = argc > 6 && !strcmp(argv[6], "time");
	if (nev > MAXEV) nev = MAXEV;
	volatile uint64_t *l2ctr = NULL;
	if (argc > 6 && !strncmp(argv[6], "l2=", 3)) {
		volatile uint8_t *r = mmio(CCACHE, 0x4000, "/dev/mem L2");
		if (!r)
			return 1;
		*(volatile uint64_t *)(r + CC_SEL) = strtoull(argv[6] + 3, 0, 16);
		l2ctr = (volatile uint64_t *)(r + CC_CTR);
	}
	if (timed || l2ctr) nev = 0;

	if (pin(cpu, 98)) {
		perror("affinity/FIFO");
		return 1;
	}
	for (int i = 0; i < nev; i++) {
		struct perf_event_attr a = { .size = sizeof(a), .type = PERF_TYPE_RAW,
			.config = strtoull(argc > 6 ? argv[6 + i] : dflt[i], 0, 16) };
		fd[i] = syscall(SYS_perf_event_open, &a, -1, cpu, -1, 0);
		if (fd[i] < 0) { perror("perf_event_open"); return 1; }
	}

	uint64_t base = 0, periods = 0, throttled = 0, spun_ns = 0, peak = 0;
	uint64_t sum_used = 0;
	int64_t pstart = now_ns() / period * period, next_report = pstart + 1000000000LL;
	for (int64_t t = pstart; t < end; ) {
		uint64_t c = timed ? now_ns() / 1000 : l2ctr ? *l2ctr : 0, v;
		for (int i = 0; i < nev; i++)
			if (read(fd[i], &v, sizeof(v)) == sizeof(v))
				c += v;
		if (!periods && !base) base = c;
		uint64_t used = c - base;
		t = now_ns();
		if (t >= pstart + period) {		/* period over: refill */
			if (used > peak) peak = used;
			sum_used += used;
			periods++;
			base = c;
			pstart += period * ((t - pstart) / period);
			used = 0;
		}
		if (budget && used >= budget) {		/* exhausted: hold the CPU */
			throttled++;
			int64_t s = now_ns();
			while ((t = now_ns()) < pstart + period)
				;
			spun_ns += t - s;
			continue;
		}
		if (!budget && t >= next_report) {
			printf("%.0f events/period avg, peak %llu\n",
			       periods ? (double)sum_used / periods : 0, (unsigned long long)peak);
			fflush(stdout);
			next_report += 1000000000LL;
		}
		int64_t nxt = t + poll;
		sleep_until(nxt < pstart + period ? nxt : pstart + period);
	}
	struct rusage ru;
	getrusage(RUSAGE_SELF, &ru);
	double cpu_s = ru.ru_utime.tv_sec + ru.ru_stime.tv_sec +
		       (ru.ru_utime.tv_usec + ru.ru_stime.tv_usec) * 1e-6;
	printf("cpu %d budget %llu period %lld us: periods %llu throttled %llu (%.1f %%) "
	       "spun %.1f %% cpu %.1f %% avg %.0f peak %llu events/period\n",
	       cpu, (unsigned long long)budget, (long long)(period / 1000),
	       (unsigned long long)periods, (unsigned long long)throttled,
	       periods ? 100.0 * throttled / periods : 0,
	       spun_ns / (secs * 1e7), 100.0 * cpu_s / secs,
	       periods ? (double)sum_used / periods : 0, (unsigned long long)peak);
	return 0;
}
