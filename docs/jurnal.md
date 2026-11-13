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
  1.233 de contacte au un CUI folosit și apar la mai multe contacte (dubluri în BOCP) — de curățat înainte de trecerea reală.
- Capcane: Odoo respinge CUI „-” chiar cu `no_vat_validation` → curățare la pregătire + import care sare înregistrările
  respinse; ieșirea trecută prin `tail` apare abia la final → progresul se vede numărând în bază.
- **Test cap-coadă** (`server/test_flux.py`) pe un client real din import (BOCP-5, Cluj), 100 × Cutie 200x150x90 +
  10 × Bandă solvent albă: comanda S00003 (114,30 + TVA 24,00 = 138,30) → livrarea WH/OUT/00003 (stoc 2072→1972,
  3410→3400) → factura INV/2026/00001 (4111 = 707 + 4427) → încasare bancă (512 = 4111, factura „plătită”). Merge.
  - **e-Transport** cere pe fiecare livrare un transportator cu firmă asociată → creat „Curier (test - Innoship)” cu
    partener „Transportator TEST (de inlocuit)”; în producție = curierii reali, cu CUI.
  - Odoo 19: livrarea se validează doar după „pregătit” (`picked`); la prima validare întreabă dacă trimite **SMS
    clientului** → oprit (`stock_text_confirmation = False`). Coada de e-mail oprită (baza are clienți reali).
  - Stocul e evaluat **periodic** → livrarea nu face notă 607/371 în Odoo (descărcarea rămâne în WinMentor —
    de confirmat cu contabilul).
  - **XML e-Factura** se generează (doar local, netrimis), dar lipseau datele firmei: CUI, stradă, județ.
    Puse din BOCP (Sistem → Setări cont → Date companie, cu acordul lui Grig): RO17326100, J2005000552294,
    str Toma Socolescu nr 33 B, Paulești 107400, Prahova. După asta XML-ul CIUS-RO 1.0.1 iese **fără erori**
    (furnizor RO-PH, client cu CUI RO-CJ, 2 linii, TVA 21% = 24,00, fără TVA 114,30). „De plată 0,00” pentru că
    factura era deja încasată (normal, e-Factura se trimite înainte de încasare → 138,30).
  - De făcut pentru producție: seria facturilor (acum „INV/2026/…”, în BOCP alta), conectarea la SPV (certificat
    digital, o face Grig), transmiterea în mediul de test ANAF.
- **Liste de preț pe client** (BOCP: Catalog → Liste de prețuri; citite din pagină cu script →
  `date/bocp_liste_pret_2026-11-12.csv`): 9 liste, 383 reguli, fiecare alocată unui singur client (planteo — niciunul).
  Două feluri de reguli: **adaos % peste prețul de achiziție** (Amc 324, Campack 22, Optimpack 1; toate 13%) și
  **preț fix fără TVA** (restul). Importate cu `server/importa_liste_pret.sh` ca liste Odoo „BOCP - <nume>”
  (adaos → formulă pe cost, fix → preț fix), alocate celor 8 clienți (ref BOCP-<id>).
  Verificat (`server/test_liste_pret.py`, comenzile ciornă S00004–S00006 pentru Amc, RTC, Campack): prețurile din
  Odoo = cele din BOCP la toate liniile. Atenție: adaosul se aplică pe costul din Odoo (ultimul NIR); la 23 din 347
  produse costul diferă cu >2% de „preț achiziție” din BOCP. 8 produse din lista Amc ies mai scumpe decât prețul
  obișnuit de vânzare (mediana ultimelor 90 zile) — de verificat cu Grig.
- **Grila de preț pe cantitate NU e în BOCP**: e în Magento (ambalajecurierat.ro, 257 produse, 4–6 trepte, aceeași
  pentru toți) și e deja extrasă în proiectul `ambalajecurierat` (`date/extras/`). În Odoo ar fi o listă cu praguri
  (`min_quantity`) — pas separat.
- Capcane BOCP: fereastra listei se deschide pe ultimul tab folosit; la listele mici lipsește selectorul de pagină.

## 13.11.2026
- Grig: call center + facturare lucrează în Comenzi (Ofertare și Comenzi, eCommerce, eMag) și Vânzări → Bonuri de
  vânzare; logistica în Gestiune, Rapoarte, Comenzi, Catalog; Ana (contabilitate) în Financiar, Integrări, Comenzi.
  Ecranele citite și descrise în `docs/ecrane_bocp.md`.
- **Primul modul propriu `addons/rogri_comenzi`** (instalat în odoo_test): meniul de sus „Comenzi” ca în BOCP
  (Toate / Ofertare și comenzi / eCommerce / eMag; Tablă comenzi; Facturare → De facturat!, Ridicare client,
  Facturi emise). Pe comandă: sursă, etapă (valorile din BOCP), metodă plată, ridicare personală, AWB, referință
  externă, profit % (din marja Odoo), alertă „lipsă stoc” (rând roșu / etichetă pe card). Butoane pe rând:
  **Emite** (confirmă + facturează + validează) și **AWB** (deocamdată doar mesaj — Innoship urmează).
  Filtre ca filele din BOCP: comenzi noi, în prelucrare, în livrare, finalizate, de facturat, fără AWB, ridicare.
  Verificat în shell (profit S00003 = 40,3%, Emite → INV/2026/00002) și în browser (listă + tablă).
- Capcane: `docker compose restart` din același script nu se executase (Odoo „Up 16 hours”) → site-ul nu vedea
  câmpurile noi; browserul ținea ecranele vechi în memorie (IndexedDB) → acum `server/instaleaza_modul.sh` repornește
  și verifică; în browser Ctrl+Shift+R.
