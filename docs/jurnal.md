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
  `/usr/local/hestia/data/templates/web/nginx/`).
- DNS: înregistrarea nu se salvase; adăugată de Claude în hPanel (cu acordul lui Grig): A `odoo-test` → 187.124.166.96,
  TTL 300. A apărut la serverele Hostinger după ~3 minute.
- SSL Let's Encrypt (`v-add-letsencrypt-domain app odoo-test.rogri.tech`), valabil până la 10.02.2027 (reînnoire automată
  Hestia). **Capcană:** Hestia n-a reîncărcat nginx după certificat → HTTPS servea certificatul implicit până la
  `systemctl reload nginx`.
- Verificat: `https://odoo-test.rogri.tech/web/login` → 200, `X-Robots-Tag: noindex`, http → 301 spre https,
  managerul de baze dezactivat („disabled by the administrator”).
- Verificat după: magazinul de test, n8n, app.rogri.tech răspund ca înainte; Odoo ~240 MB + baza ~120 MB RAM.
- Exporturi din BOCP (în `date/`, doar local): stoc zilnic, contacte (70.887), catalog produse (1.150, citit din
  pagină), jurnal mișcări ian–nov 2026 (145.788, citit din pagină cu script). Detalii și capcane în `inventar_bocp.md`.
- **Exportul „Stoc zilnic” nu e de încredere** (ex. Cutie 200x150x90: −140.217 în export vs 2.072 în catalog) →
  stocul se ia din catalog („Stoc Global”).
- Import în `odoo_test` (`server/pregateste_produse.py` local → `server/importa_produse.sh` pe server):
  1.150 produse stocabile, 27 categorii, 12 furnizori; cost = ultimul NIR 2026 (454) sau ultimele ieșiri (27);
  preț vânzare = mediana bonurilor din ultimele 90 zile / 1,21 (427); fără preț → 0, nu 1 leu implicit.
  Stoc: 328 produse, 201.427.459 buc., 11.836.608 lei la cost — identic cu fișierul.
  153 produse cu stoc **negativ** în BOCP nu s-au importat (lista în `date/odoo_produse_raport.txt`).
- „Imprimare” (98,5 mil. buc. = 9,85 mil. lei), „DESEURI CARTON” (99,9 mil.), „CURIER RAPID” (97.016) aveau stoc
  în BOCP, dar nu sunt marfă. **Decis de Grig:** Imprimare (3064) și Curier rapid (3065) = **servicii** (fără stoc);
  cele 6 produse „DESEU…” = categoria **Deșeuri** (stocul rămâne ca în BOCP, fără cost).
  După reimport: stoc 2.016.248 buc. marfă + produse finite = **1.982.114,75 lei** la cost; deșeuri 100,8 mil. „buc.”, 0 lei.
- Import parteneri (`server/pregateste_parteneri.py` local → `server/importa_parteneri.sh` pe server, ~20 min):
  **70.887** (32.101 firme, 65.797 clienți, 79 furnizori, 29.242 cu CUI) + 16.528 adrese de livrare (corespondența
  diferită de sediu), 0 respinși. Referința internă `BOCP-<ID>` → reimportul actualizează, nu dublează.
  CNP-urile (26) nu s-au importat. 179 de CUI-uri neconforme din BOCP („-”, „****”, mai multe coduri, nr. J…) sunt
  în notele partenerului, nu la CUI. Telefon2 → note (Odoo 19 nu mai are „mobil”). Termene de plată din BOCP (89).
  1.231 de CUI-uri apar la mai multe contacte (dubluri în BOCP) — de curățat înainte de trecerea reală.
- Capcane: Odoo respinge CUI „-” chiar cu `no_vat_validation` → curățare la pregătire + import care sare înregistrările
  respinse; ieșirea trecută prin `tail` apare abia la final → progresul se vede numărând în bază.
- Capcane Odoo 19: categoria-rădăcină „All” (`product.product_category_all`) nu mai există; prețul implicit e 1 leu;
  fișierele copiate în container sunt ale lui root → se șterg cu `exec -u root`.
