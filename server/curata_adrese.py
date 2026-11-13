# Rulat în `odoo shell -d odoo_test` (decis de Grig 13.11.2026: „pe toate trei”).
# Curăță adresele moștenite din BOCP:
#   1. stradă = aceeași bucată repetată exact de n ori → rămâne o singură dată;
#   2. stradă cu repetiții amestecate → eticheta „Adresă de verificat (BOCP)” (o corectează un om);
#   3. adresă de livrare identică cu sediul (după normalizare) → ștearsă, dacă nu e folosită în comenzi/facturi
#      (altfel arhivată).
# Înainte de orice modificare scrie copia /tmp/adrese_inainte.csv (o copiază scriptul .sh în /root/backup-claude).
import csv
import re
import unicodedata

Partner = env["res.partner"].with_context(active_test=False, tracking_disable=True)


def norm(t):
    t = "".join(ch for ch in unicodedata.normalize("NFKD", t or "") if not unicodedata.combining(ch)).upper()
    return re.sub(r"[^A-Z0-9]+", "", t)


def bloc_repetat(t):
    s = norm(t)
    for L in range(6, len(s) // 2 + 1):
        if len(s) % L == 0 and s[:L] * (len(s) // L) == s:
            return L
    return None


def prima_bucata(text, L):
    """Primele L caractere alfanumerice (normalizate) din textul original, cu tot ce e între ele."""
    n = 0
    for i, ch in enumerate(text):
        if norm(ch):
            n += 1
            if n == L:
                return text[: i + 1].strip(" ,;.-\n\t")
    return text


def repetitii(t):
    s = re.sub(r"[^A-Z0-9]+", " ", "".join(ch for ch in unicodedata.normalize("NFKD", t or "")
                                           if not unicodedata.combining(ch)).upper()).strip()
    best = 1
    if len(s) < 16:
        return 1
    for L in range(8, len(s) // 2 + 1):
        for i in range(0, len(s) - L + 1, 3):
            bucata = s[i:i + L]
            c = s.count(bucata)
            if c > best and len(bucata.strip()) >= 8:
                best = c
        if best > 1 and L > 40:
            break
    return best


toate = Partner.search_read([("street", "!=", False)], ["id", "street", "city", "parent_id", "type"])
exacte, amestecate = [], []
for p in toate:
    L = bloc_repetat(p["street"])
    if L:
        exacte.append((p, L))
    elif repetitii(p["street"]) >= 2:
        amestecate.append(p)

# copie de siguranță (înainte de orice)
with open("/tmp/adrese_inainte.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "parent_id", "type", "street", "city", "categorie"])
    for p, _L in exacte:
        w.writerow([p["id"], p["parent_id"] and p["parent_id"][0], p["type"], p["street"], p["city"], "repetat_exact"])
    for p in amestecate:
        w.writerow([p["id"], p["parent_id"] and p["parent_id"][0], p["type"], p["street"], p["city"], "amestecat"])

# 1. corectura sigură
for p, L in exacte:
    Partner.browse(p["id"]).street = prima_bucata(p["street"], L)
env.cr.commit()
print("ADRESE 1. repetate exact, corectate:", len(exacte))

# 2. etichetă pentru verificare manuală
eticheta = env["res.partner.category"].search([("name", "=", "Adresă de verificat (BOCP)")], limit=1) \
    or env["res.partner.category"].create({"name": "Adresă de verificat (BOCP)", "color": 3})
Partner.browse([p["id"] for p in amestecate]).write({"category_id": [(4, eticheta.id)]})
env.cr.commit()
print("ADRESE 2. amestecate, etichetate pentru verificare:", len(amestecate))

# 3. livrări identice cu sediul (recalculat după corectura de la 1)
livrari = Partner.search([("type", "=", "delivery"), ("parent_id", "!=", False), ("street", "!=", False)])
identice = livrari.filtered(lambda d: (norm(d.street), norm(d.city)) == (norm(d.parent_id.street), norm(d.parent_id.city)))
with open("/tmp/adrese_inainte.csv", "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    for d in identice:
        w.writerow([d.id, d.parent_id.id, d.type, d.street, d.city, "livrare_identica_sediu"])
folosite = set(env["sale.order"].search([("partner_shipping_id", "in", identice.ids)]).mapped("partner_shipping_id.id")) \
    | set(env["account.move"].search([("partner_shipping_id", "in", identice.ids)]).mapped("partner_shipping_id.id"))
sterse = arhivate = 0
for d in identice:
    if d.id in folosite:
        d.active = False
        arhivate += 1
        continue
    try:
        with env.cr.savepoint():
            d.unlink()
        sterse += 1
    except Exception:
        d.active = False
        arhivate += 1
env.cr.commit()
print("ADRESE 3. livrari identice cu sediul:", len(identice), "| sterse", sterse, "| arhivate (folosite)", arhivate)
print("ADRESE verificare: repetate exact ramase", sum(1 for p in Partner.search_read([("street", "!=", False)], ["street"])
                                                     if bloc_repetat(p["street"])))
