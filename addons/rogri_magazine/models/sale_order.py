from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    rogri_magazin_id = fields.Many2one("rogri.magazin", string="Magazin online", index=True, copy=False,
                                       readonly=True)
    rogri_total_magazin = fields.Monetary(string="Total în magazin", copy=False, readonly=True,
                                          help="Totalul comenzii așa cum apare în magazin (pentru comparație)")

    _rogri_ref_magazin_unica = models.Constraint(
        "unique(rogri_magazin_id, rogri_ref_externa)",
        "Comanda din magazin a fost deja preluată.",
    )
