# Odoo Rogri — pilot pentru înlocuirea BOCP

Scop: testăm Odoo Community 19 ca ERP (comenzi, stocuri, facturare + e-Factura, liste de preț cu reduceri pe cantitate,
portal B2B, AWB, achiziții) în locul BOCP. **Contabilitatea rămâne în WinMentor.**

## Unde sunt lucrurile

| Ce | Unde |
|---|---|
| Configurația (acest depozit) | `C:\Users\Grig\Documents\odoo-rogri` + copie privată pe GitHub (`grigo2000ro/odoo-rogri`) |
| Pilotul pe server | VPS Hostinger KVM 2 (același cu magazinul de test), folder `/opt/odoo-test`, în Docker |
| Adresa | `https://odoo-test.rogri.tech` (ascunsă de Google) |
| Parolele | pe server: `/root/secrete/odoo-test.env` — Grig le citește din consola web Hostinger, nu se scriu în chat |

## Structură

- `docker-compose.yml` — Odoo 19 + PostgreSQL 16, cu limite de memorie (Odoo 2 GB, baza 768 MB), porturi doar local.
- `config/odoo.conf.model` — setările Odoo; pe server devine `config/odoo.conf` (cu parola, nu intră în git).
- `addons/` — module suplimentare (localizarea România de la OCA, conector WooCommerce, curieri) — vor veni pe rând.
- `server/nginx/` — șabloanele HestiaCP care leagă adresa de Odoo (`odoo.tpl`, `odoo.stpl`).
- `docs/jurnal.md` — ce s-a făcut, pe zile.

## Reguli

- Pilotul nu atinge restul serverului (MariaDB, PHP, magazinul de test, n8n, centrala).
- Înainte de orice schimbare pe server: snapshot sau copie.
- Ștergerea completă a pilotului: `cd /opt/odoo-test && docker compose down -v` + ștergerea domeniului din Hestia.
- Pentru producție (după pilot) Odoo se mută pe un VPS separat.
