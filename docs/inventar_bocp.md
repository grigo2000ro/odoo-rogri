# Inventar BOCP — ce trebuie să facă Odoo în locul lui

Scop: lista completă a ce face BOCP azi, ca să nu scăpăm nimic la trecere. Fiecare rând primește un răspuns de la Grig:
**DA** (folosim zilnic) / **RAR** / **NU** (nu folosim, nu trebuie în Odoo). Coloana „În Odoo” o completează Claude.

Sursa: ce a spus Grig (12.11.2026), conectorul BOCP (citire, 12.11.2026), bocp.ro, memoria proiectului magazinului.

## Ce am văzut prin conector (12.11.2026)

- **1.150 de produse vândabile** în nomenclator (plicuri, cutii, etichete, folie, pungi, bandă adezivă, fulgi polistiren).
- **Categorii web**: două arbori (unul vechi și unul nou „PLICURI…”), plus categorii eMag.
- **Tipuri de stoc folosite**: Marfă, Marfă retur, Produse finite, Semifabricate, Ambalaje, Materii prime etc.
- **Monede**: RON, EUR, HUF, BGN. **Unități**: buc, 1000 buc, rol, set, palet, kg, m2…
- **Surse de comenzi** active în cont: magazin propriu (CloudMart), conectori e-commerce, portal B2B, comenzi manuale, eMag.
- **eMag**: conectat, dar publicarea e oprită. **OLX**: feed inactiv.
- **CRM**: apeluri primite/plasate (legătura cu centrala), e-mailuri programate, clienți noi.
- **Abonamente**: modulul există în cont.
- **„Piloți” BOCP** (automatizări): import comenzi, emitere facturi, generare AWB, tipărire, comandă stoc la furnizori,
  planificare producție, catalog. Detaliile nu sunt vizibile (permisiune neacordată conectorului).
- Conectorul NU dă prețuri, costuri, stocuri, clienți → pentru Odoo trebuie **exporturi din BOCP** (vezi mai jos).

## Lista de confirmat

| # | Funcție în BOCP | Folosim? | În Odoo Community |
|---|---|---|---|
| 1 | Comenzi manuale / oferte către clienți | DA | Vânzări — standard |
| 2 | Facturare + trimitere automată e-Factura | DA | Facturare + `l10n_ro_edi` — standard |
| 3 | Încasări (casă, bancă), urmărire facturi neîncasate | DA | Facturare — standard |
| 4 | Stocuri: recepții (NIR), transferuri, inventar | DA | Stocuri — standard |
| 5 | Mai multe gestiuni / depozite | DA | Stocuri — standard |
| 6 | Liste de preț cu reduceri pe cantitate | DA | Liste de preț — standard |
| 7 | Prețuri speciale pe client / grup de clienți | DA | Liste de preț — standard |
| 8 | Portal B2B (clienții comandă singuri) | DA | Portal / eCommerce — standard, de verificat |
| 9 | Legătura cu magazinele (WooCommerce, Magento rogri.ro) | DA | modul suplimentar (conector), de ales |
| 10 | AWB curieri (care: Fan, Sameday, Cargus, DPD…?) | DA — prin **Innoship** (agregator, un singur API pentru toți curierii) | module suplimentare pe curier |
| 11 | Comenzi la furnizori + necesar automat | DA | Achiziții + reguli de reaprovizionare — standard |
| 12 | Feed-uri de produse de la furnizori | DA | modul suplimentar / import |
| 13 | Producție (cutii proprii?) | DA — cutii din carton | Fabricație (MRP) — standard |
| 14 | eMag | DA | modul suplimentar, de ales |
| 15 | CRM: apeluri din centrală, e-mailuri | DA | CRM standard; apelurile — de integrat |
| 16 | Abonamente | NU | — (nu e nevoie de Enterprise pentru asta) |
| 17 | e-Transport (UIT) | DA | `l10n_ro_edi_stock` — standard |
| 18 | Retururi de la clienți | DA | Stocuri + facturi storno — standard |
| 19 | Tipărire automată (facturi, AWB, etichete) | DA | de discutat (imprimantă în rețea) |
| 20 | Rapoarte zilnice (vânzări, marjă, stoc) | DA | Rapoarte standard + tabloul de bord propriu |
| 21 | Export spre WinMentor | DA | prin SPV e-Factura + **întrebarea pentru contabil** |
| 22 | Altceva? | | |

