"""Construiește lista de parteneri (clienți + furnizori) pentru Odoo din exportul de contacte BOCP. Rulează local.

Intrare: date/export_contacte-2026-11-12*.xlsx (3 tranșe, 70.887 contacte)
Ieșire:  date/odoo_parteneri.csv + date/odoo_parteneri_raport.txt

Reguli:
  - un rând pe ID Contact BOCP; în Odoo referința internă = „BOCP-<ID>” (după ea se recunoaște la reimport);
  - firmă = are CUI (nu CNP de 13 cifre) sau BOCP o marchează „Companie”;
  - CUI-ul se păstrează exact cum e în BOCP (cu sau fără RO); CNP-urile NU se importă;
  - telefon = Telefon1; Telefon2 (dacă diferă) intră în note, pentru că Odoo 19 nu mai are câmpul mobil;
  - adresa = cea de sediu; dacă cea de corespondență diferă, devine adresă de livrare separată;
  - nume lipsă → e-mailul sau „Contact BOCP <ID>” (marcat în raport).
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")
D = Path(__file__).resolve().parent.parent / "date"

d = pd.concat([pd.read_excel(f, dtype=str) for f in sorted(D.glob("export_contacte-2026-11-12*.xlsx"))],
              ignore_index=True).fillna("")
d = d.apply(lambda c: c.str.strip())
d = d.drop_duplicates("ID Contact")

def fara_diacritice(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)).upper().strip()

cui = d["CUI CNP"].str.replace(r"\s+", "", regex=True).str.upper().str.replace(r"^CUI:?", "", regex=True)
e_cnp = cui.str.fullmatch(r"\d{13}")
# CUI conform: românesc (RO opțional + 2–10 cifre) sau cod TVA străin (2 litere + 6–12 caractere alfanumerice).
# Restul (ex. „-”, „****”, mai multe coduri, nr. J…) NU intră la CUI, ci în note — Odoo le-ar respinge.
cui_conform = cui.str.fullmatch(r"(RO)?\d{2,10}") | (cui.str.fullmatch(r"(?!RO)[A-Z]{2}[0-9A-Z]{6,12}") & cui.str.contains(r"\d"))
cui_neconform = d["CUI CNP"].where(cui.ne("") & ~e_cnp & ~cui_conform, "")
cui = cui.where(cui_conform, "")
p = pd.DataFrame({
    "ref": "BOCP-" + d["ID Contact"],
    "nume": d["Denumire"],
    "firma": cui.ne("") | cui_neconform.ne("") | d["Companie"].ne("0"),
    "cui": cui,
    "cui_neconform": cui_neconform,
    "nrc": d["NR Inregistrare"],
    "telefon": d["Telefon1"],
    "telefon2": d["Telefon2"].where(d["Telefon2"].ne(d["Telefon1"]), ""),
    "email": d["Email"].str.lower(),
    "website": d["Website"],
    "strada": d["Adresă1 Sediu"],
    "oras": d["Oraș Sediu"],
    "cod_postal": d["Cod Poștal Sediu"],
    "judet": d["Județ Sediu"].map(fara_diacritice),
    "tara": d["Țara Sediu"],
    "client": d["Este client:"].eq("1"),
    "furnizor": d["Este furnizor:"].eq("1"),
    "termen_zile": pd.to_numeric(d["Termen de plata"], errors="coerce").fillna(0).astype(int),
    "reprezentant": d["Reprezentant"],
})
fara_nume = p["nume"].eq("")
p.loc[fara_nume, "nume"] = p.loc[fara_nume, "email"]
p.loc[p["nume"].eq(""), "nume"] = "Contact " + p["ref"]

# adresă de livrare separată când corespondența diferă de sediu
cor = d[["Adresă1 Coresp.", "Oraș Coresp.", "Cod Poștal Coresp.", "Județ Coresp.", "Țara Coresp."]]
sed = d[["Adresă1 Sediu", "Oraș Sediu", "Cod Poștal Sediu", "Județ Sediu", "Țara Sediu"]]
difera = cor["Adresă1 Coresp."].ne("") & (cor.values != sed.values).any(axis=1)
p["livr_strada"] = cor["Adresă1 Coresp."].where(difera, "")
p["livr_oras"] = cor["Oraș Coresp."].where(difera, "")
p["livr_cod_postal"] = cor["Cod Poștal Coresp."].where(difera, "")
p["livr_judet"] = cor["Județ Coresp."].map(fara_diacritice).where(difera, "")
p["livr_tara"] = cor["Țara Coresp."].where(difera, "")

raport = [
    f"Contacte: {len(p)} (clienți {p.client.sum()}, furnizori {p.furnizor.sum()}, nici una {(~p.client & ~p.furnizor).sum()})",
    f"Firme: {p.firma.sum()}, persoane fizice: {(~p.firma).sum()}",
    f"Cu CUI: {p.cui.ne('').sum()} (din care cu RO: {p.cui.str.startswith('RO').sum()}); CNP-uri neimportate: {int(e_cnp.sum())}",
    f"CUI neconform (pus în note, nu la CUI): {p.cui_neconform.ne('').sum()}",
    f"CUI folosit la mai multe contacte: {int(p.cui[p.cui.ne('')].duplicated(keep=False).sum())} contacte",
    f"Fără nume în BOCP: {int(fara_nume.sum())} (au primit e-mailul sau „Contact BOCP-<ID>”)",
    f"Cu adresă de livrare separată: {int(difera.sum())}",
    f"Cu termen de plată > 0: {(p.termen_zile > 0).sum()}",
    f"Fără județ: {p.judet.eq('').sum()}",
]
p.to_csv(D / "odoo_parteneri.csv", index=False, encoding="utf-8")
(D / "odoo_parteneri_raport.txt").write_text("\n".join(raport), encoding="utf-8")
print("\n".join(raport))
print("Județe distincte:", p.judet.nunique())
