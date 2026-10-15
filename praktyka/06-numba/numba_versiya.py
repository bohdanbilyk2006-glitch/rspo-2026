import os
import platform
import subprocess
import sys
import numba
import numpy as np
from numba import njit, prange
from time import perf_counter

W, H = 1500, 1000
MAX_ITER = 300
XMIN, XMAX = -2.0, 0.6
YMIN, YMAX = -1.2, 1.2


def fizychni_yadra():
    try:
        rezultat = subprocess.check_output(
            [
                "powershell.exe", "-NoProfile", "-Command",
                "(Get-CimInstance Win32_Processor | "
                "Measure-Object -Property NumberOfCores -Sum).Sum"
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=20
        )
        return int(rezultat.strip())
    except (OSError, ValueError, subprocess.SubprocessError):
        return "не удалось определить"


def pasport():
    print("Процессор:", platform.processor())
    print("Физических ядер:", fizychni_yadra())
    print("Логических процессоров:", os.cpu_count())
    print("Python:", sys.version)
    print("ОС:", platform.platform())
    print("NumPy:", np.__version__)
    print("Numba:", numba.__version__)
    print("Размер:", W, "x", H)
    print("MAX_ITER:", MAX_ITER)
    print("Область X:", XMIN, "..", XMAX)
    print("Область Y:", YMIN, "..", YMAX)
    print("Прогонов Python:", 1)
    print("Первых вызовов каждой Numba-функции:", 1)
    print("Прогонов каждой Numba-функции после компиляции:", 3)
    print(flush=True)


def ryadok(y):
    cy = YMIN + (YMAX - YMIN) * y / H
    out = []

    for x in range(W):
        cx = XMIN + (XMAX - XMIN) * x / W
        zx = zy = 0.0
        n = 0

        while zx * zx + zy * zy <= 4.0 and n < MAX_ITER:
            zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
            n += 1

        out.append(n)

    return out


def poslidovno():
    return [ryadok(y) for y in range(H)]


def zamir(fn, prohoniv=3, *a):
    chasy = []

    for _ in range(prohoniv):
        t = perf_counter()
        r = fn(*a)
        chasy.append(perf_counter() - t)

    return min(chasy), chasy, r


@njit
def mandelbrot_numba(W, H, MAX_ITER, XMIN, XMAX, YMIN, YMAX):
    out = np.empty((H, W), dtype=np.int32)

    for y in range(H):
        cy = YMIN + (YMAX - YMIN) * y / H

        for x in range(W):
            cx = XMIN + (XMAX - XMIN) * x / W
            zx = 0.0
            zy = 0.0
            n = 0

            while zx * zx + zy * zy <= 4.0 and n < MAX_ITER:
                zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
                n += 1

            out[y, x] = n

    return out


@njit(parallel=True)
def mandelbrot_prange(W, H, MAX_ITER, XMIN, XMAX, YMIN, YMAX):
    out = np.empty((H, W), dtype=np.int32)

    for y in prange(H):
        cy = YMIN + (YMAX - YMIN) * y / H

        for x in range(W):
            cx = XMIN + (XMAX - XMIN) * x / W
            zx = 0.0
            zy = 0.0
            n = 0

            while zx * zx + zy * zy <= 4.0 and n < MAX_ITER:
                zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
                n += 1

            out[y, x] = n

    return out


if __name__ == "__main__":
    pasport()

    t_base, chasy, base = zamir(poslidovno, 1)
    base = np.array(base)
    ARGS = (W, H, MAX_ITER, XMIN, XMAX, YMIN, YMAX)

    print("Последовательно (Python):", round(t_base, 4), "с")

    t0 = perf_counter()
    mandelbrot_numba(*ARGS)
    print("Первый вызов @njit (компиляция + выполнение):", round(perf_counter() - t0, 4), "с")

    t, chasy, r = zamir(mandelbrot_numba, 3, *ARGS)
    assert np.array_equal(r, base), "результат розійшовся з еталоном"

    print("@njit:", [round(c, 4) for c in chasy],
          "минимум:", round(t, 4),
          "ускорение:", round(t_base / t, 2))

    t0 = perf_counter()
    mandelbrot_prange(*ARGS)
    print("Первый вызов prange (компиляция + выполнение):", round(perf_counter() - t0, 4), "с")

    t_prange, chasy_prange, r_prange = zamir(
        mandelbrot_prange, 3, *ARGS
    )
    assert np.array_equal(r_prange, base), "результат розійшовся з еталоном"

    print("prange:", [round(c, 4) for c in chasy_prange],
          "минимум:", round(t_prange, 4),
          "ускорение:", round(t_base / t_prange, 2),
          "относительно @njit:", round(t / t_prange, 2))

    print("Потоков Numba для prange:", numba.get_num_threads())
