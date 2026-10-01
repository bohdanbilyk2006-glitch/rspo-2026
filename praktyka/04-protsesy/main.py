import os
import platform
import sys
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor

import matplotlib.pyplot as plt


W, H = 1500, 1000
MAX_ITER = 300
XMIN, XMAX = -2.0, 0.6
YMIN, YMAX = -1.2, 1.2

PHYSICAL_CORES = 16
CHUNKSIZE = 8


def ryadok(y):
    cy = YMIN + (YMAX - YMIN) * y / H
    out = []

    for x in range(W):
        cx = XMIN + (XMAX - XMIN) * x / W
        zx = zy = 0.0
        n = 0

        while zx * zx + zy * zy <= 4.0 and n < MAX_ITER:
            zx, zy = (
                zx * zx - zy * zy + cx,
                2.0 * zx * zy + cy
            )
            n += 1

        out.append(n)

    return out


def poslidovno():
    return [ryadok(y) for y in range(H)]


def protsesamy(n):
    with ProcessPoolExecutor(max_workers=n) as ex:
        return list(
            ex.map(
                ryadok,
                range(H),
                chunksize=CHUNKSIZE
            )
        )


def zamir(fn, prohoniv=3, *args):
    chasy = []

    for _ in range(prohoniv):
        t = perf_counter()
        result = fn(*args)
        chasy.append(perf_counter() - t)

    return min(chasy), chasy, result


if __name__ == "__main__":
    logical_cores = os.cpu_count()
    processes = [1, 2, 4, 8, logical_cores]

    print("Процессор:", platform.processor())
    print("Физических ядер:", PHYSICAL_CORES)
    print("Логических процессоров:", logical_cores)
    print("Python:", sys.version)
    print("Размер:", W, "x", H)
    print("MAX_ITER:", MAX_ITER)

    t_base, times_base, base = zamir(poslidovno, 3)

    print("\nПоследовательно")
    print("Прогоны:", [round(t, 6) for t in times_base])
    print("Минимум:", round(t_base, 6))
    print("Ускорение: 1.000")

    speedups = []
    efficiencies = []

    for n in processes:
        t, times, result = zamir(protsesamy, 3, n)

        assert result == base

        speedup = t_base / t
        efficiency = speedup / n

        print("\nПроцессов:", n)
        print("Прогоны:", [round(x, 6) for x in times])
        print("Минимум:", round(t, 6))
        print("Ускорение:", round(speedup, 3))
        print("Эффективность:", round(efficiency, 3))

        speedups.append(speedup)
        efficiencies.append(efficiency)

    plt.plot(
        processes,
        speedups,
        "o-",
        label="Ускорение"
    )

    plt.plot(
        processes,
        processes,
        "--",
        label="Идеал"
    )

    plt.xlabel("Количество процессов")
    plt.ylabel("Ускорение")
    plt.xticks(processes)
    plt.grid()
    plt.legend(loc="upper left")

    ax2 = plt.gca().twinx()

    ax2.plot(
        processes,
        efficiencies,
        "s-",
        label="Эффективность"
    )

    ax2.set_ylabel("Эффективность S/N")
    ax2.set_ylim(0, 1.1)
    ax2.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig("grafik.png")
    plt.show()
