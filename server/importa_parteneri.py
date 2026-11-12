# Rulat în `odoo shell -d odoo_test` (vezi server/importa_parteneri.sh).
# Citește /tmp/odoo_parteneri.csv (făcut de server/pregateste_parteneri.py) și creează/actualizează partenerii.
# Recunoaștere la reimport: referința internă „BOCP-<ID>”. CUI-ul nu se validează la import (vin date vechi din BOCP).
import csv
import unicodedata

FISIER = "/tmp/odoo_parteneri.csv"
Partner = env["res.partner"].with_context(no_vat_validation=True, tracking_disable=True, mail_create_nolog=True)
ro = env.ref("base.ro")

def cheie(s):
    s = "".join(ch for ch in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(ch)).upper()
    for x in ("MUNICIPIUL ", "JUD. ", "JUDETUL "):
        s = s.replace(x, "")
    return "".join(ch for ch in s if ch.isalnum())

judete = {cheie(s.name): s.id for s in env["res.country.state"].search([("country_id", "=", ro.id)])}
tari = {cheie(c.name): c.id for c in env["res.country"].with_context(lang="en_US").search([])}
tari.update({cheie(c.name): c.id for c in env["res.country"].search([])})

termene = {}
def termen(zile):
    if zile <= 0:
        return False
    if zile not in termene:
        t = env["account.payment.term"].search([("name", "=ilike", f"{zile} zile")], limit=1)
        if not t:
            t = env["account.payment.term"].create({
                "name": f"{zile} zile",
                "line_ids": [(0, 0, {"value": "percent", "value_amount": 100, "nb_days": zile})],
            })
        termene[zile] = t.id
    return termene[zile]

def adresa(strada, oras, cp, judet, tara):
    tid = tari.get(cheie(tara)) or (ro.id if tara == "" and (oras or strada) else False)
    v = {"street": strada or False, "city": oras or False, "zip": cp or False, "country_id": tid or False}
    if tid == ro.id:
        v["state_id"] = judete.get(cheie(judet), False)
    return v

existenti = {r["ref"]: r["id"] for r in Partner.search_read([("ref", "=like", "BOCP-%")], ["ref"])}
randuri = list(csv.DictReader(open(FISIER, encoding="utf-8")))
noi = actualizati = livrari = 0
lot = []

respinsi = []

def creeaza(valori):
    """Creează tot lotul; dacă Odoo respinge ceva, le ia pe rând și le sare doar pe cele respinse."""
    try:
        with env.cr.savepoint():
            return Partner.create(valori)
    except Exception:
        rez = Partner
        for v in valori:
            try:
                with env.cr.savepoint():
                    rez |= Partner.create(v)
            except Exception as e:
                respinsi.append(f"{v['ref']}: {str(e).splitlines()[0][:120]}")
        return rez

def scrie_lot(lot):
    global noi, actualizati, livrari
    de_creat = [v for ref, v, l in lot if ref not in existenti]
    create = creeaza(de_creat) if de_creat else Partner
    for p in create:
        existenti[p.ref] = p.id
    noi += len(create)
    for ref, v, l in lot:
        if ref not in existenti:
            continue  # respins la creare
        if v not in de_creat:
            try:
                with env.cr.savepoint():
                    Partner.browse(existenti[ref]).write(v)
                actualizati += 1
            except Exception as e:
                respinsi.append(f"{ref}: {str(e).splitlines()[0][:120]}")
        if l:
            parinte = existenti[ref]
            if not Partner.search_count([("parent_id", "=", parinte), ("type", "=", "delivery")]):
                Partner.create(dict(l, parent_id=parinte, type="delivery"))
                livrari += 1
    env.cr.commit()

for i, r in enumerate(randuri, 1):
    note = []
    if r["telefon2"]:
        note.append(f"Telefon 2: {r['telefon2']}")
    if r.get("cui_neconform"):
        note.append(f"CUI din BOCP (neconform): {r['cui_neconform']}")
    if r["reprezentant"]:
        note.append(f"Reprezentant: {r['reprezentant']}")
    v = {
        "name": r["nume"],
        "ref": r["ref"],
        "is_company": r["firma"] == "True",
        "vat": r["cui"] or False,
        "nrc": r["nrc"] or False,
        "phone": r["telefon"] or False,
        "email": r["email"] or False,
        "website": r["website"] or False,
        "customer_rank": 1 if r["client"] == "True" else 0,
        "supplier_rank": 1 if r["furnizor"] == "True" else 0,
        "comment": "<br/>".join(note) or False,
        **adresa(r["strada"], r["oras"], r["cod_postal"], r["judet"], r["tara"]),
    }
    tz = termen(int(r["termen_zile"] or 0))
    if tz:
        v["property_payment_term_id"] = tz
    livr = None
    if r["livr_strada"]:
        livr = adresa(r["livr_strada"], r["livr_oras"], r["livr_cod_postal"], r["livr_judet"], r["livr_tara"])
    lot.append((r["ref"], v, livr))
    if len(lot) == 500:
        scrie_lot(lot)
        lot = []
        if i % 5000 == 0:
            print("PROGRES", i)
if lot:
    scrie_lot(lot)
for x in respinsi[:30]:
    print("RESPINS", x)
print("IMPORT gata: noi", noi, "actualizati", actualizati, "adrese livrare", livrari, "respinsi", len(respinsi),
      "| parteneri BOCP", Partner.search_count([("ref", "=like", "BOCP-%")]),
      "| fara judet RO", Partner.search_count([("ref", "=like", "BOCP-%"), ("country_id", "=", ro.id), ("state_id", "=", False)]))
