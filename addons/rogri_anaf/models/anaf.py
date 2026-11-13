"""Interogarea serviciului public ANAF (fără cont, fără cheie)."""
import logging
import re
import time
from datetime import date

import requests

_logger = logging.getLogger(__name__)

ANAF_URL = "https://webservicesp.anaf.ro/api/PlatitorTvaRest/v9/tva"
LOT_MAXIM = 100          # limita ANAF: 100 CUI pe cerere
PAUZA_SECUNDE = 1.1      # limita ANAF: 1 cerere pe secundă
_ultima_cerere = [0.0]


def cui_curat(text):
    """„RO 12345678” / „ro12345678” / „12345678” → „12345678”; altceva → ''."""
    t = re.sub(r"\s+", "", str(text or "")).upper().removeprefix("RO")
    return t if re.fullmatch(r"\d{2,10}", t) else ""


def cui_valid(cui):
    """Cifra de control a CUI-ului românesc."""
    if not re.fullmatch(r"\d{2,10}", cui or ""):
        return False
    cheie = "753217532"
    corp, control = cui[:-1].rjust(9, "0"), int(cui[-1])
    s = sum(int(a) * int(b) for a, b in zip(corp, cheie)) * 10 % 11
    return (0 if s == 10 else s) == control


def interogheaza(cuiuri):
    """Întoarce {cui: date | None(negăsit)} pentru lista dată. Ridică excepție dacă ANAF nu răspunde."""
    rezultat = {}
    lista = sorted({c for c in (cui_curat(x) for x in cuiuri) if c})
    for i in range(0, len(lista), LOT_MAXIM):
        lot = lista[i:i + LOT_MAXIM]
        astept = PAUZA_SECUNDE - (time.monotonic() - _ultima_cerere[0])
        if astept > 0:
            time.sleep(astept)
        corp = [{"cui": int(c), "data": date.today().isoformat()} for c in lot]
        r = requests.post(ANAF_URL, json=corp, timeout=30)
        _ultima_cerere[0] = time.monotonic()
        # ANAF: 200 când găsește, 404 cu „notFound” când nu găsește nimic din lot
        if r.status_code not in (200, 404):
            raise RuntimeError(f"ANAF a răspuns {r.status_code}")
        js = r.json()
        for f in js.get("found") or []:
            g = f.get("date_generale") or {}
            rezultat[str(g.get("cui"))] = _date_firma(f)
        for c in js.get("notFound") or js.get("notfound") or []:
            rezultat[str(c)] = None
    return rezultat


def _date_firma(f):
    g = f.get("date_generale") or {}
    s = f.get("adresa_sediu_social") or {}
    strada = (s.get("sdenumire_Strada") or "").strip()
    if s.get("snumar_Strada"):
        strada += f" nr. {s['snumar_Strada']}"
    if s.get("sdetalii_Adresa"):
        strada = f"{strada}, {s['sdetalii_Adresa']}".strip(", ")
    inactiv = f.get("stare_inactiv") or {}
    return {
        "cui": str(g.get("cui")),
        "denumire": (g.get("denumire") or "").strip(),
        "nr_reg_com": (g.get("nrRegCom") or "").strip(),
        "telefon": (g.get("telefon") or "").strip(),
        "platitor_tva": bool((f.get("inregistrare_scop_Tva") or {}).get("scpTVA")),
        "tva_incasare": bool((f.get("inregistrare_RTVAI") or {}).get("statusTvaIncasare")),
        "split_tva": bool((f.get("inregistrare_SplitTVA") or {}).get("statusSplitTVA")),
        "efactura": bool(g.get("statusRO_e_Factura")),
        "radiat": bool(inactiv.get("dataRadiere")),
        "inactiv": bool(inactiv.get("statusInactivi")),
        "stare_text": (g.get("stare_inregistrare") or "").strip(),
        "strada": strada or (g.get("adresa") or "").strip(),
        "localitate": (s.get("sdenumire_Localitate") or "").strip(),
        "judet_cod": (s.get("scod_JudetAuto") or "").strip(),
        "judet": (s.get("sdenumire_Judet") or "").strip(),
        "cod_postal": (s.get("scod_Postal") or "").strip(),
    }