- **Etapa 1a — comenzi din magazin în Odoo** (modul `addons/rogri_magazine`):
  - Magazinul de test WooCommerce are 7.567 comenzi aduse din Magento (2022–2026, stare „arhiva-magento”), 260
    produse cu SKU — **toate cele 260 de coduri există în Odoo**. Prețuri fără TVA, CUI în `_billing_cui`.
  - Cheie API WooCommerce **doar de citire** („Odoo test”, id 1), salvată în `/root/secrete/odoo-test.env`
    (`WOO_TEST_CK/CS`); site-ul de test cere și parola HTTP (merge: parolă HTTP + cheia în adresă).
  - Odoo citește la 5 minute comenzile modificate (cron „Rogri: preluare comenzi…”) și creează **oferte** (nu
    confirmă → nu mișcă stocul, nu trimite nimic). Client după CUI, apoi e-mail; altfel client nou. Produse după
    cod. Transportul și taxele ca linii de serviciu. Starea din magazin → etapa. Tot ce nu se potrivește → Comenzi →
    Configurare → Jurnal preluare. Comanda deja preluată nu se dublează (constrângere magazin + nr.).
  - Probă pe ultimele 60: **0 diferențe de total, 0 produse negăsite**; 36 cu clientul din BOCP, 3 clienți noi,
    21 fără date de client (comenzile vechi din Magento au venit în magazinul de test fără nume/adresă/e-mail).
  - **Flux viu verificat:** comanda de test #8601 plasată în magazin (client „Test Odoo”, ramburs, 331,54 lei,
    e-mailuri blocate în script) a apărut singură în Odoo în ≤5 minute, cu același total. Comanda #8601 rămâne în
    magazinul de test (creată „test-odoo”).
  - De verificat în BOCP: clienții din comenzile recente negăsiți după CUI/e-mail/telefon (exportul BOCP îi are?).
- **Verificare ANAF după CUI** (modul `addons/rogri_anaf`, serviciul public PlatitorTvaRest v9, același ca în
  magazin; max. 100 CUI/cerere, 1 cerere/s):
  - fișa partenerului: tab „ANAF” (stare activ / INACTIV / RADIAT / negăsit / CUI invalid, plătitor TVA, TVA la
    încasare, split TVA, e-Factura, diferențe față de ANAF) + bandă roșie dacă firma e inactivă/radiată; butoane
    „Verifică la ANAF” și „Completează din ANAF” (cu confirmare); filtre „Probleme ANAF”, „Date diferite de ANAF”;
    verificare în masă din listă (Acțiuni → Verifică la ANAF);
  - partener nou: scrii CUI-ul → denumire, adresă, județ, Reg. Com., RO după TVA vin din ANAF;
  - comandă manuală: câmp „CUI client” → clientul existent sau creat din ANAF (verificat în browser cu 4221306 →
    Ministerul Finanțelor; clientul de probă șters); starea ANAF a clientului apare pe comandă;
  - clienții din magazine cu CUI se verifică la preluare (cei noi se completează din ANAF); inactiv/radiat → problemă
    în Jurnal preluare;
  - cron noaptea (01:30 UTC): 2.000 de clienți cu CUI, cei mai vechi verificați întâi.
  - Primul lot (200 clienți BOCP): 173 activi, **21 INACTIVI, 2 RADIAȚI**, 4 CUI invalid; 34 cu „RO” greșit
    (plătitor/neplătitor TVA), 14 denumiri diferite (unele CUI-uri aparțin altei firme!), 28 localități diferite.
  - **Verificarea completă** (29.245 clienți cu CUI, ~12 minute): 27.084 activi, **1.692 INACTIVI, 192 RADIAȚI**,
    10 negăsiți, 267 CUI invalid; **2.921 cu „RO” greșit**, 1.423 denumiri diferite, 5.351 localități diferite;
    15.774 plătitori TVA, 7.981 în registrul e-Factura. De curățat înainte de trecere (filtrele din Contacte).
  - **„RO” corectat după ANAF** (cerut de Grig): 2.921 clienți — plătitor TVA → „RO”+CUI, neplătitor → doar cifrele.
    Copie înainte: `/root/backup-claude/odoo_test_cui_inainte_RO_20261113_0954.csv` (id, ref, vat vechi). După:
    0 plătitori fără RO, 0 neplătitori cu RO. Denumirile și adresele NU s-au schimbat (de verificat de un om).
  - Comparația ține cont de forme diferite: „Mun. Cluj-Napoca” = „Cluj Napoca”, „SC X SRL” = „X S.R.L.”, PFA.
- **Adrese repetate din BOCP** (Grig: „în BOCP apărea eroarea cu adresa duplicată”): din 83.815 adrese, **885 au
  textul repetat** în câmpul stradă (848 × 2, 19 × 3, 15 × 4, 3 × 6–8; ex. „STR MITROPOLIEI NR 39” × 8) — vine
  chiar din exportul BOCP. 428 sunt aceeași bucată repetată exact (corectabile automat, 39 sunt adrese de livrare);
  restul de ~457 sunt amestecate (ex. „Str Sofiei str. Sofiei 3str. Sofiei 3…”) → de corectat de un om; câteva
  „× 2” sunt false alarme („Mircea Vodă … intersecție Mircea Vodă”). Separat: **735 adrese de livrare identice cu
  sediul** (scrise puțin diferit) — inutile. Nu există livrări dublate la același client.
- Capcane Odoo 19: categoria-rădăcină „All” (`product.product_category_all`) nu mai există; prețul implicit e 1 leu;
  fișierele copiate în container sunt ale lui root → se șterg cu `exec -u root`.
