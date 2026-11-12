#!/bin/bash
# Încarcă partenerii (clienți + furnizori) în odoo_test. Rulat ca root pe server, din /opt/odoo-test.
# Înainte: de pe calculator se copiază date/odoo_parteneri.csv în /opt/odoo-test/import/ (scp).
set -e
cd /opt/odoo-test
docker compose cp import/odoo_parteneri.csv odoo:/tmp/odoo_parteneri.csv
docker compose exec -T odoo odoo shell -d odoo_test --no-http --limit-time-real=0 --limit-time-cpu=0 \
  < server/importa_parteneri.py 2>&1 | grep -E "PROGRES|IMPORT|RESPINS|Error|Traceback|line [0-9]+" | tail -45
docker compose exec -T -u root odoo rm -f /tmp/odoo_parteneri.csv
rm -f import/odoo_parteneri.csv
