#!/bin/bash
# Încarcă produsele și stocul în odoo_test. Rulat ca root pe server, din /opt/odoo-test.
# Înainte: de pe calculator se copiază date/odoo_produse.csv în /opt/odoo-test/import/ (scp).
set -e
cd /opt/odoo-test
docker compose cp import/odoo_produse.csv odoo:/tmp/odoo_produse.csv
docker compose exec -T odoo odoo shell -d odoo_test --no-http < server/importa_produse.py 2>&1 \
  | grep -E "PROGRES|IMPORT|Error|Traceback|line [0-9]+" | tail -20
docker compose exec -T -u root odoo rm -f /tmp/odoo_produse.csv
