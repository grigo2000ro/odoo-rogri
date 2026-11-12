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
| 1 | Comenzi manuale / oferte către clienți | | Vânzări — standard |
| 2 | Facturare + trimitere automată e-Factura | | Facturare + `l10n_ro_edi` — standard |
| 3 | Încasări (casă, bancă), urmărire facturi neîncasate | | Facturare — standard |
| 4 | Stocuri: recepții (NIR), transferuri, inventar | | Stocuri — standard |
| 5 | Mai multe gestiuni / depozite | | Stocuri — standard |
| 6 | Liste de preț cu reduceri pe cantitate | | Liste de preț — standard |
| 7 | Prețuri speciale pe client / grup de clienți | | Liste de preț — standard |
| 8 | Portal B2B (clienții comandă singuri) | | Portal / eCommerce — standard, de verificat |
| 9 | Legătura cu magazinele (WooCommerce, Magento rogri.ro) | | modul suplimentar (conector), de ales |
| 10 | AWB curieri (care: Fan, Sameday, Cargus, DPD…?) | | module suplimentare pe curier |
| 11 | Comenzi la furnizori + necesar automat | | Achiziții + reguli de reaprovizionare — standard |
| 12 | Feed-uri de produse de la furnizori | | modul suplimentar / import |
| 13 | Producție (cutii proprii?) | | Fabricație (MRP) — standard |
| 14 | eMag | | modul suplimentar, de ales |
| 15 | CRM: apeluri din centrală, e-mailuri | | CRM standard; apelurile — de integrat |
| 16 | Abonamente | | Abonamente sunt **doar Enterprise** → de discutat |
| 17 | e-Transport (UIT) | | `l10n_ro_edi_stock` — standard |
| 18 | Retururi de la clienți | | Stocuri + facturi storno — standard |
| 19 | Tipărire automată (facturi, AWB, etichete) | | de discutat (imprimantă în rețea) |
| 20 | Rapoarte zilnice (vânzări, marjă, stoc) | | Rapoarte standard + tabloul de bord propriu |
| 21 | Export spre WinMentor | | prin SPV e-Factura + **întrebarea pentru contabil** |
| 22 | Altceva? | | |

## Întrebarea pentru contabil

> Contabilitatea rămâne în WinMentor, iar facturile vor fi emise din Odoo și trimise în e-Factura.
> 1. Cum ajung azi în WinMentor ieșirile din stoc la cost (descărcarea de gestiune, 607/371) din BOCP?
> 2. WinMentor ține gestiunea cantitativ-valorică sau doar contabilitatea?
> 3. Recepțiile (NIR) de la furnizori se fac în BOCP, în WinMentor sau în ambele?
> 4. Încasările (bancă, casă) se introduc în WinMentor sau vin din BOCP?

## Exporturi din BOCP de care avem nevoie pentru pilot

Doar ca fișiere Excel/CSV pe calculator (în `date/`, care nu intră în git):
1. Produsele cu prețul de vânzare, prețul de achiziție, cota TVA, unitatea, codul de bare.
2. Listele de preț cu pragurile de cantitate.
3. Stocul pe gestiuni la o dată.
4. 10–20 de clienți reali (pentru probă; ulterior lista completă).
