#!/bin/bash
# Instalează sau actualizează un modul propriu din addons/ în odoo_test și repornește Odoo.
# Folosire (ca root pe server, din /opt/odoo-test):  bash server/instaleaza_modul.sh rogri_comenzi
# Înainte: de pe calculator  scp -r addons/<modul> ambalaje-vps:/opt/odoo-test/addons/
# ATENȚIE: după instalare Odoo TREBUIE repornit (altfel site-ul nu vede câmpurile noi), iar în browser poate
# fi nevoie de o reîncărcare completă (Ctrl+Shift+R).
set -e
MODUL="$1"
[ -n "$MODUL" ] || { echo "Lipsește numele modulului"; exit 1; }
cd /opt/odoo-test
find "addons/$MODUL" -type f -exec sed -i 's/\r$//' {} \;
chmod -R a+rX "addons/$MODUL"
if docker compose exec -T db psql -U odoo -d odoo_test -tAc "select state from ir_module_module where name='$MODUL'" | grep -q installed; then
  OPT="-u"
else
  OPT="-i"
fi
docker compose exec -T odoo odoo -d odoo_test $OPT "$MODUL" --stop-after-init --no-http 2>&1 \
  | grep -E "ERROR|CRITICAL|Traceback|Modules loaded|line [0-9]+" | tail -20
docker compose restart odoo
sleep 10
docker ps --format '{{.Names}} {{.Status}}' | grep odoo-test-odoo
curl -s -o /dev/null -w 'login %{http_code}\n' https://odoo-test.rogri.tech/web/login
