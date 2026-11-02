/*
 * Read and set the per-hart SiFive L2 prefetchers (U74-MC: 0x2030000 +
 * 0x2000 * hart) through /dev/mem. basicCtrl at +0 (bit 0 scalar loads,
 * bit 28 cross 4 KiB pages), additionalCtrl at +4 (bit 19 scalar stores).
 * See the U74 Core Complex Manual, chapter "Level 2 Prefetcher".
 *
 * Hart 0 is the S7 monitor core without a prefetcher; accessing its slot
 * faults.
 *
 * usage: pfctl                          dump basicCtrl/additionalCtrl of harts 1..4
 *        pfctl HART BASIC ADDITIONAL    set both registers (hex), then dump
 */
#include "jh7110.h"

#define HARTS 5

int main(int argc, char **argv)
{
	volatile uint8_t *r = mmio(PF_BASE, HARTS * 0x2000, NULL);
	if (!r)
		return 1;

	for (int i = 1; i + 2 < argc; i += 3) {
		int h = atoi(argv[i]);
		if (h < 1 || h >= HARTS) { fprintf(stderr, "bad hart %s\n", argv[i]); return 1; }
		volatile uint32_t *c = (volatile uint32_t *)(r + 0x2000 * h);
		c[0] = strtoul(argv[i + 1], 0, 16);
		c[1] = strtoul(argv[i + 2], 0, 16);
	}
	for (int h = 1; h < HARTS; h++) {
		volatile uint32_t *c = (volatile uint32_t *)(r + 0x2000 * h);
		printf("hart %d basicCtrl 0x%08x additionalCtrl 0x%08x\n", h, c[0], c[1]);
	}
	return 0;
}
