{
    "name": "Rogri - Verificare ANAF după CUI",
    "version": "19.0.1.0.0",
    "summary": "Datele firmei din ANAF după CUI: la clienți, la comenzi manuale și la comenzile din magazine",
    "description": "Serviciul public ANAF PlatitorTvaRest v9: stare ANAF pe partener, completare după CUI, "
                   "CUI client pe comanda manuală, verificarea clienților din magazine, verificare noaptea.",
    "author": "Rogri Impex",
    "license": "LGPL-3",
    "depends": ["rogri_comenzi", "rogri_magazine", "l10n_ro"],
    "data": [
        "data/cron.xml",
        "views/partner_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
}
