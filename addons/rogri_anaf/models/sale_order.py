from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    rogri_cui_client = fields.Char("CUI client", store=False,
                                   help="Scrie CUI-ul: clientul se caută în Odoo, iar dacă nu există se creează din ANAF")
    rogri_client_anaf_stare = fields.Selection(related="partner_id.commercial_partner_id.rogri_anaf_stare",
                                               string="Stare ANAF client")

    @api.onchange("rogri_cui_client")
    def _onchange_rogri_cui_client(self):
        if not self.rogri_cui_client:
            return
        try:
            self.partner_id = self.env["res.partner"].rogri_din_cui(self.rogri_cui_client)
        except UserError as e:
            return {"warning": {"title": _("CUI client"), "message": str(e)}}
        except Exception:
            return {"warning": {"title": _("CUI client"), "message": _("ANAF nu răspunde acum; alege clientul manual.")}}
        finally:
            self.rogri_cui_client = False
