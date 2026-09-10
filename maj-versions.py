#!/usr/bin/env python3
"""Resynchronise les numéros de version de la vitrine sur les vraies releases.

Ils étaient écrits à la main, donc périmés dès la publication suivante : la
page annonçait Syntax 1.1.0 quand la 2.1.0 était en ligne depuis longtemps.
Ce script lit la dernière release de chaque dépôt `<app>-Share` et réécrit la
ligne correspondante.

    python3 maj-versions.py          # montre ce qui changerait
    python3 maj-versions.py --ecrire # applique

Une app sans release, ou dont la carte ne porte pas de version, est laissée
telle quelle : toutes n'en publient pas, et inventer un numéro serait pire
que de n'en afficher aucun.
"""
import re, subprocess, sys

PAGE = "index.html"

# Le nom affiché sur la carte sert à deviner le dépôt `<nom>-Share`. GitHub
# ignore la casse, donc « Macropad » retrouve MACROPAD-Share tout seul — mais
# six apps ont été renommées côté vitrine sans que le dépôt suive. Sans cette
# table, leur carte affichait une version figée que rien ne resynchronisait,
# c'est-à-dire exactement le problème que ce script existe pour régler.
DEPOTS = {
    "DiskStats": "STATVIEWER",
    "CobaltNotch": "ULTRANOTCH",
    "Au Propre": "DICTIA",
    "VoiceStudio": "VOICE-STUDIO",
    "SurfaceCobalt": "Surface-Cobalt",
    "GambiOS": "GAMBI_OS_MAC",
}


def derniere_version(app):
    depot = DEPOTS.get(app, app)
    r = subprocess.run(
        ["gh", "release", "view", "--repo", f"gambidrissi-dev/{depot}-Share",
         "--json", "tagName", "-q", ".tagName"],
        capture_output=True, text=True)
    tag = r.stdout.strip()
    return tag.lstrip("v") if r.returncode == 0 and tag else None


def main():
    ecrire = "--ecrire" in sys.argv
    page = open(PAGE, encoding="utf-8").read()

    # Chaque carte : le nom de l'app puis, un peu plus loin, sa ligne de méta.
    motif = re.compile(
        r'(<span class="app-name">([^<]+)</span>.*?<span class="app-meta">)([^<]*)(</span>)',
        re.S)

    changements = []

    def remplacer(m):
        debut, nom, meta, fin = m.group(1), m.group(2), m.group(3), m.group(4)
        # Sans « vX.Y.Z » en tête, la carte n'affiche pas de version : on n'en
        # ajoute pas une, c'est un choix éditorial qui n'est pas le nôtre.
        if not re.match(r"v\d", meta.strip()):
            return m.group(0)
        version = derniere_version(nom)
        if version is None:
            return m.group(0)
        neuf = re.sub(r"^v[\d.]+", f"v{version}", meta.strip())
        if neuf != meta.strip():
            changements.append((nom, meta.strip().split(" ")[0], f"v{version}"))
        return debut + neuf + fin

    nouvelle = motif.sub(remplacer, page)

    if not changements:
        print("tout est à jour")
        return
    for nom, avant, apres in changements:
        print(f"  {nom:<14} {avant} → {apres}")
    if ecrire:
        open(PAGE, "w", encoding="utf-8").write(nouvelle)
        print(f"\n{len(changements)} version(s) corrigée(s) dans {PAGE}")
    else:
        print("\n(--ecrire pour appliquer)")


if __name__ == "__main__":
    main()
