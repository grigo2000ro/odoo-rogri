{
    "name": "Rogri - Magazine online (preluare comenzi)",
    "version": "19.0.1.0.0",
    "summary": "Preia comenzile din WooCommerce (ambalajecurierat.ro) în Odoo, doar în citire, în paralel cu BOCP",
    "description": """
Etapa 1a din docs/plan_dezvoltare.md.
- Magazinele se configurează în Comenzi → Configurare → Magazine online (adresă, cheie API doar de citire).
- La câteva minute (sau la buton) Odoo citește comenzile noi/modificate și creează comenzi cu sursa magazinului.
- Comenzile rămân OFERTE (neconfirmate): nu mișcă stocul și nu trimit nimic nicăieri.
- Clientul: după CUI, apoi după e-mail; dacă nu există, se creează. Produsele: după cod (SKU = cod produs).
- Tot ce nu se potrivește apare în Jurnal preluare (nu se ghicește nimic).
""",
    "author": "Rogri Impex",
    "license": "LGPL-3",
    "depends": ["rogri_comenzi"],
    "data": [
        "security/ir.model.access.csv",
        "data/cron.xml",
        "views/magazin_views.xml",
    ],
    "installable": True,
}