## Concluzie după răspunsuri (12.11.2026)

- Abonamentele NU se folosesc → **Odoo Community ajunge**; nu există motiv pentru Enterprise.
- Standard în Community (doar configurare): 1–8, 11, 13, 17, 18, 20.
- Nevoie de module suplimentare / integrare (de ales și testat pe rând):
  9 conector WooCommerce + Magento, 10 curieri, 12 feed-uri furnizori, 14 eMag, 15 apeluri din centrală,
  19 tipărire automată, 21 punte spre WinMentor (după răspunsul contabilului).
- AWB: prin Innoship → o singură integrare Odoo–Innoship (de verificat dacă există modul gata sau o facem prin API).
- Producție: cutii din carton → Fabricație cu rețete (carton → cutie).

## Întrebarea pentru contabil

> Contabilitatea rămâne în WinMentor, iar facturile vor fi emise din Odoo și trimise în e-Factura.
> 1. Cum ajung azi în WinMentor ieșirile din stoc la cost (descărcarea de gestiune, 607/371) din BOCP?
> 2. WinMentor ține gestiunea cantitativ-valorică sau doar contabilitatea?
> 3. Recepțiile (NIR) de la furnizori se fac în BOCP, în WinMentor sau în ambele?
> 4. Încasările (bancă, casă) se introduc în WinMentor sau vin din BOCP?

## Unde sunt exporturile în BOCP (verificat în Chrome, 12.11.2026)

- **Rapoarte → Export date** (CSV, pe perioadă): Bonuri vânzare, Articole vândute, NIR, Articole recepționate,
  Comenzi Marketplace, **Stoc zilnic**.
- **Catalog → Liste de prețuri**: 9 liste pe client (Amc 324 articole, Campack 22, Mediapost 20, RTC 10 etc.), cu
  „Editor centralizat” și „Import”. Pragurile pe cantitate nu apar aici → probabil în fișa produsului (tab „Prețuri”).
  Stoc zilnic are coloane: ID produs BOCP, denumire, categorie, dată, stoc început/sfârșit de zi, cost mediu, cost.
  **Capcană:** alegerea gestiunii (Depozit / Mainfreight) nu schimbă fișierul — cele două exporturi au ieșit identice.
- **Catalog → Catalog produse**: fără export CSV/Excel (iconițele fac doar PDF/tipărire). Tab „Prețuri”: preț de vânzare
  cu TVA pe punct de lucru, fără preț de achiziție și fără praguri. „Unelte” = înlocuire text în masă (ireversibil, NU).
- **Contacte → Agenda Contacte → Export**: alegi coloanele (42 implicit), apoi o tranșă, apoi „Descarcă fișier Excel”.
  **Capcană:** tranșele nu sunt ce scrie pe ele: „0 > 14999” a dat 14.999 rânduri, „15000 > 29999” a dat 29.999
  (de la 15.000), „45000 > 59999” a dat restul (25.889). Exportat 12.11.2026: **70.887 contacte** (65.797 clienți,
  79 furnizori, 29.452 cu CUI). La granițele tranșelor pot lipsi 1–2 contacte — pentru migrarea finală se reface.
- Gestiuni: **Depozit - En-Gros** și **Mainfreight - En-Gros**.
- **Rapoarte → Rapoarte Gestiune → Jurnal mișcări detaliat** = fișa de magazie pentru toate produsele, pe **lună**:
  produs, cod, intrare, ieșire, valoric, valoare achiziție, TVA achiziție, document (NIR, bon vânzare, bon conversie,
  bon consum, transfer, inventar…), nr./dată, preț vânzare cu TVA. Filtre: an (2010–2026), lună, punct de lucru,
  gestiune contabilă (Marfa 371, Produse finite 345, Materii prime 301, Ambalaje 381…), tip document.
  **Fără buton de export** → se poate extrage tabelul din pagină în CSV (local). Noiembrie 2026 (1–12), Marfa: 8.070 rânduri.

## Exporturi din BOCP de care avem nevoie pentru pilot

Doar ca fișiere Excel/CSV pe calculator (în `date/`, care nu intră în git):
1. Produsele cu prețul de vânzare, prețul de achiziție, cota TVA, unitatea, codul de bare.
2. Listele de preț cu pragurile de cantitate.
3. Stocul pe gestiuni la o dată.
4. 10–20 de clienți reali (pentru probă; ulterior lista completă).
