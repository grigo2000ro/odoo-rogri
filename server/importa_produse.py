# Rulat în `odoo shell -d odoo_test` (vezi server/importa_produse.sh).
# Citește /tmp/odoo_produse.csv (făcut de server/pregateste_produse.py) și creează/actualizează:
#   categorii, furnizori, produse stocabile (cost, preț vânzare, furnizor) și stocul inițial în WH/Stoc.
# Se poate rula de mai multe ori: produsele se caută după codul intern; stocul se aduce la valoarea din fișier.
import csv

FISIER = "/tmp/odoo_produse.csv"
Categ = env["product.category"]
Partner = env["res.partner"]
Tmpl = env["product.template"]
Quant = env["stock.quant"]
loc = env["stock.warehouse"].search([("company_id", "=", env.company.id)], limit=1).lot_stock_id
radacina = env.ref("product.product_category_all", raise_if_not_found=False) or Categ  # în Odoo 19 poate lipsi

def num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None

categorii, furnizori = {}, {}
def categorie(nume):
    nume = (nume or "").strip() or "Necategorizat"
    if nume not in categorii:
        c = Categ.search([("name", "=", nume), ("parent_id", "=", radacina.id)], limit=1)
        categorii[nume] = c or Categ.create({"name": nume, "parent_id": radacina.id})
    return categorii[nume]

def furnizor(nume):
    nume = (nume or "").strip()
    if not nume or nume == "0":
        return None
    if nume not in furnizori:
        f = Partner.search([("name", "=", nume), ("is_company", "=", True)], limit=1)
        furnizori[nume] = f or Partner.create({"name": nume, "is_company": True, "supplier_rank": 1})
    return furnizori[nume]

randuri = list(csv.DictReader(open(FISIER, encoding="utf-8")))
noi = actualizate = cu_stoc = 0
for i, r in enumerate(randuri, 1):
    vals = {
        "name": r["nume"] or r["cod"],
        "default_code": r["cod_odoo"],
        "type": "consu",
        "is_storable": True,
        "categ_id": categorie(r["categorie"]).id,
        "sale_ok": True,
        "purchase_ok": True,
    }
    pret, cost = num(r["pret_fara_tva"]), num(r["cost"])
    # fără vânzări în ultimele 90 de zile → preț 0 (Odoo ar pune implicit 1 leu, adică o cifră inventată)
    vals["list_price"] = round(pret, 4) if pret is not None else 0.0
    t = Tmpl.search([("default_code", "=", r["cod_odoo"])], limit=1)
    if t:
        t.write(vals)
        actualizate += 1
    else:
        t = Tmpl.create(vals)
        noi += 1
    p = t.product_variant_id
    if cost is not None:
        p.standard_price = round(cost, 4)
    f = furnizor(r["furnizor"])
    if f and not t.seller_ids.filtered(lambda s: s.partner_id == f):
        env["product.supplierinfo"].create({"partner_id": f.id, "product_tmpl_id": t.id, "price": round(cost or 0, 4)})
    q = num(r["stoc_import"]) or 0.0
    if q > 0 or p.qty_available:
        Quant.with_context(inventory_mode=True).create({
            "product_id": p.id, "location_id": loc.id, "inventory_quantity": q,
        }).action_apply_inventory()
        cu_stoc += q > 0
    if i % 200 == 0:
        env.cr.commit()
        print("PROGRES", i)
env.cr.commit()
print("IMPORT gata: noi", noi, "actualizate", actualizate, "cu stoc", cu_stoc,
      "| total produse", Tmpl.search_count([]), "| categorii", len(categorii), "| furnizori", len(furnizori))
