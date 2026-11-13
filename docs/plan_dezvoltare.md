# Plan de dezvoltare și customizare Odoo (înlocuirea BOCP)

Scris 13.11.2026. Se actualizează pe măsură ce terminăm etape. Stadiul zilnic e în `jurnal.md`.

## Principii
1. **Odoo merge în paralel cu BOCP** până la trecere. BOCP rămâne sistemul real; Odoo doar *citește* și repetă
   operațiile, ca să comparăm. Nimic din Odoo nu trimite la clienți, ANAF, curieri sau magazine până nu hotărăm.
2. **Copiem fluxurile de lucru din BOCP, nu ecranele unu la unu.** Adăugăm în module proprii (`addons/rogri_*`),
   nu modificăm Odoo → actualizările anuale rămân posibile.
3. **Fiecare etapă se termină cu un test pe date reale** și cu „merge / nu merge” de la oamenii care o folosesc.
4. **Producția pe un VPS separat**, nu pe cel de acum (care ține magazinul nou, n8n, centrala).

## Ce e gata (12–13.11.2026)
- Odoo 19 Community pe https://odoo-test.rogri.tech; e-Factura și e-Transport instalate.
- Din BOCP: 1.150 produse + stoc, 70.887 clienți/furnizori, 9 liste de preț pe client, jurnalul de mișcări ian–nov.
- Fluxul comandă → livrare → factură → încasare testat; XML e-Factura fără erori (netrimis).
- Modulul `rogri_comenzi`: meniul Comenzi ca în BOCP, etape, tablă, profit %, lipsă stoc, butonul Emite.

## Ordinea propusă și de ce

Întrebarea a fost: încep cu legarea magazinelor? **Da, dar doar în citire și în paralel cu BOCP.**
Comenzile online sunt cele mai multe (în BOCP, ~80% din bonuri sunt create automat din magazine), deci arată cel
mai repede dacă Odoo face față volumului real și dacă produsele și clienții se potrivesc. Imediat după ele vin
**livrarea (Innoship)** și **facturarea reală (SPV)**, fără de care comenzile n-au cum să plece din Odoo.

### Etapa 1 — Comenzile online intră în Odoo (în paralel cu BOCP) · ~1–2 săptămâni
**1a. ambalajecurierat.ro (WooCommerce de test, pe același server)** — primul, pentru că e tot test, deci fără risc.
- Odoo citește comenzile din WooCommerce (la câteva minute) → comandă cu sursa „ambalajecurierat.ro”, etapa
  „Nepreluată”, metoda de plată, transportul, referința externă (nr. comenzii din magazin).
- Clientul: găsit după e-mail / CUI; dacă nu există, se creează. Produsele: după cod (SKU = cod produs BOCP).
- Raport de potrivire: comenzi cu produse sau clienți negăsiți → listă de corectat, nu se ghicește nimic.
- Doar citire: Odoo NU trimite înapoi stoc sau prețuri (le trimite încă BOCP).

**1b. rogri.ro (Magento)** — comenzile reale, tot doar în citire.
- De la Grig: un utilizator API în adminul Magento (cheie cu drept doar de citire comenzi).
- Comparăm zilnic: comenzile din Odoo = comenzile din BOCP (număr, total, produse).

**1c. Raport zilnic de comparație Odoo ↔ BOCP** (comenzi, valori) — ca să știm când putem avea încredere.

Mai târziu (după trecere): Odoo trimite stocul și prețurile în magazine, în locul BOCP.

### Etapa 2 — Livrare și AWB prin Innoship · ~1 săptămână
- Butonul AWB din `rogri_comenzi` → Innoship (cont de test sau AWB-uri anulate imediat).
- Curierii reali ca transportatori (cu CUI) pentru e-Transport; ridicarea personală ca metodă de livrare.
- Tipărirea etichetei AWB și a avizului; easybox pentru eMag.
- De la Grig: cheile API Innoship (le pune el pe server, nu în chat).

