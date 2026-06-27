# F24 Follow-ups board (embed)

Host del board del monitor de follow-ups de Ferre24 para embeberlo como **iframe dentro
de GHL** (GitHub Pages sirve `text/html` framable; Shopify/Supabase no servían).

- `generate.py` regenera `index.html` desde el datastore de Make 104408.
- `.github/workflows/update.yml` lo actualiza **2×/día** (7 AM y 7 PM MX) y commitea.
- GitHub Pages sirve `index.html` → URL del iframe.

Solo muestra agregados (conteos por etapa) — sin nombres ni teléfonos. Código fuente
canónico en `Spekgen-ops/scripts/f24-commissions/` (este repo es solo el host).

**Embed en GHL:** Add element → Embed → pega el iframe que apunta a la URL de Pages.
