import os
import platform
import subprocess
import sys
import numpy as np
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
    print("Размер:", W, "x", H)
    print("MAX_ITER:", MAX_ITER)
    print("Область X:", XMIN, "..", XMAX)
    print("Область Y:", YMIN, "..", YMAX)
    print("Вычислений эталона Python:", 1)
    print("Прогонов NumPy:", "по одному с endpoint=True и endpoint=False")
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


def mandelbrot_numpy(endpoint=False):
    cx, cy = np.meshgrid(
        np.linspace(XMIN, XMAX, W, endpoint=endpoint),
        np.linspace(YMIN, YMAX, H, endpoint=endpoint)
    )

    zx = np.zeros((H, W))
    zy = np.zeros((H, W))
    out = np.full((H, W), MAX_ITER, dtype=np.int32)
    aktyvni = np.ones((H, W), dtype=bool)

    for n in range(MAX_ITER):
        zx_n = zx * zx - zy * zy + cx
        zy_n = 2.0 * zx * zy + cy

        zx = np.where(aktyvni, zx_n, zx)
        zy = np.where(aktyvni, zy_n, zy)

        vyletily = aktyvni & (zx * zx + zy * zy > 4.0)
        out[vyletily] = n + 1
        aktyvni &= ~vyletily

        if not aktyvni.any():
            break

    return out


if __name__ == "__main__":
    pasport()

    base = np.array(poslidovno())

    for endpoint in (True, False):
        t = perf_counter()
        r = mandelbrot_numpy(endpoint)
        t_numpy = perf_counter() - t

        print("Endpoint:", endpoint)
        print("NumPy:", round(t_numpy, 4), "с")
        print("Различающихся точек:", int((r != base).sum()), "из", base.size)
