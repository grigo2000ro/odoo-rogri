"""Construiește lista de produse pentru Odoo din exporturile BOCP (rulează local, pe calculatorul lui Grig).

Intrări (în date/, nu intră în git):
  bocp_catalog_produse_2026-11-12.csv          — catalogul (cod, nume, stoc global, furnizor, categorie)
  bocp_jurnal_miscari_2026-01_2026-11.csv      — mișcările ian–nov 2026 (NIR, bonuri vânzare...)
Ieșire:
  date/odoo_produse.csv   — un rând pe produs: cod, nume, categorie, furnizor, cost, preț vânzare fără TVA, stoc
  date/odoo_produse_raport.txt — ce s-a ales și ce probleme sunt (stoc negativ, fără preț etc.)

Reguli (nu se inventează cifre):
  cost = costul unitar din ultimul NIR din 2026 (valoare achiziție / cantitate intrată);
         dacă nu există NIR → costul unitar din ultimele ieșiri (valoare achiziție / cantitate ieșită); altfel gol.
  preț vânzare = mediana prețului cu TVA din bonurile de vânzare din ultimele 90 de zile ale perioadei,
         împărțită la (1 + cota TVA); dacă nu există vânzări → gol.
  stoc = „Stoc Global” din catalog; stocul negativ NU se importă (rămâne 0) și apare în raport.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
D = Path(__file__).resolve().parent.parent / "date"
COTA_TVA = 0.21  # cota standard din 08.2025 (jurnalul BOCP nu are TVA completat la NIR, deci nu se poate verifica de aici)

cat = pd.read_csv(D / "bocp_catalog_produse_2026-11-12.csv", dtype=str, encoding="utf-8-sig").fillna("")
j = pd.read_csv(D / "bocp_jurnal_miscari_2026-01_2026-11.csv", dtype=str, encoding="utf-8-sig")
j = j[(j["Cod produs"] != "Toate") & j["Produs"].notna()].copy()
for c in ["Intrare", "Iesire", "Valoare achizitie", "TVA achizitie", "P.V. cu TVA"]:
    j[c] = pd.to_numeric(j[c], errors="coerce")
j["data"] = pd.to_datetime(j["Nr./Data"].str.extract(r"(\d{4}-\d{2}-\d{2})")[0], errors="coerce")

raport: list[str] = []

# cota TVA reală la NIR (control)
nir = j[j["Document"].str.startswith("NIR") & (j["Valoare achizitie"] > 0)].copy()
cote = (nir["TVA achizitie"] / nir["Valoare achizitie"]).round(2).value_counts().head(4)
raport.append(f"Cote TVA întâlnite la NIR (pondere): {cote.to_dict()}")

# cost din ultimul NIR
nir = nir[nir["Intrare"] > 0].sort_values("data")
nir["cost_u"] = nir["Valoare achizitie"] / nir["Intrare"]
cost_nir = nir.groupby("Cod produs")["cost_u"].last()
# rezervă: cost din ieșiri (ultimele 90 de zile)
ies = j[(j["Iesire"] > 0) & (j["Valoare achizitie"] > 0)].copy()
ies["cost_u"] = ies["Valoare achizitie"] / ies["Iesire"]
cost_ies = ies.sort_values("data").groupby("Cod produs")["cost_u"].last()

# preț vânzare: mediana ultimelor 90 de zile
bv = j[j["Document"].eq("Bon vânzare") & (j["P.V. cu TVA"] > 0)]
prag = bv["data"].max() - pd.Timedelta(days=90)
pret = (bv[bv["data"] >= prag].groupby("Cod produs")["P.V. cu TVA"].median() / (1 + COTA_TVA))

p = cat.copy()
p["stoc_global"] = pd.to_numeric(p["stoc_global"], errors="coerce").fillna(0)
p["cost"] = p["cod"].map(cost_nir)
p["sursa_cost"] = p["cost"].notna().map({True: "NIR", False: ""})
lips = p["cost"].isna()
p.loc[lips, "cost"] = p.loc[lips, "cod"].map(cost_ies)
p.loc[lips & p["cost"].notna(), "sursa_cost"] = "iesiri"
p["pret_fara_tva"] = p["cod"].map(pret)
p["stoc_import"] = p["stoc_global"].clip(lower=0)

# coduri duplicate în catalog → în Odoo codul intern trebuie să fie unic
dup = p["cod"].duplicated(keep=False) & p["cod"].ne("")
p["cod_odoo"] = p["cod"]
p.loc[dup | p["cod"].eq(""), "cod_odoo"] = p["cod"] + "-B" + p["id_bocp"]

raport += [
    f"Produse în catalog: {len(p)}",
    f"Cu cost din NIR: {(p.sursa_cost == 'NIR').sum()}, din ieșiri: {(p.sursa_cost == 'iesiri').sum()}, fără cost: {p['cost'].isna().sum()}",
    f"Cu preț de vânzare (ultimele 90 zile, de la {prag.date()}): {p['pret_fara_tva'].notna().sum()}",
    f"Stoc > 0: {(p.stoc_global > 0).sum()}, = 0: {(p.stoc_global == 0).sum()}, < 0 (NU se importă): {(p.stoc_global < 0).sum()}",
    f"Coduri duplicate/goale în catalog (primesc sufix -B<id>): {int((dup | p['cod'].eq('')).sum())}",
    "",
    "Produse cu stoc NEGATIV în BOCP (cod; nume; stoc):",
]
for _, r in p[p.stoc_global < 0].sort_values("stoc_global").iterrows():
    raport.append(f"  {r.cod}; {r.nume}; {r.stoc_global:g}")

cols = ["cod_odoo", "cod", "id_bocp", "nume", "categorie", "furnizor", "cost", "sursa_cost", "pret_fara_tva",
        "stoc_global", "stoc_import"]
p[cols].to_csv(D / "odoo_produse.csv", index=False, encoding="utf-8")
(D / "odoo_produse_raport.txt").write_text("\n".join(raport), encoding="utf-8")
print("\n".join(raport[:8]))
