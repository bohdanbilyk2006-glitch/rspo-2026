import multiprocessing as mp
import os
import platform
import random
import subprocess
import sys
import time

ZAPAS_POCHATKOVYI = 30_000
PROTSESIV = 4
ZAMOVLEN_NA_PROTSES = 20_000
MAX_U_ZAMOVLENNI = 3
PROGONIV = 10

sys.setswitchinterval(1e-6)


def fizychni_yadra():
    result = subprocess.check_output(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "(Get-CimInstance Win32_Processor | "
            "Measure-Object -Property NumberOfCores -Sum).Sum"
        ],
        text=True
    )
    return int(result.strip())


def obrobyty_zamovlennya(
    zalyshok,
    vidvantazheno,
    vidmov,
    zamok,
    nasinnya
):
    rnd = random.Random(nasinnya)

    for _ in range(ZAMOVLEN_NA_PROTSES):
        kilkist = rnd.randint(1, MAX_U_ZAMOVLENNI)

        with zamok:
            if zalyshok.value >= kilkist:
                zalyshok.value = zalyshok.value - kilkist
                vidvantazheno.value = vidvantazheno.value + kilkist
            else:
                vidmov.value = vidmov.value + 1


def prognaty(nomer):
    zalyshok = mp.Value("i", ZAPAS_POCHATKOVYI)
    vidvantazheno = mp.Value("i", 0)
    vidmov = mp.Value("i", 0)
    zamok = mp.Lock()

    procesy = [
        mp.Process(
            target=obrobyty_zamovlennya,
            args=(
                zalyshok,
                vidvantazheno,
                vidmov,
                zamok,
                1000 + i
            )
        )
        for i in range(PROTSESIV)
    ]

    t0 = time.perf_counter()

    for p in procesy:
        p.start()

    for p in procesy:
        p.join()

    tryvalist = time.perf_counter() - t0

    z = zalyshok.value
    v = vidvantazheno.value
    vm = vidmov.value

    porushennya = []

    if z < 0:
        porushennya.append(
            "залишок від'ємний: %d" % z
        )

    if v + z != ZAPAS_POCHATKOVYI:
        porushennya.append(
            "баланс не сходиться: %d + %d = %d, а має бути %d"
            % (v, z, v + z, ZAPAS_POCHATKOVYI)
        )

    stan = "OK" if not porushennya else "ПОРУШЕНО"

    print(
        "Прогін %d: залишок %d, відвантажено %d, "
        "відмов %d, %.4f с, %s"
        % (nomer, z, v, vm, tryvalist, stan)
    )

    for p in porushennya:
        print("  ->", p)

    return not porushennya, tryvalist


if __name__ == "__main__":
    print("Процесор:", platform.processor())
    print("Фізичних ядер:", fizychni_yadra())
    print("Логічних процесорів:", os.cpu_count())
    print("Python:", sys.version)
    print("ОС:", platform.platform())
    print("Процесів:", PROTSESIV)
    print("Замовлень на процес:", ZAMOVLEN_NA_PROTSES)
    print("Початковий запас:", ZAPAS_POCHATKOVYI)
    print("Switch interval:", sys.getswitchinterval())

    chysto = 0
    chasy = []

    print("\nПісля виправлення")

    for i in range(1, PROGONIV + 1):
        ok, t = prognaty(i)
        chasy.append(t)

        if ok:
            chysto += 1

    print("\nБез порушень:", chysto, "із", PROGONIV)
    print("Часи:", [round(t, 4) for t in chasy])
    print(
        "Середній час:",
        round(sum(chasy) / len(chasy), 4),
        "с"
    )
