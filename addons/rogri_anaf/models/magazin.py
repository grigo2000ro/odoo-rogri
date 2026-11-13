import logging

from odoo import models

_logger = logging.getLogger(__name__)


class RogriMagazin(models.Model):
    _inherit = "rogri.magazin"

    def _client(self, o, probleme):
        """După găsirea/crearea clientului din magazin: firmele se verifică (și cele noi se completează) la ANAF."""
        client, livrare = super()._client(o, probleme)
        if client.vat and not client.rogri_anaf_data:
            nou = any(p.startswith("Client nou") for p in probleme)
            try:
                client._rogri_verifica_anaf(completeaza=nou)
            except Exception as e:  # ANAF căzut nu oprește preluarea comenzii
                _logger.warning("ANAF indisponibil la preluarea comenzii: %s", e)
                probleme.append("Clientul nu a putut fi verificat la ANAF (serviciul nu a răspuns)")
                return client, livrare
            if client.rogri_anaf_stare in ("inactiv", "radiat", "negasit", "cui_invalid"):
                probleme.append(f"Client cu probleme la ANAF: {dict(client._fields['rogri_anaf_stare'].selection)[client.rogri_anaf_stare]}")
        return client, livrare
