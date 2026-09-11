import os, platform, sys
from time import perf_counter
import cProfile, pstats


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


def zberegty_pgm(dani, shlyah="mandelbrot.pgm"):
    with open(shlyah, "wb") as f:
        f.write(b"P5\n%d %d\n255\n" % (W, H))
        f.write(bytes(min(255, v * 255 // MAX_ITER)
                      for r in dani for v in r))


def zamir(fn, prohoniv=3, *a):
    chasy = []

    for _ in range(prohoniv):
        t = perf_counter()
        r = fn(*a)
        chasy.append(perf_counter() - t)

    return min(chasy), chasy, r


if __name__ == "__main__":
    print(platform.processor())
    print("логічних ядер:", os.cpu_count())
    print("Python:", sys.version)
    print("ОС:", platform.platform())
    print("Размер:", W, "x", H)
    print("MAX_ITER:", MAX_ITER)
    print("Количество прогонов:", 3)

    t_calc, calc_times, base = zamir(poslidovno, 3)
    print("Время вычисления по прогонам:", calc_times)
    print("Минимум вычисления:", t_calc, "с")

    t_save, save_times, _ = zamir(zberegty_pgm, 3, base)
    print("Время сохранения по прогонам:", save_times)
    print("Минимум сохранения:", t_save, "с")

    s = t_save / (t_calc + t_save)
    print("Доля сохранения:", s * 100, "%")

    prof = cProfile.Profile()
    r = prof.runcall(poslidovno)


    with open("profil.txt", "w", encoding="utf-8") as f:
        pstats.Stats(prof, stream=f).sort_stats("cumulative").print_stats(10)
