#!/bin/bash
# Încarcă listele de preț pe client în odoo_test. Rulat ca root pe server, din /opt/odoo-test.
# Înainte: de pe calculator se copiază date/bocp_liste_pret_*.csv în /opt/odoo-test/import/bocp_liste_pret.csv (scp).
set -e
cd /opt/odoo-test
docker compose cp import/bocp_liste_pret.csv odoo:/tmp/bocp_liste_pret.csv
docker compose exec -T odoo odoo shell -d odoo_test --no-http < server/importa_liste_pret.py 2>&1 \
  | grep -E "LISTA|LIPSA|IMPORT|Error|Traceback|line [0-9]+" | tail -45
docker compose exec -T -u root odoo rm -f /tmp/bocp_liste_pret.csv
rm -f import/bocp_liste_pret.csv
