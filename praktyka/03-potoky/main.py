import os, platform, sys, time
from concurrent.futures import ThreadPoolExecutor

W, H = 1500, 1000
MAX_ITER = 300
XMIN, XMAX = -2.0, 0.6
YMIN, YMAX = -1.2, 1.2


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
        t = time.perf_counter()
        r = fn(*a)
        chasy.append(time.perf_counter() - t)

    return min(chasy), chasy, r


def potokamy(n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        return list(ex.map(ryadok, range(H)))


def zapyt(nomer):
    time.sleep(0.5)
    return nomer


def zapyty_poslidovno():
    return [zapyt(i) for i in range(32)]


def zapyty_potokamy(n):
    with ThreadPoolExecutor(max_workers=n) as ex:
        return list(ex.map(zapyt, range(32)))


if __name__ == "__main__":
    print(platform.processor())
    print("Логических процессоров:", os.cpu_count())
    print("Python:", sys.version)
    print("GIL:", sys._is_gil_enabled())
    print("Размер:", W, "x", H)
    print("MAX_ITER:", MAX_ITER)
    print("Прогонов:", 3)

    print("\nМандельброт", flush=True)
    print("Вариант | три прогона, с | минимум, с | ускорение")

    t_base, chasy, base = zamir(poslidovno, 3)
    print("Последовательно", [round(c, 6) for c in chasy],
          round(t_base, 6), 1.0, sep=" | ")

    for n in (2, 4, 8, os.cpu_count()):
        t, chasy, r = zamir(potokamy, 3, n)
        assert r == base, "результат розійшовся з послідовним"
        print(n, [round(c, 6) for c in chasy],
              round(t, 6), round(t_base / t, 3), sep=" | ")

    print("\nCPU / wall: 8 потоков", flush=True)
    print("Прогон | wall, с | CPU, с | CPU / wall")

    for i in range(3):
        wall0 = time.perf_counter()
        cpu0 = time.process_time()

        r = potokamy(8)

        cpu = time.process_time() - cpu0
        wall = time.perf_counter() - wall0

        assert r == base, "результат розійшовся з послідовним"
        print(i + 1, round(wall, 6), round(cpu, 6),
              round(cpu / wall, 3), sep=" | ")

    print("\nОжидание: 32 задачи по 0.5 с", flush=True)
    print("Вариант | три прогона, с | минимум, с | ускорение")

    t_base, chasy, base = zamir(zapyty_poslidovno, 3)
    print("Последовательно", [round(c, 6) for c in chasy],
          round(t_base, 6), 1.0, sep=" | ")

    for n in (2, 4, 8, 16, 32):
        t, chasy, r = zamir(zapyty_potokamy, 3, n)
        assert r == base, "результат розійшовся з послідовним"
        print(n, [round(c, 6) for c in chasy],
              round(t, 6), round(t_base / t, 3), sep=" | ")