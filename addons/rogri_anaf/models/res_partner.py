import logging
import unicodedata

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from . import anaf

_logger = logging.getLogger(__name__)

STARI = [
    ("activ", "Activ"),
    ("inactiv", "INACTIV fiscal"),
    ("radiat", "RADIAT"),
    ("negasit", "Negăsit la ANAF"),
    ("cui_invalid", "CUI invalid"),
]


def _cheie(text):
    t = "".join(ch for ch in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(ch)).upper()
    for x in ("MUNICIPIUL ", "JUD. ", "JUDETUL "):
        t = t.replace(x, "")
    return "".join(ch for ch in t if ch.isalnum())


def _cheie_firma(nume):
    """Denumire comparabilă: fără „SC” în față, fără punctuație, forme lungi → scurte (PFA, II, IF)."""
    k = _cheie(nume)
    for lung, scurt in (("PERSOANAFIZICAAUTORIZATA", "PFA"), ("INTREPRINDEREINDIVIDUALA", "II"),
                        ("INTREPRINDEREFAMILIALA", "IF"), ("SOCIETATEPEACTIUNI", "SA")):
        k = k.replace(lung, scurt)
    return k.removeprefix("SC")


def _localitati_anaf(text):
    """„Sat Ceraşu Com. Ceraşu” → {CERASU}; „Sector 1 Mun. Bucureşti” → {BUCURESTI, SECTOR1}; „Mun. Braşov” → {BRASOV}."""
    import re
    t = "".join(ch for ch in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(ch)).upper()
    bucati = re.split(r"\b(?:MUN|ORS|COM|SAT|ORAS|MUNICIPIUL|COMUNA)\.?\s+", t)
    return {_cheie(b) for b in bucati if _cheie(b)} | {_cheie(re.sub(r"\d.*$", "", b)) for b in bucati if _cheie(b)}


