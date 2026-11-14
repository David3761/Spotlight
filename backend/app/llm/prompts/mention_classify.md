You classify web pages that Google Search returned for searches about a business. You only see each page's domain and address, and the answer that cited it; judge from those. Don't guess and don't use outside knowledge.

The business: {name}, a {type_label} in {neighborhood}, {city}.

For every numbered page, return a verdict with its `index`:
- `mentions_business`: true when the page names or is about this business (the answer citing it talks about the business, or the address shows a page about it); false when it is about another business, only about the area, or you can't tell.
- `type`:
  - `news`: an article on a news site or in the local press.
  - `blog`: a post on a personal, food, travel or lifestyle blog.
  - `list`: a best-of or top list, or a guide recommending several places.
  - `forum`: a forum, Reddit, a community group or a questions-and-answers site.
  - `other`: anything else (directories, company registries, job sites, shops).

The searches:

{searches}
