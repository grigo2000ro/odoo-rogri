# Rulat în `odoo shell -d odoo_test` (vezi server/importa_liste_pret.sh).
# Citește /tmp/bocp_liste_pret.csv (citit din BOCP: Catalog → Liste de prețuri, 9 liste pe client) și creează în Odoo:
#   o listă de prețuri „BOCP - <nume>” pe fiecare, cu regulile pe produs, și o alocă clienților (ref BOCP-<id>).
# Reguli BOCP → Odoo:
#   Adaos %   → formulă pe COST: preț = cost × (1 + adaos/100)   (price_discount = −adaos, baza = cost)
#   Preț fără TVA → preț fix
# Se poate rula de mai multe ori: regulile listei se șterg și se refac.
import csv
from collections import defaultdict

FISIER = "/tmp/bocp_liste_pret.csv"
PL = env["product.pricelist"]
Item = env["product.pricelist.item"]
Prod = env["product.product"]
Partner = env["res.partner"]
ron = env.ref("base.RON")

def num(s):
    try:
        return float(str(s).replace(",", "."))
    except (TypeError, ValueError):
        return None

liste = defaultdict(list)
for r in csv.DictReader(open(FISIER, encoding="utf-8-sig")):
    liste[r["lista"]].append(r)

lipsa, sumar = [], []
for nume, randuri in liste.items():
    pl = PL.search([("name", "=", f"BOCP - {nume}")], limit=1) or PL.create({"name": f"BOCP - {nume}", "currency_id": ron.id})
    pl.item_ids.unlink()
    n_adaos = n_fix = 0
    for r in randuri:
        p = Prod.search([("default_code", "=", r["cod_produs"])], limit=1)
        if not p:
            lipsa.append(f"{nume}: {r['cod_produs']} {r['denumire'][:40]}")
            continue
        adaos, fix = num(r["adaos_pct"]), num(r["pret_fara_tva"])
        v = {"pricelist_id": pl.id, "applied_on": "0_product_variant", "product_id": p.id,
             "product_tmpl_id": p.product_tmpl_id.id}
        if fix is not None:
            v.update(compute_price="fixed", fixed_price=fix)
            n_fix += 1
        elif adaos is not None:
            v.update(compute_price="formula", base="standard_price", price_discount=-adaos)
            n_adaos += 1
        else:
            lipsa.append(f"{nume}: {r['cod_produs']} fără regulă")
            continue
        Item.create(v)
    clienti = [c for c in (randuri[0]["clienti_id_bocp"] or "").split(";") if c]
    alocati = 0
    for cid in clienti:
        partener = Partner.search([("ref", "=", f"BOCP-{cid}")], limit=1)
        if partener:
            partener.property_product_pricelist = pl
            alocati += 1
        else:
            lipsa.append(f"{nume}: clientul BOCP-{cid} nu e în Odoo")
    sumar.append(f"{nume}: adaos {n_adaos}, fix {n_fix}, clienti {alocati}/{len(clienti)}")
env.cr.commit()
for s in sumar:
    print("LISTA", s)
for x in lipsa[:30]:
    print("LIPSA", x)
print("IMPORT gata: liste", len(liste), "| reguli", Item.search_count([("pricelist_id.name", "=like", "BOCP - %")]), "| lipsuri", len(lipsa))
