#!/bin/bash
# Creează config/odoo.conf din model, cu parolele din /root/secrete/odoo-test.env. Rulat ca root din /opt/odoo-test.
set -e
cd /opt/odoo-test
. /root/secrete/odoo-test.env
umask 077
sed -e "s/__ADMIN_PASSWD__/$ODOO_MASTER_PASSWORD/" -e "s/__PG_PASSWORD__/$PG_PASSWORD/" config/odoo.conf.model > config/odoo.conf
# în imaginea Odoo utilizatorul „odoo” are uid 100, gid 101
chown 100:101 config/odoo.conf
chmod 600 config/odoo.conf
echo "odoo.conf generat"
