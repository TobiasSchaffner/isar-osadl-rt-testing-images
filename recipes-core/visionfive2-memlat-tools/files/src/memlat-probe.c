/*
 * DRAM access latency probe.
 *
 * Walks a random cyclic pointer chain through a buffer far larger than the
 * JH7110 L2 (2 MB), so every load is a dependent cache miss. Once per
 * second it times LOADS dependent loads and prints "<unix time> <ns/load>".
 * Run pinned to an isolated core: memlat-probe [cpu] [seconds]
 */
#include "jh7110.h"

#define BUF   (64UL << 20)
#define LOADS 2000

int main(int argc, char **argv)
{
	int cpu = argc > 1 ? atoi(argv[1]) : 3, secs = argc > 2 ? atoi(argv[2]) : 600;
	size_t n = BUF / LINE, i;

	if (pin(cpu, 98))
		perror("affinity/fifo");
	mlockall(MCL_CURRENT | MCL_FUTURE);

	char *buf = aligned_alloc(LINE, BUF);
	if (!buf || chase_init(buf, n))
		return 1;

	void **p = (void **)buf;
	double next = now_s(CLOCK_MONOTONIC);
	for (int s = 0; s < secs; s++) {
		next += 1.0;
		double t0 = now_s(CLOCK_MONOTONIC);
		for (i = 0; i < LOADS; i++)
			p = *p;
		double dt = now_s(CLOCK_MONOTONIC) - t0;
		printf("%.3f %.1f\n", now_s(CLOCK_REALTIME), dt * 1e9 / LOADS);
		fflush(stdout);
		sleep_until((int64_t)(next * 1e9));
	}
	return p == NULL;	/* keep the chase live */
}
