# Rulat în `odoo shell -d odoo_test`. Test cap-coadă pe baza de TEST: comandă → livrare → factură → XML e-Factura.
# Nimic nu pleacă în afară: coada de e-mail e oprită, iar XML-ul e-Factura doar se generează (nu se trimite la ANAF).
import base64

# 0. siguranță: baza conține clienți reali → coada de e-mailuri oprită
for c in env["ir.cron"].search([("name", "in", ["E-mail: Email Queue Manager", "Mail: Email Queue Manager"])]):
    c.active = False
print("TEST coada e-mail oprita:", not env["ir.cron"].search([("name", "ilike", "Email Queue Manager"), ("active", "=", True)]))
# fără SMS/e-mail de confirmare la livrare (altfel Odoo întreabă dacă trimite SMS clientului)
env.company.sudo().write({"has_received_warning_stock_sms": True, "stock_text_confirmation": False})

ro = env.ref("base.ro")
client = env["res.partner"].search([
    ("ref", "=like", "BOCP-%"), ("is_company", "=", True), ("vat", "=like", "RO%"), ("customer_rank", ">", 0),
    ("country_id", "=", ro.id), ("state_id", "!=", False), ("street", "!=", False), ("city", "!=", False),
], limit=1, order="id")
P = env["product.product"]
p1 = P.search([("default_code", "=", "1409")])  # Cutie 200x150x90 mm
p2 = P.search([("default_code", "=", "3020")])  # Banda adeziva solvent alba
stoc_inainte = {p.default_code: p.qty_available for p in p1 | p2}
print("TEST client:", client.ref, "| judet", client.state_id.name, "| produse:", p1.display_name, "/", p2.display_name)
print("TEST stoc inainte:", stoc_inainte)

# transportator: modulul e-Transport (l10n_ro_edi_stock) nu validează livrarea fără el
curier = env["delivery.carrier"].search([("name", "=", "Curier (test - Innoship)")], limit=1)
if not curier:
    serv = env["product.product"].create({"name": "Transport curier (test)", "type": "service", "list_price": 0})
    curier = env["delivery.carrier"].create({"name": "Curier (test - Innoship)", "delivery_type": "fixed",
                                             "fixed_price": 0, "product_id": serv.id})
if not curier.l10n_ro_edi_stock_partner_id:
    # firma transportatoare (apare în e-Transport); în producție = curierul real (Fan, Sameday...) cu CUI
    curier.l10n_ro_edi_stock_partner_id = env["res.partner"].create(
        {"name": "Transportator TEST (de inlocuit)", "is_company": True, "country_id": env.ref("base.ro").id})

# 1. comanda
so = env["sale.order"].create({
    "partner_id": client.id,
    "carrier_id": curier.id,
    "client_order_ref": "TEST pilot Odoo",
    "order_line": [
        (0, 0, {"product_id": p1.id, "product_uom_qty": 100}),
        (0, 0, {"product_id": p2.id, "product_uom_qty": 10}),
    ],
})
so.action_confirm()
print("TEST comanda:", so.name, so.state, "| total fara TVA", so.amount_untaxed, "| TVA", so.amount_tax, "| total", so.amount_total)

# 2. livrarea
pick = so.picking_ids
pick.carrier_id = curier
for m in pick.move_ids:
    m.quantity = m.product_uom_qty
pick.move_ids.picked = True  # Odoo 19: fără „pregătit”, validarea nu mută stocul
pick.with_context(skip_sms=True).button_validate()
print("TEST livrare:", pick.name, pick.state, "| stoc dupa:", {p.default_code: p.qty_available for p in p1 | p2})

# 3. factura
inv = so._create_invoices()
inv.action_post()
print("TEST factura:", inv.name, inv.state, "| total", inv.amount_total, "| scadenta", inv.invoice_date_due)
for l in inv.line_ids:
    print("TEST  nota:", l.account_id.code, l.account_id.name[:35], "D", l.debit, "C", l.credit)
# descărcarea de gestiune (607/371) — dacă există valorizare automată
for am in env["account.move"].search([("stock_move_id", "in", pick.move_ids.ids)]) if "stock_move_id" in env["account.move"]._fields else []:
    for l in am.line_ids:
        print("TEST  gestiune:", l.account_id.code, "D", l.debit, "C", l.credit)

# 4. XML e-Factura (CIUS-RO), doar generat
try:
    builder = env["account.edi.xml.ubl_ro"]
    xml, erori = builder._export_invoice(inv)
    print("TEST XML e-Factura:", len(xml or b""), "octeti | erori:", erori or "niciuna")
    if xml:
        env["ir.attachment"].create({"name": f"{inv.name.replace('/', '_')}_efactura_TEST.xml", "raw": xml,
                                     "res_model": "account.move", "res_id": inv.id})
except Exception as e:
    print("TEST XML e-Factura EROARE:", type(e).__name__, str(e)[:400])

# 5. încasarea prin bancă
banca = env["account.journal"].search([("type", "=", "bank")], limit=1)
env["account.payment.register"].with_context(active_model="account.move", active_ids=inv.ids).create(
    {"journal_id": banca.id}).action_create_payments()
print("TEST incasare:", inv.payment_state, "| rest de incasat", inv.amount_residual)
env.cr.commit()
print("TEST gata")