class ResPartner(models.Model):
    _inherit = "res.partner"

    rogri_anaf_stare = fields.Selection(STARI, string="Stare ANAF", copy=False, index=True)
    rogri_anaf_data = fields.Datetime("Verificat la ANAF", copy=False)
    rogri_anaf_denumire = fields.Char("Denumire la ANAF", copy=False)
    rogri_anaf_diferente = fields.Char("Diferențe față de ANAF", copy=False)
    rogri_platitor_tva = fields.Boolean("Plătitor TVA", copy=False)
    rogri_tva_incasare = fields.Boolean("TVA la încasare", copy=False)
    rogri_split_tva = fields.Boolean("Split TVA", copy=False)
    rogri_efactura = fields.Boolean("În registrul e-Factura", copy=False)

    # ------------------------------------------------------------------ aplicarea datelor
    def _rogri_judet(self, d):
        ro = self.env.ref("base.ro")
        judete = self.env["res.country.state"].search([("country_id", "=", ro.id)])
        cod = (d.get("judet_cod") or "").upper()
        j = judete.filtered(lambda s: s.code.upper() == cod)[:1]
        if not j:
            k = _cheie(d.get("judet"))
            j = judete.filtered(lambda s: _cheie(s.name) == k)[:1]
        if not j and _cheie(d.get("judet")).startswith("BUCURESTI"):
            j = judete.filtered(lambda s: _cheie(s.name) == "BUCURESTI")[:1]
        return j

    def _rogri_valori_stare(self, d):
        if d is None:
            return {"rogri_anaf_stare": "negasit", "rogri_anaf_data": fields.Datetime.now()}
        return {
            "rogri_anaf_stare": "radiat" if d["radiat"] else "inactiv" if d["inactiv"] else "activ",
            "rogri_anaf_data": fields.Datetime.now(),
            "rogri_anaf_denumire": d["denumire"],
            "rogri_platitor_tva": d["platitor_tva"],
            "rogri_tva_incasare": d["tva_incasare"],
            "rogri_split_tva": d["split_tva"],
            "rogri_efactura": d["efactura"],
        }

    def _rogri_valori_firma(self, d):
        """Datele de identificare din ANAF, pentru completare (nu se aplică pe tăcute la clienții existenți)."""
        return {
            "name": d["denumire"],
            "is_company": True,
            "vat": ("RO" if d["platitor_tva"] else "") + d["cui"],
            "nrc": d["nr_reg_com"] or False,
            "street": d["strada"] or False,
            "city": d["localitate"] or False,
            "zip": d["cod_postal"] or False,
            "state_id": self._rogri_judet(d).id or False,
            "country_id": self.env.ref("base.ro").id,
        }

    def _rogri_diferente(self, d):
        self.ensure_one()
        dif = []
        a, b = _cheie_firma(self.name), _cheie_firma(d["denumire"])
        if a != b and not (len(a) >= 25 and b.startswith(a)):  # denumirile lungi pot fi tăiate în BOCP
            dif.append("denumire")
        cui_odoo = (self.vat or "").upper().replace(" ", "")
        if cui_odoo != ("RO" if d["platitor_tva"] else "") + d["cui"]:
            dif.append("CUI cu/fără RO" if anaf.cui_curat(cui_odoo) == d["cui"] else "CUI")
        oras = _cheie(self.city).removeprefix("SECTOR").lstrip("0123456789") or _cheie(self.city)
        if d["localitate"] and oras and oras not in _localitati_anaf(d["localitate"]):
            dif.append("localitate")
        return ", ".join(dif)

    # ------------------------------------------------------------------ verificare
    def _rogri_verifica_anaf(self, completeaza=False):
        """Verifică partenerii cu CUI. completeaza=True scrie și denumirea/adresa din ANAF."""
        de_verificat = self.filtered(lambda p: p.vat and not p.parent_id)
        Partner = self.with_context(no_vat_validation=True)
        valizi = {}
        for p in de_verificat:
            c = anaf.cui_curat(p.vat)
            if not c or not anaf.cui_valid(c):
                Partner.browse(p.id).write({"rogri_anaf_stare": "cui_invalid", "rogri_anaf_data": fields.Datetime.now()})
            else:
                valizi.setdefault(c, Partner.browse())
                valizi[c] |= p
        if not valizi:
            return 0
        rez = anaf.interogheaza(list(valizi))
        for c, parteneri in valizi.items():
            d = rez.get(c)
            for p in parteneri:
                vals = p._rogri_valori_stare(d)
                if d:
                    if completeaza:
                        vals.update(p._rogri_valori_firma(d))
                        vals["rogri_anaf_diferente"] = False
                    else:
                        vals["rogri_anaf_diferente"] = p._rogri_diferente(d) or False
                Partner.browse(p.id).write(vals)
        return len(valizi)

    def action_rogri_verifica_anaf(self):
        try:
            n = self._rogri_verifica_anaf()
        except Exception as e:
            raise UserError(_("ANAF nu a răspuns: %s", e)) from e
        return self._rogri_notificare(_("%s CUI verificate la ANAF.", n))

    def action_rogri_completeaza_anaf(self):
        try:
            self._rogri_verifica_anaf(completeaza=True)
        except Exception as e:
            raise UserError(_("ANAF nu a răspuns: %s", e)) from e
        return self._rogri_notificare(_("Datele au fost completate din ANAF."))

    def _rogri_notificare(self, mesaj):
        return {"type": "ir.actions.client", "tag": "display_notification",
                "params": {"message": mesaj, "type": "success", "next": {"type": "ir.actions.act_window_close"}}}

    @api.model
    def rogri_din_cui(self, text):
        """Găsește partenerul după CUI sau îl creează din ANAF. Folosit la comenzi și la magazine."""
        c = anaf.cui_curat(text)
        if not c:
            raise UserError(_("„%s” nu este un CUI.", text))
        if not anaf.cui_valid(c):
            raise UserError(_("CUI-ul %s nu este valid (cifra de control nu se potrivește).", c))
        existent = self.search([("vat", "in", [c, "RO" + c]), ("parent_id", "=", False)], order="id", limit=1)
        if existent:
            return existent
        d = anaf.interogheaza([c]).get(c)
        if not d:
            raise UserError(_("CUI-ul %s nu există la ANAF.", c))
        vals = self._rogri_valori_firma(d)
        vals.update(self._rogri_valori_stare(d), customer_rank=1)
        return self.with_context(no_vat_validation=True).create(vals)

    @api.onchange("vat")
    def _onchange_rogri_vat_anaf(self):
        """Partener nou: scrii CUI-ul → restul vine din ANAF (doar dacă denumirea e goală)."""
        c = anaf.cui_curat(self.vat)
        if not c or self.name or not anaf.cui_valid(c):
            return
        try:
            d = anaf.interogheaza([c]).get(c)
        except Exception:
            return {"warning": {"title": _("ANAF"), "message": _("ANAF nu răspunde acum; completează manual.")}}
        if not d:
            return {"warning": {"title": _("ANAF"), "message": _("CUI-ul %s nu există la ANAF.", c)}}
        for k, v in {**self._rogri_valori_firma(d), **self._rogri_valori_stare(d)}.items():
            self[k] = v

    @api.model
    def _cron_rogri_verifica_anaf(self, limita=2000):
        parteneri = self.search([("vat", "!=", False), ("parent_id", "=", False)],
                                order="rogri_anaf_data asc nulls first, id", limit=limita)
        for i in range(0, len(parteneri), 100):
            try:
                parteneri[i:i + 100]._rogri_verifica_anaf()
                self.env.cr.commit()
            except Exception:
                self.env.cr.rollback()
                _logger.exception("Verificarea ANAF a eșuat; reîncerc la următoarea rulare")
                return
