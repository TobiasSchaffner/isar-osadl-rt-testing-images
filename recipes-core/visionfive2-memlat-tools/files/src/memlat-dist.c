/*
 * Distribution of dependent-load latency.
 *
 * Chases a random cyclic pointer chain through a BUF_MB buffer and times
 * every batch of BATCH loads with the vDSO clock. Prints a histogram of
 * batch durations (log2 bins) and percentiles of ns/load. A 1 MB buffer
 * stays in the JH7110's 2 MB L2 and isolates the core from DRAM.
 * usage: memlat-dist cpu buf_mb seconds   (buf_mb may be fractional)
 */
#include "jh7110.h"

#define BATCH 16

static int cmp(const void *a, const void *b)
{
	return (*(const int *)a > *(const int *)b) - (*(const int *)a < *(const int *)b);
}

int main(int argc, char **argv)
{
	int cpu = atoi(argv[1]), secs = atoi(argv[3]);
	size_t buf_sz = (size_t)(atof(argv[2]) * (1 << 20)), n = buf_sz / LINE, i;

	if (pin(cpu, 98))
		perror("affinity/fifo");
	char *buf = aligned_alloc(LINE, buf_sz);
	chase_init(buf, n);
	mlockall(MCL_CURRENT | MCL_FUTURE);

	size_t cap = 20000000, k = 0;
	int *d = malloc(cap * sizeof(*d));	/* ns per batch */
	long long hist[32] = { 0 }, end = now_ns() + secs * 1000000000LL, t0 = now_ns(), t1;
	void **p = (void **)buf;
	while (t0 < end && k < cap) {
		for (i = 0; i < BATCH; i++)
			p = *p;
		t1 = now_ns();
		int b = 0, v = (int)(t1 - t0);
		while ((1 << (b + 1)) <= v && b < 31)
			b++;
		hist[b]++;
		d[k++] = v;
		t0 = t1;
	}
	qsort(d, k, sizeof(*d), cmp);
	printf("batches %zu, ns/load p50 %.0f p99 %.0f p99.9 %.0f p99.99 %.0f, max batch %.1f us\n",
	       k, d[k / 2] / (double)BATCH, d[k * 99 / 100] / (double)BATCH,
	       d[k * 999 / 1000] / (double)BATCH, d[k * 9999 / 10000] / (double)BATCH, d[k - 1] / 1e3);
	for (i = 0; i < 32; i++)
		if (hist[i])
			printf("batch %8d-%8d ns: %lld\n", 1 << i, (1 << (i + 1)) - 1, hist[i]);
	return p == NULL;
}
