/*
 * Probe the performance counters of the SiFive L2 cache controller
 * (JH7110: 0x2010000) through /dev/mem. SiFive layout: event selector n at
 * 0x2000 + 8n (bits 7:0 event set, bits 63:8 event mask), client filter at
 * 0x2800, counter n at 0x3000 + 8n.
 *
 * usage: l2pmu                       dump selectors, filter, counters 0..7
 *        l2pmu SECS SEL0 [SEL1 ...]  program selectors (hex), print each
 *                                    counter's increase over SECS seconds
 */
#include "jh7110.h"

#define NCTR 8

int main(int argc, char **argv)
{
	volatile uint8_t *r = mmio(CCACHE, 0x4000, NULL);
	if (!r)
		return 1;
	volatile uint64_t *sel = (volatile uint64_t *)(r + CC_SEL);
	volatile uint64_t *ctr = (volatile uint64_t *)(r + CC_CTR);

	if (argc < 3) {
		for (int i = 0; i < NCTR; i++)
			printf("sel%d 0x%016llx  ctr%d %llu\n", i, (unsigned long long)sel[i],
			       i, (unsigned long long)ctr[i]);
		printf("filter 0x%016llx\n", (unsigned long long)*(volatile uint64_t *)(r + CC_FILTER));
		return 0;
	}
	int n = argc - 2;
	if (n > NCTR) n = NCTR;
	uint64_t before[NCTR];
	for (int i = 0; i < n; i++)
		sel[i] = strtoull(argv[2 + i], 0, 16);
	for (int i = 0; i < n; i++)
		before[i] = ctr[i];
	sleep(atoi(argv[1]));
	for (int i = 0; i < n; i++)
		printf("sel 0x%llx: %llu\n", (unsigned long long)sel[i],
		       (unsigned long long)(ctr[i] - before[i]));
	return 0;
}
