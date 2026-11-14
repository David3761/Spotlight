You read the text of a business's website and extract facts as JSON. Only report what the text actually says; use null, false or an empty list when it doesn't say it. Don't guess and don't use outside knowledge.

The business: {name}, a {type_label} in {neighborhood}, {city}.

Fields:
- `name`: the business name as the site writes it.
- `what_it_is`: one short Romanian phrase saying what the business is, as the site describes it (e.g. „cafenea de specialitate cu boabe prăjite local”).
- `address`, `neighborhood`, `phone`, `hours`: as written on the site (hours as one line, e.g. „L–V 8:00–20:00, S–D 9:00–18:00”).
- `menu_items_or_services`: up to 15 products or services named in the text.
- `prices_present`: true when the text gives prices next to products or services.
- `menu_is_pdf_or_image`: true when the text says the menu or price list is only a PDF or an image (e.g. „descarcă meniul”), or links to one instead of listing it.
- `faq_items`: questions the site answers, with short answers, at most 8.
- `common_questions_answered`: which of these the text answers: `laptop` (working with a laptop), `wifi`, `parcare` (parking), `animale` (pets), `rezervari` (reservations).
- `has_category_pages`: true when the main products or services each have their own page or clearly separate section.
- `language`: the main language of the text as a two-letter code (`ro`, `en`, …).
- `page_with_basics`: the URL of one page that alone gives the name, what the business is, the address, the hours and the phone; null when no single page has all five.

The pages:

{pages}
