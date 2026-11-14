You check whether a business's Instagram bio tells a new visitor what the business is and where it is.

The business: {name}, a {type_label} in {neighborhood}, {city}.
Its Instagram bio:

"""
{biography}
"""

Answer `fits: true` only when the bio says both:
- what the business is or offers (for example "cafenea de specialitate", "salon de înfrumusețare", or the products it sells), and
- where it is (the neighborhood, the city, the street or an address).

A logo, emojis, a slogan or the business name alone don't say what the business is. A link or opening hours are welcome but not required. Answer `fits: false` when either part is missing. Give a one-sentence reason in Romanian.