### Etapa 3 — Facturare reală și contabilitate · ~1 săptămână + răspunsul contabilului
- Seria facturilor ca în BOCP; numerotare de la data trecerii.
- SPV: legarea cu certificatul digital (o face Grig, eu ghidez); trimitere în **mediul de test ANAF**.
- Legătura cu WinMentor după răspunsul contabilului: facturi prin SPV; încasări și descărcarea de gestiune (607/371)
  — export din Odoo sau evidență în WinMentor.

### Etapa 4 — Stocuri, achiziții, producție (managerul de logistică) · ~2 săptămâni
- Gestiunile Depozit și Mainfreight; recepții (NIR) de la furnizori; transferuri; inventar.
- **Inventar la cele 153 de produse cu stoc negativ** înainte de trecere.
- Necesar de achiziție automat (reguli min/max — „Necesar de comandat” din BOCP); comenzi la furnizori.
- Producția de cutii: rețete (carton → cutie), comenzi de producție, costul cutiei.
- Ecrane pentru logistică după modelul Gestiune / Rapoarte din BOCP (de citit întâi în BOCP).

### Etapa 5 — eMag · ~1–2 săptămâni
- Comenzile eMag în Odoo (sursa eMag), easybox, încasat și comision; apoi stocul și prețul spre eMag.
- De ales: modul existent (OCA / comercial) sau legătură proprie prin API eMag.

### Etapa 6 — Prețuri și portal B2B · ~1 săptămână
- Grila pe cantitate (din Magento, 257 produse) ca listă cu praguri; regula „cost + adaos” pentru clienții B2B.
- Portalul B2B Odoo: clienții văd prețurile lor, comandă, își descarcă facturile.
- De lămurit: cine actualizează prețurile după trecere (Odoo → magazine).

### Etapa 7 — Ecrane pe roluri și rapoarte · continuu
- Ana (Financiar, Integrări): încasări, plăți, solduri clienți/furnizori, exporturi pentru WinMentor.
- Panou de alerte ca bara „Piloți” din BOCP: comenzi blocate, facturi netrimise în SPV, AWB-uri lipsă, stoc sub minim.
- Rapoarte zilnice: vânzări, marjă, stoc; legătura cu tabloul de bord din `analiza-financiara`.
- CRM / call center: apelurile din centrala telefonică pe fișa clientului.

### Etapa 8 — Trecerea · ~2–4 săptămâni de rulare în paralel
- VPS separat pentru producție, copii de siguranță zilnice în alt loc, HTTPS, utilizatori și drepturi pe roluri.
- Curățarea datelor: contacte cu CUI dublat (1.233), adrese fără județ, CUI-uri neconforme (179).
- Instruire scurtă pe roluri (call center, facturare, logistică, contabilitate), cu ecranele din etapele de mai sus.
- Încărcarea finală: stoc la zi (după inventar), clienți, prețuri, comenzi deschise; solduri doar dacă decide
  contabilul.
- Data trecerii: la început de lună (propus 1 februarie sau 1 martie 2027), cu BOCP păstrat în citire o vreme.
- Costul BOCP se oprește abia după o lună fără probleme.

## Ce îmi trebuie de la tine, pe etape
| Etapa | De la Grig |
|---|---|
| 1b | utilizator API în Magento rogri.ro (doar citire) |
| 2 | cheile API Innoship (puse de tine pe server) |
| 3 | răspunsul contabilului; certificatul digital pentru SPV; seria facturilor |
| 4 | 30 de minute cu managerul de logistică, să-mi arate ce face zilnic |
| 5 | acces API eMag |
| 7 | 30 de minute cu Ana, la fel |
| 8 | decizia pentru VPS-ul de producție și data trecerii |

## Riscuri și cum le ținem sub control
- **Coduri de produs diferite între magazine și BOCP/Odoo** → raport de potrivire la etapa 1, corectăm înainte.
- **Volum** (zeci de comenzi pe zi, ~70.000 de clienți) → testat în paralel cu BOCP înainte de trecere.
- **Actualizări Odoo** → doar module proprii, fără modificări în Odoo; testăm actualizarea pe copie.
- **Date personale** → Odoo pe serverul nostru, doar HTTPS, utilizatori cu drepturi pe rol, fără mesaje automate
  spre clienți până la trecere.
