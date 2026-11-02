/*
 * Read and set the way-mask registers of the SiFive L2 cache controller
 * (JH7110: sifive,ccache0 at 0x2010000) through /dev/mem.
 *
 * WayMask<i> at 0x800 + 8*i restricts the ways master i may allocate into on
 * a miss; hits in any way are unaffected. The JH7110 has 32 of them. The
 * id map is undocumented; masking each id to one way and timing a 1 MB
 * pointer chase showed the data side of hart h at ids 5*h+8 and 5*h+9
 * (Linux CPU 0 is the boot hart, see /proc/cpuinfo).
 *
 * usage: waymask                    dump config, WayEnable, WayMask0..31
 *        waymask ID MASK [ID MASK]  set masks (hex), then dump
 */
#include "jh7110.h"

#define SIZE    0x1000
#define MASTERS 32

int main(int argc, char **argv)
{
	volatile uint8_t *r = mmio(CCACHE, SIZE, NULL);
	if (!r)
		return 1;
	volatile uint64_t *mask = (volatile uint64_t *)(r + CC_WAYMASK);
	uint32_t cfg = *(volatile uint32_t *)r;
	unsigned ways = (cfg >> 8) & 0xff;

	for (int i = 1; i + 1 < argc; i += 2) {
		int id = atoi(argv[i]);
		uint64_t m = strtoull(argv[i + 1], 0, 16);
		/* an empty mask would leave the master nowhere to allocate */
		if (id < 0 || id >= MASTERS || !m || m >> ways) {
			fprintf(stderr, "bad id/mask %s %s\n", argv[i], argv[i + 1]);
			return 1;
		}
		mask[id] = m;
	}
	printf("config banks %u ways %u sets 2^%u block 2^%u, WayEnable %u\n",
	       cfg & 0xff, ways, (cfg >> 16) & 0xff, cfg >> 24,
	       *(volatile uint32_t *)(r + CC_WAYENABLE));
	for (int i = 0; i < MASTERS; i++)
		printf("WayMask%-2d 0x%04llx\n", i, (unsigned long long)mask[i]);
	return 0;
}
