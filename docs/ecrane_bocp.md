# Cine lucrează unde în BOCP și ce înseamnă asta pentru Odoo

Spus de Grig (13.11.2026); ecranele citite în BOCP (doar citire) în aceeași zi.

## Oameni și meniuri

| Cine | Unde lucrează în BOCP |
|---|---|
| Call center + facturare (Mirela, Georgiana, Andreea, enia) | Comenzi → Ofertare și Comenzi, eCommerce, eMag și FashionDays |
| Facturare (încă o colegă) | Vânzări → Bonuri de vânzare |
| Managerul de logistică | Gestiune, Rapoarte, Comenzi, Catalog |
| Ana (contabilitate) | Financiar, Integrări, Comenzi |

## Ecranele de comenzi (ce au)

**Ofertare și Comenzi** (comenzi manuale / oferte B2B)
- File: Toate / Neofertate / Ofertate / Nefacturat / Vânzare emisă / Avans facturat / Factură avans + finală;
  etapă: Comenzi noi / În prelucrare / Finalizate / Eșuate.
- Coloane: sursă, utilizator, nr., dată, client, costuri estimate, cheltuieli, valoare, finalizare, status
  (Nouă, Trimisă la client, Semnată, Refăcută, Livrat la client), metodă plată (OP, OP la termen), aviz, factură,
  picking, COGS. Alertă pe rând: „Lipsă stoc / stoc nerezervat”.

**eCommerce** (ambalajecurierat.ro, rogri.ro, plus eMag)
- File pe magazin; etapă: Noi / În prelucrare / În livrare / Finalizate / Anulate; procesare: Nepreluate /
  Fără AWB / Fără factură; confirmare: Necesită confirmare / De revenit / Confirmat / Eșuat.
- **Status intern** ales pe fiecare rând: Nepreluată, În procesare, Pregătită pentru livrare, Predat curierului,
  Livrată, Finalizată, Confirmare plată, Producție, Returnată/Retur.
- Pe rând: bon vânzare, buton **AWB**, buton **Emite** factură, picking list, dropship, responsabil;
  se desface cu articolele comandate (stoc, productibil, preț).

**eMag și FashionDays**
- Status eMag: New / In progress / Prepared / Finalized / Returned / Cancelled; livrări la **easybox (locker)**.
- Coloane: plată (card online), status plată, bon vânzare, AWB, factură, **încasat, comision eMag**.
- Butoane: Resincronizare produse / comenzi.

**Bonuri de vânzare** (documentul de vânzare, înaintea facturii)
- File: Lista vânzări, **De facturat!**, **Ridicare client (3.022)**, Avansuri, Cu bonuri fiscale, Cu facturi,
  Fără bon fiscal, Doar cu rezervare, Nefinalizate, Anulate.
- Majoritatea create **automat** („MinutelyCron”, „Pilot Comenzi”) din comenzile online.
- Status liber: Expediat, Confirmare plată, Palet, Produse lipsă, Așteptare răspuns client, Ridicare colet din
  depozit, Bursa, eMag… Metodă plată: card online, C.C. (ramburs), O.P., chitanță.
- Coloane: profit %, finalizare, referință externă (nr. comandă magazin), mențiune publică, ridicare personală,
  AWB, dropship, responsabil.

## Echivalentul în Odoo (propunere)

| BOCP | Odoo |
|---|---|
| Ofertare și Comenzi | Vânzări → Oferte/Comenzi (ofertă → trimisă → semnată online → comandă) |
| eCommerce, eMag | aceleași comenzi, cu câmp **Sursă** (magazin / eMag / manual) și file pe sursă |
| Bon de vânzare | nu există separat: comanda + livrarea fac același lucru; „De facturat” e filtru standard |
| Status intern / status liber | câmp **Etapă** (aceleași valori) + tablă Kanban, pentru call center |
| Butoanele AWB / Emite pe rând | butoane în lista de comenzi (modulul nostru + Innoship) |
| Ridicare client | metodă de livrare „Ridicare personală” + filtru |
| Încasat / comision eMag | câmpuri pe comandă, din conectorul eMag |
| Alertă „lipsă stoc” | coloană/culoare în listă (disponibilitatea e standard în Odoo) |

Primul modul „Rogri” ar face: meniul **Comenzi** ca în BOCP (file pe sursă și pe etapă), câmpul Etapă cu
valorile de mai sus, coloanele obișnuite (profit %, metodă plată, AWB, factură, responsabil) și butoanele pe rând.

De citit încă: Financiar și Integrări (Ana), Gestiune și Rapoarte (logistică).
