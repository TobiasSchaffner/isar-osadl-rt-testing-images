/*
 * Memory aggressor with controlled locality and rate, to tell contention in
 * the L2 cache controller from contention in the DDR controller.
 *
 * Visits the blocks of a BUF_KB buffer in a scattered order (odd stride
 * modulo the block count) and touches every 64-byte line of a block in
 * sequence. BLOCK = 64 scatters every access like stress-ng prime-1; larger
 * blocks keep the same number of L2 misses and write-backs per line but let
 * consecutive accesses fall into the same DRAM row. A buffer that fits into
 * the core's L2 ways produces L2 traffic without DRAM traffic.
 *
 * usage: aggr cpu buf_kb block_bytes mlines_per_s secs w|r|s [mem]
 *        mlines_per_s 0 = unthrottled; w = read-modify-write, r = read only,
 *        s = store only (the in-order U74 stalls on each load miss of w and
 *        r, while stores let several misses overlap)
 * prints the achieved rate in million lines per second and, from
 * /proc/self/pagemap (root), the physical range of the buffer, the number of
 * physically contiguous runs and the share of pages per 512 MB of DRAM
 *
 * mem (optional) selects how the buffer is backed:
 *   huge          2 MB huge pages (needs vm.nr_hugepages): few TLB misses
 *   alias:KB      one KB memfd mapped repeatedly: TLB and page-table
 *                 footprint of BUF_KB, DRAM footprint of KB
 *   region:R:KB   sweep, page by page in sequence, only the first KB of the
 *                 buffer's pages in physical 512 MB chunk R (address >> 29,
 *                 DRAM starts at chunk 2); BLOCK is then ignored
 */
#include "jh7110.h"

/* Physical address of the page at p, from /proc/self/pagemap; -1 if unreadable. */
static int phys(FILE *pm, const volatile void *p, unsigned long long *pa)
{
	unsigned long long e;

	if (pread(fileno(pm), &e, 8, (unsigned long)p / 4096 * 8) != 8)
		return -1;
	*pa = (e & ((1ULL << 55) - 1)) << 12;
	return 0;
}

int main(int argc, char **argv)
{
	if (argc < 7) {
		fprintf(stderr, "usage: aggr cpu buf_kb block mlines_per_s secs w|r|s\n");
		return 1;
	}
	int cpu = atoi(argv[1]), mode = argv[6][0];
	size_t buf_sz = (size_t)atol(argv[2]) << 10, block = atol(argv[3]);
	double rate = atof(argv[4]) * 1e6, secs = atof(argv[5]);
	size_t nblk = buf_sz / block, lpb = block / LINE;

	/* block count must be a power of two for the odd stride to visit all */
	if (block < LINE || block % LINE || !nblk || nblk & (nblk - 1)) {
		fprintf(stderr, "buf/block must be a power of two, block >= %d\n", LINE);
		return 1;
	}
	if (pin(cpu, 0))
		perror("affinity");
	const char *mem = argc > 7 ? argv[7] : "";
	volatile unsigned char *buf;
	if (!strcmp(mem, "huge")) {
		buf = mmap(0, buf_sz, PROT_READ | PROT_WRITE,
			   MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
	} else if (!strncmp(mem, "alias:", 6)) {
		size_t phys = (size_t)atol(mem + 6) << 10;
		int fd = memfd_create("aggr", 0);
		buf = mmap(0, buf_sz, PROT_NONE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
		if (fd < 0 || ftruncate(fd, phys) || buf == MAP_FAILED || buf_sz % phys) {
			perror("alias");
			return 1;
		}
		for (size_t off = 0; off < buf_sz; off += phys)
			if (mmap((void *)(buf + off), phys, PROT_READ | PROT_WRITE,
				 MAP_SHARED | MAP_FIXED, fd, 0) == MAP_FAILED) {
				perror("alias mmap");
				return 1;
			}
	} else {
		buf = aligned_alloc(4096, buf_sz);
	}
	if (buf == MAP_FAILED || !buf) {
		perror("buffer");
		return 1;
	}
	memset((void *)buf, 1, buf_sz);

	FILE *pm = fopen("/proc/self/pagemap", "r");
	unsigned long long lo = ~0ULL, hi = 0, prev = 0, pa, runs = 0, part[16] = { 0 };
	for (size_t off = 0; pm && off < buf_sz; off += 4096) {
		if (phys(pm, buf + off, &pa))
			break;
		lo = pa < lo ? pa : lo, hi = pa > hi ? pa : hi;
		runs += pa != prev + 4096;
		part[(pa >> 29) & 15]++;
		prev = pa;
	}
	volatile unsigned char **pg = NULL;
	if (!strncmp(mem, "region:", 7)) {
		int region = atoi(mem + 7);
		size_t want = (size_t)atol(strchr(mem + 7, ':') + 1) / 4, got = 0;
		pg = malloc(want * sizeof(*pg));
		for (size_t off = 0; got < want && off < buf_sz; off += 4096) {
			if (phys(pm, buf + off, &pa))
				break;
			if (pa >> 29 == (unsigned)region)
				pg[got++] = buf + off;
		}
		if (got < want || want & (want - 1)) {
			fprintf(stderr, "region %d: %zu of %zu pages (need a power of two)\n",
				region, got, want);
			return 1;
		}
		block = 4096, lpb = block / LINE, nblk = want;
	}
	size_t stride = pg ? 1 : (0x9E3779B1UL % nblk) | 1, b = 0, lines = 0;
	unsigned sum = 0;
	double t0 = now_s(CLOCK_MONOTONIC), t = t0, end = t0 + secs;
	while (t < end) {
		/* 256 lines between clock reads and rate checks */
		for (int k = 0; k < 256; k += lpb) {
			volatile unsigned char *p = pg ? pg[b] : buf + b * block;
			for (size_t l = 0; l < lpb; l++, p += LINE)
				if (mode == 'w')
					p[0]++;
				else if (mode == 's')
					p[0] = l;
				else
					sum += p[0];
			b = (b + stride) & (nblk - 1);
			lines += lpb;
		}
		t = now_s(CLOCK_MONOTONIC);
		if (rate > 0)
			while (lines > (t - t0) * rate && t < end)
				t = now_s(CLOCK_MONOTONIC);
	}
	printf("%.3f Mlines/s%s\n", lines / (t - t0) / 1e6, sum == 1 ? " " : "");
	printf("phys 0x%llx-0x%llx runs %llu per512M", lo, hi, runs);
	for (int i = 0; i < 16; i++)
		if (part[i])
			printf(" %d:%llu", i, part[i]);
	printf("\n");
	return 0;
}
