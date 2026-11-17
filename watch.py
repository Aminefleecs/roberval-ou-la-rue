#!/usr/bin/env python3
"""Roberval ou la rue : guette les chambres du Crous à Compiègne.

Interroge trouverunlogement.lescrous.fr (offre en cours d'année) et :
- sort l'artillerie lourde (voix + notif + navigateur + push téléphone)
  si un logement de la résidence Roberval apparaît ;
- envoie une notif simple pour tout autre nouveau logement à Compiègne.

Fait pour être lancé toutes les 2 min par launchd (voir install.sh).
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

DIR = Path(__file__).resolve().parent
STATE = DIR / "seen.json"
LOG = DIR / "watch.log"
TOPIC_FILE = DIR / "ntfy_topic.txt"

BASE = "https://trouverunlogement.lescrous.fr"
# Rectangle autour de Compiègne : (lon, lat) nord-ouest puis sud-est
BOUNDS = [{"lon": 2.7716, "lat": 49.4448}, {"lon": 2.8945, "lat": 49.3768}]
TARGET = re.compile(r"roberval|winston\s+churchill", re.I)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

# Push téléphone via l'app ntfy : nom de canal secret dans ntfy_topic.txt
# (ignoré par git) ou dans la variable d'environnement NTFY_TOPIC.
NTFY_TOPIC = os.environ.get("NTFY_TOPIC") or (
    TOPIC_FILE.read_text().strip() if TOPIC_FILE.exists() else "")


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n"
    with LOG.open("a") as f:
        f.write(line)
    lines = LOG.read_text().splitlines(keepends=True)
    if len(lines) > 2000:
        LOG.write_text("".join(lines[-1000:]))


def http(url, data=None):
    headers = {"User-Agent": UA}
    if data is not None:
        data = json.dumps(data).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def tool_id():
    """L'id de l'outil change selon l'année ; on le relit sur la page d'accueil."""
    try:
        m = re.search(r"/tools/(\d+)/search", http(BASE + "/"))
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return 48


def search(tid):
    body = {
        "idTool": tid, "need_aggregation": False, "page": 1, "pageSize": 100,
        "sector": None, "occupationModes": [], "location": BOUNDS,
        "residence": None, "precision": 6, "equipment": [],
        "price": {"max": 10000000}, "area": {"min": 0},
        "toolMechanism": "residual",
    }
    return json.loads(http(f"{BASE}/api/fr/search/{tid}", body))["results"]["items"]


def notify(title, text, strong=False, url=None):
    t = title.replace('"', "'")
    s = text.replace('"', "'")
    subprocess.run(["osascript", "-e",
                    f'display notification "{s}" with title "{t}" sound name "Glass"'], check=False)
    if strong:
        subprocess.run(["say", "-v", "Thomas", "Chambre Roberval disponible au Crous"], check=False)
        if url:
            subprocess.run(["open", url], check=False)
    phone(title, text, strong, url)


def phone(title, text, strong=False, url=None):
    """Push sur le téléphone via ntfy (format JSON pour garder les accents)."""
    if not NTFY_TOPIC:
        return
    msg = {"topic": NTFY_TOPIC, "title": title, "message": text,
           "priority": 5 if strong else 3,
           "tags": ["rotating_light"] if strong else ["house"]}
    if url:
        msg["click"] = url
    try:
        http("https://ntfy.sh/", msg)
    except Exception as e:
        log(f"ntfy KO: {e}")


def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {"seen": [], "fails": 0}
    seen = set(state["seen"])
    first_run = not STATE.exists()

    try:
        tid = tool_id()
        items = search(tid)
    except Exception as e:
        state["fails"] = state.get("fails", 0) + 1
        log(f"erreur ({state['fails']}): {e}")
        if state["fails"] == 15:  # ~30 min d'échecs d'affilée
            notify("Bot Crous", "Le site ne répond plus depuis 30 min, vérifie à la main.")
        STATE.write_text(json.dumps(state))
        return 1
    state["fails"] = 0

    current = {}
    for it in items:
        res = it.get("residence", {})
        name = f"{res.get('label', '?')} {res.get('address', '')}"
        current[str(it["id"])] = (name, it.get("label", ""), tid)

    roberval = {k: v for k, v in current.items() if TARGET.search(v[0])}
    new = {k: v for k, v in current.items() if k not in seen}

    for k, (name, typ, tid) in new.items():
        url = f"{BASE}/tools/{tid}/accommodations/{k}"
        if k in roberval:
            notify("ROBERVAL DISPO !", f"{typ} - {name}", strong=True, url=url)
        elif not first_run:
            notify("Nouveau logement Crous Compiègne", f"{typ} - {name}", url=url)

    log(f"tool={tid} {len(current)} logement(s), {len(roberval)} Roberval, {len(new)} nouveau(x)"
        + (" : " + " ; ".join(f"{v[1]} {v[0][:45]}" for v in new.values()) if new else ""))

    # On oublie les logements retirés : s'ils reviennent, on re-alerte.
    state["seen"] = sorted(current)
    STATE.write_text(json.dumps(state))
    return 0


if __name__ == "__main__":
    if "--test-phone" in sys.argv:
        phone("ROBERVAL DISPO ! (test)", "Test du bot : si tu lis ça, les alertes arrivent bien.",
              strong=True, url=BASE + "/tools/48/search")
        sys.exit(0)
    if "--test-notif" in sys.argv:
        notify("ROBERVAL DISPO ! (test)", "Ceci est un test du bot", strong=True,
               url=BASE + "/tools/48/search")
        sys.exit(0)
    sys.exit(main())
