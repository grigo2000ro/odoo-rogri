# Rulat în `odoo shell -d odoo_test`. Verifică listele de preț BOCP în comenzi (comenzile de test rămân ciorne).
import csv
rows = list(csv.DictReader(open("/tmp/bocp_liste_pret.csv", encoding="utf-8-sig")))
P = env["product.product"]

def comanda(lista, n=3):
    rr = [r for r in rows if r["lista"] == lista][:n]
    client = env["res.partner"].search([("ref", "=", "BOCP-" + rr[0]["clienti_id_bocp"].split(";")[0])])
    so = env["sale.order"].create({"partner_id": client.id, "client_order_ref": f"TEST lista {lista}",
        "order_line": [(0, 0, {"product_id": P.search([("default_code", "=", r["cod_produs"])]).id, "product_uom_qty": 10}) for r in rr]})
    print("TEST", lista, so.name, "| lista pe comanda:", so.pricelist_id.name)
    for l, r in zip(so.order_line, rr):
        pa, ad, fx = r["pret_achizitie"], r["adaos_pct"], r["pret_fara_tva"]
        bocp = float(fx) if fx else round(float(pa) * (1 + float(ad) / 100), 4)
        print(f"TEST  {r['cod_produs']:>5} Odoo {l.price_unit:9.4f} | BOCP {bocp:9.4f}"
              + (f" (PA BOCP {pa} +{ad}% ; cost Odoo {l.product_id.standard_price})" if not fx else " (pret fix)")
              + f" | pret lista standard {l.product_id.list_price}")
    return so

comanda("Amc"); comanda("RTC"); comanda("Campack")

# cât diferă costul din Odoo (ultimul NIR) de prețul de achiziție din BOCP, la produsele cu adaos
dif = []
for r in rows:
    if r["adaos_pct"] and not r["pret_fara_tva"]:
        p = P.search([("default_code", "=", r["cod_produs"])])
        pa = float(r["pret_achizitie"] or 0)
        if pa and p and abs(p.standard_price - pa) / pa > 0.02:
            dif.append(r["cod_produs"])
print("TEST produse cu adaos:", sum(1 for r in rows if r["adaos_pct"] and not r["pret_fara_tva"]),
      "| cost Odoo diferit de PA BOCP cu >2%:", len(dif))
env.cr.commit()
