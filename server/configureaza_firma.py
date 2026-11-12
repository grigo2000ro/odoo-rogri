# Rulat în `odoo shell` (vezi server/initializeaza_baza.sh). Setează firma de test, limba și parola adminului.
import os

firma = env.company
firma.write({
    "name": "Rogri Impex SRL (TEST)",
    "country_id": env.ref("base.ro").id,
    "city": "București",
})
ro = env["res.lang"]._activate_lang("ro_RO")
admin = env.ref("base.user_admin")
admin.write({
    "login": os.environ["ODOO_ADMIN_LOGIN"],
    "password": os.environ["ODOO_ADMIN_PASSWORD"],
    "lang": "ro_RO",
    "tz": "Europe/Bucharest",
})
env.cr.commit()
print("FIRMA:", firma.name, firma.country_id.code, "| ADMIN:", admin.login, admin.lang)
