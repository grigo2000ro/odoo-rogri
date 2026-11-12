# Jurnal

## 12.11.2026
- Decis: Odoo Community în locul BOCP; contabilitatea rămâne în WinMentor; peste 5 utilizatori; fără grabă.
- Aflat: e-Factura și e-Transport sunt în Odoo Community (modulul oficial `l10n_ro_edi`); WinMentor poate importa
  facturile de ieșire din SPV → punte Odoo → ANAF → WinMentor. **Deschis:** cum ajung în WinMentor ieșirile din stoc
  la cost (de întrebat contabilul).
- VPS verificat: 6,2 GB RAM liberi din 7,8, 66 GB disc liber, porturile 8069/8072 libere, fără swap.
- DNS `rogri.tech` e la Hostinger (fără înregistrare wildcard) → `odoo-test.rogri.tech` trebuie adăugat în hPanel.
- Creat acest depozit cu configurația pilotului.
- Pe server (după snapshot-ul făcut de Grig): swap 2 GB (`/swapfile`, swappiness 10); `/opt/odoo-test` cu Odoo 19 +
  PostgreSQL 16 în Docker; parolele în `/root/secrete/odoo-test.env`; `config/odoo.conf` generat cu `server/genereaza_conf.sh`.
- Baza `odoo_test`: firma „Rogri Impex SRL (TEST)”, România, plan de conturi `ro`, RON, interfață în română; module:
  contabilitate/facturare, `l10n_ro`, `l10n_ro_edi` (e-Factura), `l10n_ro_edi_stock` (e-Transport), contacte, CRM,
  vânzări, stocuri, achiziții, livrări. Adminul are parola din fișierul de secrete (nu `admin`/`admin`).
- Capcane: utilizatorul `odoo` din imagine are uid 100 (nu 101); `odoo shell` trebuie scris înaintea opțiunilor
  (`odoo shell -d odoo_test`); `docker compose exec` nu trece prin entrypoint → parola bazei trebuie în `odoo.conf`;
  dacă țara firmei nu e RO înainte de contabilitate, Odoo pune planul generic în USD.
- Hestia: domeniul `odoo-test.rogri.tech` la utilizatorul `app`, șablon proxy `odoo` (copiat în
  `/usr/local/hestia/data/templates/web/nginx/`). **SSL încă nu** — înregistrarea DNS nu apare la serverele Hostinger.
- Verificat după: magazinul de test, n8n, app.rogri.tech răspund ca înainte; Odoo ~240 MB + baza ~120 MB RAM.
