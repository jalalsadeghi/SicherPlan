Please make one small UI text correction in the SicherPlan Web Admin.

Current behavior:
The Customers list tab title is shown as:
"Kundenstamm, Kontakte und Adresslinks"

Desired behavior:
The Customers list tab title should be the short label:
"Kunden"

Important:
- Do not change customer detail tabs. They should still show customer names like "RheinForum Köln" and "HafenKontor Köln".
- Do not change the customer detail page title.
- Do not change route structure, pageKey behavior, domCached, keepAlive, or backend code.
- Do not change sidebar behavior except if the same translation key is intentionally used there and the resulting sidebar label remains acceptable as "Kunden".

Likely file:
web/apps/web-antd/src/locales/langs/de-DE/sicherplan.json

Task:
1. Find the German translation key currently used for the Customers route/tab title.
2. Change only the route/tab label from "Kundenstamm, Kontakte und Adresslinks" to "Kunden".
3. Check whether the English equivalent is also overly long. If yes, keep it short as "Customers".
4. Update any snapshot/unit test only if it fails because of this text change.
5. Run the relevant web test or type check.

Acceptance criteria:
- The Customers list tab shows "Kunden".
- Customer detail tabs still show the customer names.
- No backend/API changes.
- No route/key/cache behavior changes.