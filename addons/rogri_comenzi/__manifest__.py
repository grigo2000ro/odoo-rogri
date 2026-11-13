{
    "name": "Rogri - Comenzi (ca în BOCP)",
    "version": "19.0.1.0.0",
    "summary": "Meniul Comenzi organizat ca în BOCP: surse, etape, tablă pentru call center, butoane pe rând",
    "description": """
Ecranul de lucru pentru call center și facturare, după modelul BOCP (vezi docs/ecrane_bocp.md):
- sursa comenzii (manual / ambalajecurierat.ro / rogri.ro / eMag / portal B2B);
- etapa internă (Nepreluată, În procesare, Pregătită, Predat curierului, Confirmare plată, Producție...);
- metoda de plată, ridicare personală, AWB, profit %, alertă lipsă stoc;
- meniul „Comenzi” cu aceleași file ca în BOCP și tabla (Kanban) pe etape;
- butoane pe rând: Emite factura, AWB.
""",
    "author": "Rogri Impex",
    "license": "LGPL-3",
    "depends": ["sale_management", "sale_stock", "sale_margin", "stock_delivery", "account"],
    "data": [
        "views/sale_order_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
}
