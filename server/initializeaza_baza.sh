#!/bin/bash
# (Re)creează baza odoo_test: firma de test în România, limba română, parola adminului, modulele pentru pilot.
# ATENȚIE: șterge baza odoo_test existentă. Rulat ca root pe server, din /opt/odoo-test.
set -e
cd /opt/odoo-test
. /root/secrete/odoo-test.env

MODULE="account,l10n_ro,l10n_ro_edi,l10n_ro_edi_stock,contacts,crm,sale_management,sale_stock,purchase,purchase_stock,stock,stock_delivery"
EXEC="docker compose exec -T -e ODOO_ADMIN_LOGIN=$ODOO_ADMIN_LOGIN -e ODOO_ADMIN_PASSWORD=$ODOO_ADMIN_PASSWORD odoo odoo"
# atenție: „shell” trebuie să fie primul argument după „odoo”, altfel Odoo îl respinge
SHELL_ODOO="$EXEC shell -d odoo_test --no-http"
EXEC="$EXEC -d odoo_test --no-http"

# 0. baza goală (Odoo oprit cât timp o ștergem)
docker compose stop odoo
docker compose exec -T db dropdb -U odoo --if-exists odoo_test
docker compose run --rm -T odoo odoo -d odoo_test -i base --load-language=ro_RO --stop-after-init --no-http 2>&1 | tail -1
docker compose start odoo
sleep 15

# 1. firma în România + parola adminului, ÎNAINTE de contabilitate (ca să se aleagă planul de conturi românesc)
$SHELL_ODOO < server/configureaza_firma.py 2>&1 | grep -E "FIRMA|Error|Traceback"

# 2. modulele
$EXEC -i "$MODULE" --stop-after-init 2>&1 | grep -E "ERROR|CRITICAL|Modules loaded" | tail -5
docker compose restart odoo

# 3. verificare
sleep 5
echo "print('VERIFICARE', env.company.name, env.company.country_id.code, env.company.chart_template, env.company.currency_id.name, env['ir.module.module'].search_count([('state','=','installed')]), env.ref('base.user_admin').login, env.ref('base.user_admin').lang)" \
  | $SHELL_ODOO 2>&1 | grep -E "VERIFICARE|Error"
