/*
 * Shared by the JH7110 (SiFive U74-MC) tools: clocks, pinning to a CPU,
 * register access through /dev/mem and the random pointer chase.
 * Include it first; it sets _GNU_SOURCE.
 */
#ifndef JH7110_H
#define JH7110_H

#define _GNU_SOURCE
#include <fcntl.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#define LINE 64

/* SiFive L2 cache controller (sifive,ccache0) */
#define CCACHE		0x2010000UL
#define CC_WAYENABLE	0x008
#define CC_WAYMASK	0x800		/* WayMask<i> at + 8i */
#define CC_SEL		0x2000		/* event selector n at + 8n */
#define CC_FILTER	0x2800
#define CC_CTR		0x3000		/* counter n at + 8n */
/* per-hart L2 prefetchers at + 0x2000 * hart */
#define PF_BASE		0x2030000UL

static inline double now_s(clockid_t c)
{
	struct timespec ts;
	clock_gettime(c, &ts);
	return ts.tv_sec + ts.tv_nsec * 1e-9;
}

static inline int64_t now_ns(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

static inline void sleep_until(int64_t t)
{
	struct timespec ts = { t / 1000000000LL, t % 1000000000LL };
	clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &ts, NULL);
}

/* Pin to cpu and, if prio, run SCHED_FIFO at prio; nonzero on failure. */
static inline int pin(int cpu, int prio)
{
	cpu_set_t set;
	struct sched_param sp = { .sched_priority = prio };

	CPU_ZERO(&set);
	CPU_SET(cpu, &set);
	return sched_setaffinity(0, sizeof(set), &set) ||
	       (prio && sched_setscheduler(0, SCHED_FIFO, &sp));
}

/*
 * Map len bytes of physical memory at base. On failure prints err, or the
 * step that failed ("/dev/mem" or "mmap"), and returns NULL.
 */
static inline volatile uint8_t *mmio(unsigned long base, size_t len, const char *err)
{
	int fd = open("/dev/mem", O_RDWR | O_SYNC);
	void *r = fd < 0 ? MAP_FAILED :
		mmap(0, len, PROT_READ | PROT_WRITE, MAP_SHARED, fd, base);

	if (r == MAP_FAILED) {
		perror(err ? err : fd < 0 ? "/dev/mem" : "mmap");
		return NULL;
	}
	return r;
}

/*
 * Link the n lines of buf into one random cycle (Fisher-Yates with a fixed
 * seed, so every run walks the same chain); -1 if out of memory.
 */
static inline int chase_init(char *buf, size_t n)
{
	size_t *perm = malloc(n * sizeof(*perm)), i;

	if (!perm)
		return -1;
	for (i = 0; i < n; i++)
		perm[i] = i;
	srand(1);
	for (i = n - 1; i > 0; i--) {
		size_t j = ((size_t)rand() << 16 ^ rand()) % (i + 1), t = perm[i];
		perm[i] = perm[j], perm[j] = t;
	}
	for (i = 0; i < n; i++)
		*(void **)(buf + perm[i] * LINE) = buf + perm[(i + 1) % n] * LINE;
	free(perm);
	return 0;
}

#endif
