from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Valorile sunt cele din BOCP (Comenzi → eCommerce → Status intern; Vânzări → Bonuri de vânzare → Status).
ETAPE = [
    ("nepreluata", "Nepreluată"),
    ("in_procesare", "În procesare"),
    ("confirmare_plata", "Confirmare plată"),
    ("asteptare_client", "Așteptare răspuns client"),
    ("produse_lipsa", "Produse lipsă"),
    ("productie", "Producție"),
    ("pregatita", "Pregătită pentru livrare"),
    ("predat_curier", "Predat curierului"),
    ("ridicare", "Ridicare din depozit"),
    ("livrata", "Livrată"),
    ("finalizata", "Finalizată"),
    ("returnata", "Returnată"),
    ("anulata", "Anulată"),
]

SURSE = [
    ("manual", "Manual / telefon"),
    ("ambalajecurierat", "ambalajecurierat.ro"),
    ("rogri_ro", "rogri.ro"),
    ("emag", "eMag"),
    ("portal", "Portal B2B"),
]

METODE_PLATA = [
    ("card_online", "Card online"),
    ("ramburs", "Ramburs (C.C.)"),
    ("op", "Ordin de plată"),
    ("op_termen", "OP la termen"),
    ("numerar", "Numerar / chitanță"),
]


class SaleOrder(models.Model):
    _inherit = "sale.order"

    rogri_sursa = fields.Selection(SURSE, string="Sursă", default="manual", required=True, index=True, tracking=True)
    rogri_etapa = fields.Selection(ETAPE, string="Etapă", default="nepreluata", required=True, index=True,
                                   tracking=True, group_expand=True, copy=False)
    rogri_metoda_plata = fields.Selection(METODE_PLATA, string="Metodă plată", tracking=True)
    rogri_ridicare_personala = fields.Boolean(string="Ridicare personală", tracking=True)
    rogri_awb = fields.Char(string="AWB", copy=False, tracking=True)
    rogri_ref_externa = fields.Char(string="Referință externă", copy=False,
                                    help="Numărul comenzii în magazin / eMag")
    rogri_profit_pct = fields.Float(string="Profit %", compute="_compute_rogri_profit_pct", digits=(16, 1))
    rogri_lipsa_stoc = fields.Boolean(string="Lipsă stoc", compute="_compute_rogri_lipsa_stoc",
                                      help="Cel puțin un produs nu are stoc disponibil pentru cantitatea comandată")

    @api.depends("margin", "amount_untaxed")
    def _compute_rogri_profit_pct(self):
        for so in self:
            so.rogri_profit_pct = (so.margin / so.amount_untaxed * 100) if so.amount_untaxed else 0.0

    @api.depends("order_line.product_uom_qty", "order_line.product_id", "state")
    def _compute_rogri_lipsa_stoc(self):
        for so in self:
            lipsa = False
            if so.state in ("draft", "sent", "sale"):
                for linie in so.order_line.filtered(lambda l: l.product_id.is_storable):
                    if linie.product_id.free_qty < linie.product_uom_qty - linie.qty_delivered:
                        lipsa = True
                        break
            so.rogri_lipsa_stoc = lipsa

    def action_rogri_emite_factura(self):
        """Butonul „Emite” din BOCP: confirmă (dacă e ofertă), facturează ce e de facturat și validează factura."""
        facturi = self.env["account.move"]
        for so in self:
            if so.state in ("draft", "sent"):
                so.action_confirm()
            if so.invoice_status != "to invoice":
                raise UserError(_("Comanda %s nu are nimic de facturat (verifică livrarea sau facturile existente).",
                                  so.name))
            factura = so._create_invoices()
            factura.action_post()
            facturi |= factura
        if len(facturi) == 1:
            return {"type": "ir.actions.act_window", "res_model": "account.move", "res_id": facturi.id,
                    "view_mode": "form", "target": "current"}
        return {"type": "ir.actions.act_window", "res_model": "account.move", "name": _("Facturi emise"),
                "domain": [("id", "in", facturi.ids)], "view_mode": "list,form"}

    def action_rogri_awb(self):
        """Butonul „AWB” din BOCP. Legătura cu Innoship vine într-o etapă următoare."""
        raise UserError(_("Generarea AWB prin Innoship nu e încă legată. Până atunci, AWB-ul se poate scrie de mână "
                          "în câmpul „AWB” al comenzii."))
