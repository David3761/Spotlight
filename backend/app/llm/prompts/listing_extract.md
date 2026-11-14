You read the text of a page on {platform} and extract a business's contact details as JSON. Only report what the text actually says; use null when it doesn't say it. Don't guess and don't use outside knowledge.

The business we're looking for: {name}, a {type_label} in {neighborhood}, {city}. The page was linked from the business's own website.

Fields:
- `is_business_page`: true when the page is this business's own page on {platform} (its profile, listing or menu); false for a home page, a search or category page, a login wall, an error page or another business's page.
- `name`: the business name as the page writes it.
- `address`: the address as the page writes it.
- `phone`: the phone number as the page writes it.
- `hours`: the opening hours as one line, e.g. „L–V 8:00–20:00, S–D 9:00–18:00”.

The page ({url}):

{page}
