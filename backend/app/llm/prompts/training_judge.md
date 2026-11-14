You compare what an AI assistant said about a business, without searching the internet, with the business's real details from Google. Judge only from the answers and the details below; don't use outside knowledge.

The business: {name}, a {type_label} in {neighborhood}, {city}.
Its details on Google:
{facts}

The assistant was asked „Ce știi despre {name} din {neighborhood}, {city}?” three times:

{about_answers}

It was also asked to recommend a few businesses of this type in {neighborhood}, three times:

{recommend_answers}

Return:
- `knows_business`: three booleans, one per answer to the first question, in order. True when that answer describes this specific business (what it is, where it is, what it offers); false when it says it doesn't know it, asks for more details, gives generic advice, or describes the area or a different business.
- `correct_type_and_area`: true when at least one answer correctly says both what kind of business it is and that it is in {neighborhood} or {city}.
- `wrong_facts`: each statement the answers make about this business that contradicts its details on Google (a different address, type, phone, opening hours, or saying it closed), as a short Romanian sentence. Leave out details Google doesn't list and anything the answers merely don't mention. Empty when there are none.
