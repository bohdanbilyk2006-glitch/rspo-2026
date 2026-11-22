"""Клієнт служби «журнал замірів».

Без прапорців клієнт виконує одну спробу без таймауту й без ключа.
Це дає змогу порівняти кожне виправлення на тому самому стенді.

    python kliyent.py --kilkist 10
    python kliyent.py --port 50010 --taimaut 2
    python kliyent.py --port 50010 --taimaut 2 --sprob 4
    python kliyent.py --port 50010 --taimaut 2 --sprob 4 --kliuch
"""

import argparse
import json
import math
import socket
import time
import uuid

HOST = "127.0.0.1"
PORT_SLUZHBY = 50007
POMYLKY_OBMINU = (OSError, ValueError)


def poslaty(port, zapyt, taimaut):
    """Надіслати один рядок JSON і прочитати підтвердження служби."""
    with socket.create_connection((HOST, port), timeout=taimaut) as soket:
        with soket.makefile("rwb") as potik:
            potik.write((json.dumps(zapyt, ensure_ascii=False) + "\n").encode())
            potik.flush()
            ryadok = potik.readline()

    if not ryadok:
        raise ConnectionError("з'єднання закрито без відповіді")
    if not ryadok.endswith(b"\n"):
        raise ConnectionError("з'єднання закрито посеред відповіді")

    vidpovid = json.loads(ryadok)
    if not isinstance(vidpovid, dict) or vidpovid.get("status") != "ok":
        raise ValueError("служба не підтвердила операцію")
    return vidpovid


def poslaty_z_povtoramy(port, zapyt, taimaut, sprob):
    """Повторювати той самий запит після пауз 0,2, 0,4 та 0,8 с."""
    pauza = 0.2
    for sproba in range(1, sprob + 1):
        try:
            return poslaty(port, zapyt, taimaut), sproba
        except POMYLKY_OBMINU:
            if sproba == sprob:
                raise
            time.sleep(pauza)
            pauza *= 2


def stan_sluzhby(port):
    """Прочитати лічильники напряму, оминаючи проксі."""
    stan = poslaty(port, {"dia": "stan"}, taimaut=5)
    if not all(type(stan.get(pole)) is int for pole in ("vsogo", "unikalnyh_kliuchiv")):
        raise ValueError("служба повернула некоректні лічильники")
    return stan


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=PORT_SLUZHBY,
                   help="50007 — напряму до служби, 50010 — через ненадійну мережу")
    p.add_argument("--port-sluzhby", type=int, default=PORT_SLUZHBY,
                   help="прямий порт служби для читання стану журналу")
    p.add_argument("--kilkist", type=int, default=10, help="скільки замірів надіслати")
    p.add_argument("--taimaut", type=float,
                   help="скільки секунд чекати на мережеву операцію")
    p.add_argument("--sprob", type=int, default=1,
                   help="максимум спроб для одного запису разом із першою")
    p.add_argument("--kliuch", action="store_true",
                   help="використовувати той самий ключ для всіх спроб одного запису")
    args = p.parse_args()
    if args.kilkist < 0:
        p.error("--kilkist має бути невід'ємною")
    if args.sprob < 1:
        p.error("--sprob має бути не менше 1")
    if args.taimaut is not None and (not math.isfinite(args.taimaut) or args.taimaut <= 0):
        p.error("--taimaut має бути додатним скінченним числом")

    print(f"[клієнт] порт {args.port} · таймаут {args.taimaut} · спроб {args.sprob}"
          f" · ключ {'так' if args.kliuch else 'ні'}")
    try:
        pochatok = stan_sluzhby(args.port_sluzhby)["vsogo"]
    except POMYLKY_OBMINU as e:
        pochatok = None
        print(f"[служба] початковий стан недоступний · {e}")

    nadislano = 0
    povtoriv = 0
    t_start = time.perf_counter()
    for i in range(args.kilkist):
        zapys = {"rozmir": "1200x800", "chas": round(0.15 + i * 0.01, 3)}
        zapyt = {"dia": "dodaty", "zapys": zapys}
        if args.kliuch:
            # Ключ належить запису, тому створюємо його перед першою спробою.
            zapyt["kliuch"] = str(uuid.uuid4())

        t0 = time.perf_counter()
        try:
            vidpovid, sprob = poslaty_z_povtoramy(args.port, zapyt, args.taimaut, args.sprob)
        except POMYLKY_OBMINU as e:
            povtoriv += args.sprob - 1
            print(f"  {i + 1:>3}. ❌ {type(e).__name__}: {e}"
                  f" · {1000 * (time.perf_counter() - t0):.0f} мс · спроб {args.sprob}")
        else:
            nadislano += 1
            povtoriv += sprob - 1
            print(f"  {i + 1:>3}. {vidpovid} · {1000 * (time.perf_counter() - t0):.0f} мс"
                  + (f" · спроб {sprob}" if sprob > 1 else ""))

    zagalom = time.perf_counter() - t_start
    print(f"\n[клієнт] надіслано успішно {nadislano} з {args.kilkist}"
          f" · помилок {args.kilkist - nadislano} · зайвих спроб {povtoriv} · разом {zagalom:.3f} с")

    try:
        stan = stan_sluzhby(args.port_sluzhby)
    except POMYLKY_OBMINU as e:
        print(f"[служба] кінцевий стан недоступний · {e}")
        return

    print(f"[служба] у журналі записів: {stan['vsogo']}"
          f" · унікальних ключів: {stan['unikalnyh_kliuchiv']}")
    if pochatok is None:
        return
    dodano = stan["vsogo"] - pochatok
    if dodano < 0:
        print("[служба] лічильник зменшився, порівняти стани журналу неможливо")
        return

    print(f"[служба] додано за цей запуск: {dodano}")
    if dodano > args.kilkist:
        print(f"⚠️  ДУБЛІКАТИ: щонайменше {dodano - args.kilkist} зайвих записів")
    elif dodano > nadislano:
        print(f"⚠️  НЕВИЗНАЧЕНІСТЬ: у журналі додалося {dodano}, підтверджень {nadislano}")
    elif dodano < args.kilkist:
        print(f"⚠️  У журналі додалося {dodano} із {args.kilkist} очікуваних записів")
    elif dodano == nadislano:
        print("✔ рівно стільки, скільки надсилали")


if __name__ == "__main__":
    main()
