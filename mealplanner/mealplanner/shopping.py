"""Builds the plain-text shopping list (pastes cleanly into Apple Notes)."""

import re

AISLES: list[tuple[str, list[str]]] = [
    ("Produce", [
        "onion", "garlic", "shallot", "scallion", "green onion", "leek", "tomato", "potato", "carrot",
        "celery", "pepper", "jalapeño", "jalapeno", "lettuce", "spinach", "kale", "cabbage", "broccoli",
        "cauliflower", "zucchini", "squash", "cucumber", "mushroom", "avocado", "lemon", "lime", "orange",
        "apple", "banana", "berries", "cilantro", "parsley", "basil", "mint", "dill", "thyme", "rosemary",
        "ginger", "corn", "green beans", "asparagus", "sweet potato", "arugula", "chive", "herbs",
    ]),
    ("Meat & Seafood", [
        "chicken", "beef", "pork", "turkey", "sausage", "bacon", "ham", "lamb", "steak", "ground",
        "shrimp", "salmon", "cod", "tilapia", "fish", "tuna", "chorizo", "prosciutto",
    ]),
    ("Dairy & Eggs", [
        "milk", "butter", "cheese", "parmesan", "mozzarella", "cheddar", "feta", "cream", "yogurt",
        "sour cream", "egg", "ricotta", "half-and-half",
    ]),
    ("Bakery", ["bread", "tortilla", "buns", "bun ", "pita", "naan", "baguette", "rolls", "brioche"]),
    ("Frozen", ["frozen"]),
    ("Pantry", [
        "rice", "pasta", "noodle", "spaghetti", "penne", "flour", "sugar", "broth", "stock", "beans",
        "chickpea", "lentil", "can ", "canned", "tomato paste", "sauce", "vinegar", "soy", "honey",
        "maple", "mustard", "mayo", "ketchup", "oats", "breadcrumbs", "panko", "cornstarch", "coconut milk",
        "peanut butter", "salsa", "sriracha", "worcestershire", "quinoa", "couscous", "nuts", "almond",
    ]),
    ("Spices", [
        "cumin", "paprika", "chili powder", "oregano", "cinnamon", "nutmeg", "turmeric", "curry",
        "cayenne", "red pepper flakes", "garlic powder", "onion powder", "italian seasoning", "bay lea",
        "coriander", "seasoning",
    ]),
]

# Check spices/frozen/pantry first so "garlic powder", "frozen peas" and "chicken broth"
# don't land in produce or meat (and "flour tortillas" isn't pantry flour).
MATCH_ORDER = ["Spices", "Frozen", "Bakery", "Pantry", "Produce", "Meat & Seafood", "Dairy & Eggs"]

STAPLES = [
    "salt", "black pepper", "kosher salt", "olive oil", "vegetable oil", "canola oil", "cooking spray",
    "water", "ice",
]


def _aisle(line: str) -> str:
    low = line.lower()
    if any(re.search(rf"\b{re.escape(s)}\b", low) for s in STAPLES) and not re.search(
        r"\b(bell|jalape|poblano|chicken|beef)\b", low
    ):
        return "Probably already have"
    if "breadcrumb" in low or "panko" in low:
        return "Pantry"
    for aisle in MATCH_ORDER:
        if any(w in low for w in dict(AISLES)[aisle]):
            return aisle
    return "Other"


def build(recipes: list[dict], week_of: str) -> str:
    picked = [r for r in recipes if r["in_list"]]
    if not picked:
        return "No recipes added to the list yet."

    groups: dict[str, list[str]] = {}
    seen: set[str] = set()
    for r in picked:
        for ing in r["ingredients"]:
            key = ing.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            groups.setdefault(_aisle(ing), []).append(ing)

    order = [a for a, _ in AISLES] + ["Other", "Probably already have"]
    lines = [f"Shopping list – week of {week_of}", ""]
    lines.append("Meals:")
    lines += [f"• {r['title']}" for r in picked]
    for aisle in order:
        items = groups.get(aisle)
        if not items:
            continue
        lines += ["", aisle.upper()]
        lines += [f"- {i}" for i in items]
    lines += ["", "Recipes:"]
    lines += [f"{r['title']}: {r['url']}" for r in picked]
    return "\n".join(lines) + "\n"
