import logging
from datetime import timedelta

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Starea comenzii în WooCommerce → etapa din rogri_comenzi
ETAPA_DIN_STARE = {
    "pending": "confirmare_plata",
    "on-hold": "confirmare_plata",
    "processing": "nepreluata",
    "completed": "finalizata",
    "cancelled": "anulata",
    "failed": "anulata",
    "refunded": "returnata",
    "arhiva-magento": "finalizata",
}
# Metoda de plată din WooCommerce → rogri_metoda_plata
METODA_PLATA = {
    "euplatesc": "card_online",
    "cod": "ramburs",
    "bacs": "op",
    "cheque": "op",
}


class RogriMagazin(models.Model):
    _name = "rogri.magazin"
    _description = "Magazin online legat de Odoo"

    name = fields.Char("Magazin", required=True)
    activ = fields.Boolean("Preluare automată", default=False,
                           help="Dacă e bifat, Odoo verifică la câteva minute comenzile noi")
    tip = fields.Selection([("woocommerce", "WooCommerce")], default="woocommerce", required=True)
    sursa = fields.Selection(selection=lambda self: self.env["sale.order"]._fields["rogri_sursa"].selection,
                             string="Sursă pe comenzi", required=True)
    url = fields.Char("Adresa magazinului", required=True, help="ex. https://test.ambalajecurierat.ro")
    cheie = fields.Char("Cheie API (consumer key)", groups="base.group_system")
    secret = fields.Char("Secret API (consumer secret)", groups="base.group_system")
    http_user = fields.Char("Utilizator parolă HTTP", groups="base.group_system",
                            help="Doar pentru site-uri de test protejate cu parolă")
    http_parola = fields.Char("Parolă HTTP", groups="base.group_system")
    ultima_sincronizare = fields.Datetime("Comenzi modificate după", help="De aici continuă preluarea automată")
    comenzi_ids = fields.One2many("sale.order", "rogri_magazin_id", string="Comenzi preluate")
    nr_comenzi = fields.Integer(compute="_compute_nr")
    jurnal_ids = fields.One2many("rogri.magazin.jurnal", "magazin_id", string="Jurnal")
    nr_probleme = fields.Integer(compute="_compute_nr")

    def _compute_nr(self):
        for m in self:
            m.nr_comenzi = len(m.comenzi_ids)
            m.nr_probleme = self.env["rogri.magazin.jurnal"].search_count(
                [("magazin_id", "=", m.id), ("tip", "=", "problema")])

    # ------------------------------------------------------------------ citire din WooCommerce
    def _cere(self, cale, params=None):
        self.ensure_one()
        m = self.sudo()
        p = dict(params or {}, consumer_key=m.cheie, consumer_secret=m.secret)
        auth = (m.http_user, m.http_parola) if m.http_user else None
        r = requests.get(m.url.rstrip("/") + "/wp-json/wc/v3/" + cale, params=p, auth=auth, timeout=60)
        if r.status_code != 200:
            raise UserError(_("Magazinul %(m)s a răspuns %(c)s la %(cale)s", m=m.name, c=r.status_code, cale=cale))
        return r.json(), r.headers

    def _comenzi(self, **params):
        """Toate comenzile care respectă filtrul (pe pagini de câte 50)."""
        pagina, rezultat = 1, []
        while True:
            date, antet = self._cere("orders", dict(params, per_page=50, page=pagina))
            rezultat += date
            if pagina >= int(antet.get("X-WP-TotalPages", 1)) or not date:
                return rezultat
            pagina += 1

    # ------------------------------------------------------------------ butoane / cron
    def action_vezi_comenzi(self):
        self.ensure_one()
        act = self.env["ir.actions.act_window"]._for_xml_id("rogri_magazine.action_rogri_magazin_comenzi")
        act["domain"] = [("rogri_magazin_id", "=", self.id)]
        return act

    def action_vezi_probleme(self):
        self.ensure_one()
        act = self.env["ir.actions.act_window"]._for_xml_id("rogri_magazine.action_rogri_magazin_jurnal")
        act["domain"] = [("magazin_id", "=", self.id)]
        act["context"] = {"search_default_probleme": 1}
        return act

    def action_test_legatura(self):
        for m in self:
            _date, antet = m._cere("orders", {"per_page": 1})
            raise UserError(_("Legătura merge: magazinul are %s comenzi.", antet.get("X-WP-Total")))

    def action_sincronizeaza(self):
        for m in self:
            m._sincronizeaza()

    def action_importa_ultimele(self, numar=50):
        """Pentru test: preia ultimele N comenzi, oricare ar fi starea lor."""
        for m in self:
            date, _antet = m._cere("orders", {"per_page": min(numar, 100), "orderby": "date", "order": "desc",
                                               "status": "any"})
            for o in reversed(date):
                m._importa_sigur(o)

    @api.model
    def _cron_sincronizeaza(self):
        for m in self.search([("activ", "=", True)]):
            try:
                m._sincronizeaza()
                self.env.cr.commit()
            except Exception as e:  # un magazin căzut nu oprește celelalte
                self.env.cr.rollback()
                _logger.exception("Preluare eșuată din %s", m.name)
                m._jurnal(False, "problema", f"Preluarea a eșuat: {e}")
                self.env.cr.commit()

    def _sincronizeaza(self):
        self.ensure_one()
        acum = fields.Datetime.now()
        dupa = self.ultima_sincronizare or (acum - timedelta(days=1))
        comenzi = self._comenzi(modified_after=fields.Datetime.to_string(dupa - timedelta(minutes=2)).replace(" ", "T"),
                                status="any", orderby="modified", order="asc")
        for o in comenzi:
            self._importa_sigur(o)
        self.ultima_sincronizare = acum
        return len(comenzi)

    # ------------------------------------------------------------------ preluarea unei comenzi
    def _jurnal(self, comanda, tip, mesaj, ref=False):
        self.env["rogri.magazin.jurnal"].create({
            "magazin_id": self.id, "comanda_id": comanda.id if comanda else False,
            "ref_externa": ref or (comanda.rogri_ref_externa if comanda else False), "tip": tip, "mesaj": mesaj})

    def _importa_sigur(self, o):
        try:
            with self.env.cr.savepoint():
                return self._importa(o)
        except Exception as e:
            _logger.exception("Comanda %s din %s nu s-a putut prelua", o.get("number"), self.name)
            self._jurnal(False, "problema", f"Nu s-a putut prelua: {e}", ref=str(o.get("number") or o.get("id")))

    def _importa(self, o):
        SO = self.env["sale.order"]
        ref = str(o.get("number") or o["id"])
        existenta = SO.search([("rogri_magazin_id", "=", self.id), ("rogri_ref_externa", "=", ref)], limit=1)
        etapa = ETAPA_DIN_STARE.get(o.get("status"), "nepreluata")
        if existenta:
            # doar urmărim starea; restul comenzii nu se rescrie (poate fi deja lucrată în Odoo)
            if existenta.state in ("draft", "sent") and existenta.rogri_etapa != etapa:
                existenta.rogri_etapa = etapa
            return existenta

        probleme = []
        client, livrare = self._client(o, probleme)
        linii = self._linii(o, probleme)
        transport = [m.get("method_id") for m in o.get("shipping_lines", [])]
        so = SO.create({
            "partner_id": client.id,
            "partner_shipping_id": livrare.id,
            "date_order": (o.get("date_created_gmt") or o.get("date_created") or "").replace("T", " ")[:19] or False,
            "rogri_magazin_id": self.id,
            "rogri_sursa": self.sursa,
            "rogri_ref_externa": ref,
            "rogri_etapa": etapa,
            "rogri_metoda_plata": METODA_PLATA.get(o.get("payment_method")),
            "rogri_ridicare_personala": "local_pickup" in transport,
            "rogri_total_magazin": float(o.get("total") or 0),
            "client_order_ref": f"{self.name} #{ref}",
            "note": (o.get("customer_note") or False),
            "order_line": linii,
        })
        # prețurile vin din magazin, nu din listele Odoo
        dif = round(so.amount_total - so.rogri_total_magazin, 2)
        if abs(dif) > 0.05:
            probleme.append(f"Total diferit: Odoo {so.amount_total:.2f} vs magazin {so.rogri_total_magazin:.2f} "
                            f"(diferență {dif:+.2f})")
        if probleme:
            for p in probleme:
                self._jurnal(so, "problema", p)
            so.message_post(body="<br/>".join(["Probleme la preluare:"] + probleme))
        else:
            self._jurnal(so, "ok", "Preluată fără probleme")
        return so

    def _client(self, o, probleme):
        Partner = self.env["res.partner"].with_context(no_vat_validation=True)
        b = o.get("billing") or {}
        meta = {m["key"]: m["value"] for m in o.get("meta_data", []) if isinstance(m, dict)}
        cui = (meta.get("_billing_cui") or "").replace(" ", "").upper()
        email = (b.get("email") or "").strip().lower()
        client = Partner.browse()
        if cui:
            cifre = cui.removeprefix("RO")
            client = Partner.search([("vat", "in", [cifre, "RO" + cifre]), ("parent_id", "=", False)], limit=1)
        if not client and email:
            client = Partner.search([("email", "=ilike", email), ("parent_id", "=", False)], limit=1)
        if not client and not (cui or email or b.get("first_name") or b.get("last_name") or b.get("company")):
            # comanda nu are deloc date de client (ex. comenzile vechi aduse din Magento) → un singur client comun
            ref_anonim = f"WEB-{self.id}-FARA-DATE"
            client = Partner.search([("ref", "=", ref_anonim)], limit=1) or Partner.create(
                {"name": f"Client fără date ({self.name})", "ref": ref_anonim, "customer_rank": 1})
            probleme.append("Comanda nu are date de client în magazin (nume, e-mail, CUI lipsesc)")
            return client, client
        if not client:
            ro = self.env.ref("base.ro")
            judet = self.env["res.country.state"].search(
                [("country_id", "=", ro.id), ("code", "=", (b.get("state") or "").upper())], limit=1)
            firma = bool(cui) or bool(b.get("company"))
            client = Partner.create({
                "name": (b.get("company") if firma and b.get("company") else
                         f"{b.get('first_name', '')} {b.get('last_name', '')}".strip()) or email or "Client magazin",
                "is_company": firma, "vat": cui or False, "email": email or False, "phone": b.get("phone") or False,
                "street": b.get("address_1") or False, "street2": b.get("address_2") or False,
                "city": b.get("city") or False, "zip": b.get("postcode") or False,
                "country_id": ro.id if (b.get("country") or "RO") == "RO" else False,
                "state_id": judet.id or False, "customer_rank": 1, "ref": f"WEB-{self.id}-{o.get('customer_id') or o['id']}",
            })
            probleme.append(f"Client nou creat: {client.name} (nu exista după CUI/e-mail)")
        livrare = client
        s = o.get("shipping") or {}
        if s.get("address_1") and (s.get("address_1"), s.get("city")) != (client.street, client.city):
            livrare = self.env["res.partner"].search([("parent_id", "=", client.id), ("type", "=", "delivery"),
                                                      ("street", "=", s.get("address_1")),
                                                      ("city", "=", s.get("city"))], limit=1)
            if not livrare:
                ro = self.env.ref("base.ro")
                judet = self.env["res.country.state"].search(
                    [("country_id", "=", ro.id), ("code", "=", (s.get("state") or "").upper())], limit=1)
                livrare = self.env["res.partner"].create({
                    "parent_id": client.id, "type": "delivery",
                    "name": f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or False,
                    "street": s.get("address_1"), "street2": s.get("address_2") or False, "city": s.get("city"),
                    "zip": s.get("postcode") or False, "state_id": judet.id or False, "country_id": ro.id,
                    "phone": s.get("phone") or False,
                })
        return client, livrare

    def _produs_serviciu(self, cod, nume):
        P = self.env["product.product"]
        p = P.search([("default_code", "=", cod)], limit=1)
        return p or P.create({"name": nume, "default_code": cod, "type": "service", "list_price": 0,
                              "sale_ok": True, "purchase_ok": False})

    def _linii(self, o, probleme):
        P = self.env["product.product"]
        linii = []
        for li in o.get("line_items", []):
            sku = (li.get("sku") or "").strip()
            qty = float(li.get("quantity") or 0)
            produs = P.search([("default_code", "=", sku)], limit=1) if sku else P.browse()
            if not produs or not qty:
                probleme.append(f"Produs negăsit în Odoo: cod „{sku}” – {li.get('name')} × {qty:g}")
                linii.append((0, 0, {"display_type": "line_note",
                                     "name": f"[NEGĂSIT] {sku} {li.get('name')} × {qty:g} = {li.get('total')} lei"}))
                continue
            subtotal, total = float(li.get("subtotal") or 0), float(li.get("total") or 0)
            reducere = round((1 - total / subtotal) * 100, 4) if subtotal and total < subtotal else 0.0
            linii.append((0, 0, {"product_id": produs.id, "product_uom_qty": qty,
                                 "price_unit": round(subtotal / qty, 4), "discount": reducere}))
        for t in o.get("shipping_lines", []):
            if float(t.get("total") or 0):
                serv = self._produs_serviciu("TRANSPORT-WEB", "Transport (magazin online)")
                linii.append((0, 0, {"product_id": serv.id, "product_uom_qty": 1, "name": t.get("method_title"),
                                     "price_unit": float(t["total"])}))
        for f in o.get("fee_lines", []):
            if float(f.get("total") or 0):
                serv = self._produs_serviciu("TAXA-WEB", "Taxă / reducere magazin online")
                linii.append((0, 0, {"product_id": serv.id, "product_uom_qty": 1, "name": f.get("name"),
                                     "price_unit": float(f["total"])}))
        return linii


class RogriMagazinJurnal(models.Model):
    _name = "rogri.magazin.jurnal"
    _description = "Jurnal preluare comenzi din magazine"
    _order = "id desc"

    magazin_id = fields.Many2one("rogri.magazin", required=True, ondelete="cascade", index=True)
    comanda_id = fields.Many2one("sale.order", string="Comandă Odoo", ondelete="set null")
    ref_externa = fields.Char("Nr. în magazin")
    tip = fields.Selection([("ok", "OK"), ("problema", "Problemă")], required=True, index=True)
    mesaj = fields.Char("Mesaj")
