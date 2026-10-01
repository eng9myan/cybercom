"""Seed catalog data — 25 real, well-known Amman fast-food chains and 3
real hypermarkets. Grocery items (name, unit, price) for HyperMax were
pulled live from hypermax.com.jo (Dairy-Breakfast, Fruits & Vegetables,
Meat & Poultry, Beverages categories) — real brands, real Jordan JOD
prices as of the scrape. Safeway has no storefront/website in Jordan, so
per instruction its catalog duplicates HyperMax's at a different branch
location. Cozmo's catalog is hand-curated to its real published category
mix (thegroup.jo/cozmo-supermarket) — its live site wasn't scraped item
by item.

Restaurant names are real chains operating in Amman (mix confirmed via
Talabat Jordan's own listings + well-known regional/international
chains); menu items and nutrition are plausible estimates for TEST data,
not each chain's verified official figures — every seeded NutritionFact
is created with source=ESTIMATED, exactly the "AI-estimated, low
confidence until verified" path the product design already calls for.

Pure data, no Django imports — safe to import from a migration.
"""

# Amman-area coordinates, spread across real districts for realistic
# haversine/dispatch variety.
AMMAN = (31.9539, 35.9106)          # Downtown / Abdali
SWEIFIEH = (31.9539, 35.8659)
ABDOUN = (31.9454, 35.8631)
SHMEISANI = (31.9713, 35.8987)
JABAL_AMMAN = (31.9497, 35.9239)
KHALDA = (31.9642, 35.8438)

RESTAURANTS = [
    # (name, cuisine, coords, [(item, price_jod, kcal, protein_g, carbs_g, fat_g, diet_tags, ingredients)])
    ("McDonald's", "burger", AMMAN, [
        ("Big Mac", 3.25, 550, 25, 45, 30, [], ["beef", "bun", "cheese", "lettuce", "sauce"]),
        ("McChicken", 2.50, 400, 14, 40, 21, [], ["chicken", "bun", "mayo"]),
        ("French Fries Medium", 1.75, 340, 4, 44, 16, ["vegetarian"], ["potato", "oil"]),
        ("Grilled Chicken Salad", 3.50, 300, 30, 12, 14, ["gluten_free"], ["chicken", "lettuce", "tomato"]),
    ]),
    ("KFC", "chicken", SWEIFIEH, [
        ("Zinger Burger", 3.00, 450, 22, 40, 22, [], ["chicken", "bun", "spicy sauce"]),
        ("Original Recipe 2pc", 4.25, 490, 38, 18, 30, ["gluten_free"], ["chicken"]),
        ("Popcorn Chicken", 2.75, 420, 20, 25, 27, [], ["chicken", "breading"]),
        ("Coleslaw", 1.25, 150, 1, 12, 11, ["vegetarian", "gluten_free"], ["cabbage", "mayo"]),
    ]),
    ("Pizza Hut", "pizza", AMMAN, [
        ("Pepperoni Pizza Medium", 6.50, 800, 34, 84, 36, [], ["dough", "cheese", "pepperoni"]),
        ("Margherita Pizza Medium", 5.75, 680, 28, 82, 24, ["vegetarian"], ["dough", "cheese", "tomato"]),
        ("Stuffed Crust Cheese Slice", 2.00, 320, 13, 34, 14, ["vegetarian"], ["dough", "cheese"]),
        ("Garlic Bread", 1.50, 250, 6, 30, 11, ["vegetarian"], ["bread", "garlic", "butter"]),
    ]),
    ("Burger King", "burger", SHMEISANI, [
        ("Whopper", 3.50, 660, 28, 49, 40, [], ["beef", "bun", "tomato", "onion"]),
        ("Chicken Royale", 3.00, 540, 24, 45, 29, [], ["chicken", "bun", "mayo"]),
        ("Onion Rings", 1.50, 320, 4, 40, 16, ["vegetarian"], ["onion", "breading"]),
        ("Veggie Burger", 3.00, 420, 12, 50, 18, ["vegetarian"], ["veg patty", "bun"]),
    ]),
    ("Hardee's", "burger", KHALDA, [
        ("Famous Star", 3.20, 590, 24, 46, 33, [], ["beef", "bun", "cheese"]),
        ("Charbroiled Chicken Sandwich", 3.10, 480, 30, 42, 20, [], ["chicken", "bun"]),
        ("Curly Fries", 1.60, 400, 5, 48, 20, ["vegetarian"], ["potato", "spice"]),
        ("Hand-Scooped Ice Cream", 1.75, 280, 5, 34, 13, ["vegetarian"], ["milk", "sugar"]),
    ]),
    ("Domino's Pizza", "pizza", ABDOUN, [
        ("Pepperoni Passion Medium", 6.25, 780, 32, 80, 34, [], ["dough", "cheese", "pepperoni"]),
        ("Veggie Supreme Medium", 5.50, 620, 22, 78, 20, ["vegetarian"], ["dough", "cheese", "vegetables"]),
        ("Chicken Lovers Medium", 6.75, 750, 36, 76, 30, [], ["dough", "cheese", "chicken"]),
        ("Chocolate Lava Cake", 1.75, 350, 4, 45, 17, ["vegetarian"], ["chocolate", "flour"]),
    ]),
    ("Papa John's", "pizza", JABAL_AMMAN, [
        ("The Works Medium", 6.90, 760, 30, 78, 33, [], ["dough", "cheese", "assorted toppings"]),
        ("BBQ Chicken Bacon Medium", 7.10, 790, 34, 80, 32, [], ["dough", "chicken", "bacon", "bbq sauce"]),
        ("Garden Fresh Medium", 5.60, 600, 20, 76, 18, ["vegetarian"], ["dough", "vegetables", "cheese"]),
        ("Cheese Sticks", 2.25, 370, 14, 38, 18, ["vegetarian"], ["dough", "cheese"]),
    ]),
    ("Cozy Pizza", "pizza", SWEIFIEH, [
        ("Cozy Special Pizza", 5.90, 720, 28, 74, 30, [], ["dough", "cheese", "assorted toppings"]),
        ("Four Cheese Pizza", 6.10, 700, 30, 68, 32, ["vegetarian"], ["dough", "four cheeses"]),
        ("Chicken Alfredo Pasta", 4.50, 620, 32, 60, 24, [], ["pasta", "chicken", "cream sauce"]),
        ("Caesar Salad", 3.00, 320, 12, 14, 24, [], ["lettuce", "chicken", "parmesan", "dressing"]),
    ]),
    ("Sizzle Grill", "grill", AMMAN, [
        ("Mixed Grill Platter", 8.50, 780, 52, 30, 42, ["keto", "gluten_free"], ["lamb", "chicken", "beef"]),
        ("Grilled Chicken Skewers", 5.50, 420, 44, 8, 20, ["keto", "gluten_free"], ["chicken"]),
        ("Kafta Platter", 6.00, 540, 34, 20, 34, ["gluten_free"], ["beef", "onion", "parsley"]),
        ("Hummus Side", 1.50, 180, 6, 16, 10, ["vegan", "vegetarian", "gluten_free"], ["chickpeas", "tahini"]),
    ]),
    ("WOK U LIKE", "asian", SHMEISANI, [
        ("Chicken Fried Rice", 4.00, 560, 24, 70, 18, [], ["rice", "chicken", "egg", "vegetables"]),
        ("Beef Noodles Stir Fry", 4.50, 610, 28, 66, 22, [], ["noodles", "beef", "vegetables"]),
        ("Vegetable Spring Rolls", 2.25, 260, 5, 32, 12, ["vegan", "vegetarian"], ["cabbage", "carrot", "wrapper"]),
        ("Sweet & Sour Chicken", 4.75, 590, 26, 62, 20, [], ["chicken", "pineapple", "sauce"]),
    ]),
    ("Black Stacks", "burger", ABDOUN, [
        ("Truffle Chicken Sandwich", 4.50, 620, 28, 48, 32, [], ["chicken", "truffle sauce", "black bun"]),
        ("Black Stacks Burger", 4.75, 680, 30, 46, 38, [], ["beef", "special sauce", "black bun"]),
        ("Black Fries", 2.00, 380, 5, 46, 18, ["vegetarian"], ["potato", "seasoning"]),
        ("Brown Bread Chicken Wrap", 3.75, 480, 26, 44, 20, [], ["chicken", "brown bread"]),
    ]),
    ("Hashem Restaurant", "local", JABAL_AMMAN, [
        ("Falafel Sandwich", 0.75, 320, 10, 40, 14, ["vegan", "vegetarian"], ["chickpeas", "bread"]),
        ("Hummus Plate", 1.25, 220, 8, 20, 12, ["vegan", "vegetarian", "gluten_free"], ["chickpeas", "tahini"]),
        ("Foul Medames", 1.00, 260, 12, 34, 8, ["vegan", "vegetarian"], ["fava beans", "olive oil"]),
        ("Mixed Plate (Falafel + Hummus + Foul)", 2.25, 620, 24, 68, 24, ["vegetarian"], ["chickpeas", "fava beans", "bread"]),
    ]),
    ("Sufra", "jordanian", JABAL_AMMAN, [
        ("Mansaf", 9.50, 950, 48, 60, 56, ["gluten_free"], ["lamb", "rice", "jameed yogurt"]),
        ("Maqluba", 6.50, 720, 30, 80, 26, ["gluten_free"], ["rice", "chicken", "eggplant"]),
        ("Musakhan Rolls", 4.00, 480, 22, 44, 22, [], ["chicken", "sumac", "onion", "bread"]),
        ("Kunafa Slice", 2.50, 420, 10, 50, 20, ["vegetarian"], ["cheese", "semolina", "syrup"]),
    ]),
    ("Shawarma AlDayaa", "shawarma", AMMAN, [
        ("Chicken Shawarma Sandwich", 1.25, 380, 22, 36, 16, [], ["chicken", "bread", "garlic sauce"]),
        ("Beef Shawarma Sandwich", 1.50, 420, 24, 34, 20, [], ["beef", "bread", "tahini"]),
        ("Shawarma Plate", 3.50, 620, 40, 46, 28, ["gluten_free"], ["chicken", "rice", "salad"]),
        ("Garlic Sauce Side", 0.50, 140, 0, 2, 15, ["vegetarian", "gluten_free"], ["garlic", "oil"]),
    ]),
    ("Reem Al Bawadi", "arabic", SWEIFIEH, [
        ("Grilled Mixed Meat", 9.00, 820, 54, 22, 48, ["keto", "gluten_free"], ["lamb", "chicken", "beef"]),
        ("Freekeh with Chicken", 6.00, 640, 32, 70, 20, [], ["freekeh", "chicken"]),
        ("Fattoush Salad", 2.50, 240, 5, 26, 12, ["vegan", "vegetarian"], ["lettuce", "bread chips", "sumac"]),
        ("Warak Enab (Stuffed Grape Leaves)", 3.00, 380, 8, 50, 16, ["vegan", "vegetarian"], ["grape leaves", "rice"]),
    ]),
    ("Zaatar w Zeit", "lebanese", SHMEISANI, [
        ("Manakeesh Zaatar", 1.25, 320, 7, 42, 14, ["vegan", "vegetarian"], ["dough", "zaatar", "olive oil"]),
        ("Cheese Manakeesh", 1.50, 380, 14, 38, 18, ["vegetarian"], ["dough", "cheese"]),
        ("Halloumi Wrap", 2.75, 460, 18, 40, 24, ["vegetarian"], ["halloumi", "bread", "vegetables"]),
        ("Chicken Taouk Wrap", 3.25, 500, 28, 42, 22, [], ["chicken", "garlic sauce", "bread"]),
    ]),
    ("Abu Jbara", "shawarma", JABAL_AMMAN, [
        ("Special Shawarma Sandwich", 1.75, 450, 26, 36, 22, [], ["beef", "chicken", "bread"]),
        ("Shawarma Plate Large", 4.00, 720, 46, 50, 32, ["gluten_free"], ["beef", "chicken", "rice"]),
        ("Fries with Cheese", 2.00, 460, 12, 48, 24, ["vegetarian"], ["potato", "cheese"]),
        ("Pickles Side", 0.35, 20, 0, 4, 0, ["vegan", "vegetarian", "gluten_free"], ["cucumber", "vinegar"]),
    ]),
    ("Subway", "sandwiches", ABDOUN, [
        ("Chicken Teriyaki 6-inch", 2.75, 370, 24, 50, 6, [], ["chicken", "bread", "teriyaki sauce"]),
        ("Veggie Delite 6-inch", 2.00, 230, 9, 44, 3, ["vegan", "vegetarian"], ["bread", "vegetables"]),
        ("Tuna 6-inch", 2.90, 430, 20, 42, 20, [], ["tuna", "mayo", "bread"]),
        ("Turkey Breast 6-inch", 2.60, 280, 18, 46, 4, [], ["turkey", "bread"]),
    ]),
    ("Krispy Kreme", "dessert", AMMAN, [
        ("Original Glazed Doughnut", 0.90, 190, 2, 22, 11, ["vegetarian"], ["dough", "glaze"]),
        ("Chocolate Iced Doughnut", 1.00, 250, 2, 33, 12, ["vegetarian"], ["dough", "chocolate"]),
        ("Doughnut Dozen", 8.50, 2280, 24, 264, 132, ["vegetarian"], ["dough", "glaze"]),
        ("Iced Coffee", 2.25, 180, 3, 28, 6, ["vegetarian"], ["coffee", "milk", "sugar"]),
    ]),
    ("Baskin Robbins", "dessert", SWEIFIEH, [
        ("Double Scoop Cup", 2.50, 340, 6, 40, 17, ["vegetarian", "gluten_free"], ["milk", "cream", "sugar"]),
        ("Milkshake Regular", 3.25, 480, 9, 60, 20, ["vegetarian"], ["ice cream", "milk"]),
        ("Sundae Classic", 3.00, 420, 7, 52, 18, ["vegetarian", "gluten_free"], ["ice cream", "syrup", "nuts"]),
        ("Sorbet Scoop", 2.25, 160, 0, 40, 0, ["vegan", "vegetarian", "gluten_free"], ["fruit", "sugar"]),
    ]),
    ("Costa Coffee", "coffee", SHMEISANI, [
        ("Cappuccino Medium", 2.25, 120, 6, 10, 6, ["vegetarian", "gluten_free"], ["espresso", "milk"]),
        ("Flat White", 2.50, 140, 7, 10, 7, ["vegetarian", "gluten_free"], ["espresso", "milk"]),
        ("Chocolate Muffin", 2.00, 380, 5, 50, 18, ["vegetarian"], ["flour", "chocolate", "sugar"]),
        ("Iced Latte", 2.75, 180, 6, 22, 5, ["vegetarian", "gluten_free"], ["espresso", "milk", "ice"]),
    ]),
    ("Starbucks", "coffee", ABDOUN, [
        ("Caffe Latte Grande", 2.85, 190, 10, 18, 7, ["vegetarian", "gluten_free"], ["espresso", "milk"]),
        ("Caramel Macchiato Grande", 3.10, 250, 8, 34, 7, ["vegetarian"], ["espresso", "milk", "caramel"]),
        ("Butter Croissant", 2.25, 340, 6, 36, 18, ["vegetarian"], ["flour", "butter"]),
        ("Cold Brew", 2.50, 5, 0, 1, 0, ["vegan", "vegetarian", "gluten_free"], ["coffee"]),
    ]),
    ("Tim Hortons", "coffee", KHALDA, [
        ("Original Blend Coffee", 1.75, 10, 0, 1, 0, ["vegan", "vegetarian", "gluten_free"], ["coffee"]),
        ("Boston Cream Doughnut", 1.10, 260, 3, 34, 13, ["vegetarian"], ["dough", "cream"]),
        ("Bagel with Cream Cheese", 2.10, 380, 12, 54, 12, ["vegetarian"], ["bagel", "cream cheese"]),
        ("Iced Capp", 2.60, 330, 5, 48, 13, ["vegetarian"], ["coffee", "cream", "sugar"]),
    ]),
    ("Chili's", "american", AMMAN, [
        ("Classic Bacon Burger", 6.50, 780, 38, 44, 46, [], ["beef", "bacon", "bun"]),
        ("Baby Back Ribs Half Rack", 10.50, 900, 52, 40, 54, ["gluten_free"], ["pork ribs", "bbq sauce"]),
        ("Southwestern Chicken Salad", 6.00, 480, 34, 30, 24, ["gluten_free"], ["chicken", "beans", "corn"]),
        ("Molten Chocolate Cake", 3.00, 460, 6, 62, 22, ["vegetarian"], ["chocolate", "flour"]),
    ]),
    ("Automatic Restaurant", "lebanese", JABAL_AMMAN, [
        ("Chicken Taouk Plate", 4.50, 560, 36, 42, 24, ["gluten_free"], ["chicken", "rice", "garlic sauce"]),
        ("Mixed Grill Plate", 7.50, 780, 50, 30, 44, ["keto", "gluten_free"], ["lamb", "chicken", "kafta"]),
        ("Tabbouleh Salad", 2.25, 180, 4, 24, 8, ["vegan", "vegetarian"], ["parsley", "bulgur", "tomato"]),
        ("Kibbeh (4 pieces)", 3.00, 420, 16, 30, 24, [], ["bulgur", "meat", "onion"]),
    ]),
]

# ── Hypermarkets ─────────────────────────────────────────────────────────
# HyperMax items scraped live from hypermax.com.jo on 2026-09-26 (Dairy-
# Breakfast, Fruits & Vegetables, Meat & Poultry, Beverages category
# pages) — real brands + real JOD prices. Safeway duplicates this catalog
# at a different branch, per instruction (no Safeway storefront exists in
# Jordan to scrape). Cozmo's list is hand-curated to its real category
# mix, not item-by-item scraped.
HYPERMAX_PRODUCTS = [
    # (name, unit, price_jod, category, diet_tags)
    ("American Heritage Mozzarella String", "28 Gram", 0.38, "Dairy & Eggs", ["vegetarian"]),
    ("Hammoudeh Cheese Laziza", "450 Gram", 2.60, "Dairy & Eggs", ["vegetarian"]),
    ("Almarai Spread Cream Cheese", "500 Gram", 4.00, "Dairy & Eggs", ["vegetarian"]),
    ("Puck Spread Cream Cheese", "500 Gram", 4.07, "Dairy & Eggs", ["vegetarian"]),
    ("Almarai Cheese Triangle 16 Pieces", "240 Gram", 1.65, "Dairy & Eggs", ["vegetarian"]),
    ("5 Cows Cheddar Cheese Slices", "200 Gram", 1.19, "Dairy & Eggs", ["vegetarian"]),
    ("Rhodes White Feta Cheese", "500 Gram", 1.65, "Dairy & Eggs", ["vegetarian"]),
    ("Hammoudeh Akawi Cheese", "450 Gram", 3.80, "Dairy & Eggs", ["vegetarian"]),
    ("Hy Top Kashkawane Cheese", "700 Gram", 6.71, "Dairy & Eggs", ["vegetarian"]),
    ("Moravia Parmesan Italy Cheese", "500 Gram", 9.00, "Dairy & Eggs", ["vegetarian"]),
    ("Ecuador Banana", "1 Kg", 0.88, "Fruits & Vegetables", ["vegan", "vegetarian", "gluten_free"]),
    ("Mango", "1 Kg", 0.99, "Fruits & Vegetables", ["vegan", "vegetarian", "gluten_free"]),
    ("Potato", "1 Kg", 0.49, "Fruits & Vegetables", ["vegan", "vegetarian", "gluten_free"]),
    ("Lemon Local", "1 Kg", 0.69, "Fruits & Vegetables", ["vegan", "vegetarian", "gluten_free"]),
    ("Onion Golden", "500 Gram", 0.22, "Fruits & Vegetables", ["vegan", "vegetarian", "gluten_free"]),
    ("Avocado", "1 Kg", 2.99, "Fruits & Vegetables", ["vegan", "vegetarian", "keto", "gluten_free"]),
    ("Cucumber Local", "1 Kg", 0.47, "Fruits & Vegetables", ["vegan", "vegetarian", "gluten_free"]),
    ("Tomato Greenhouse", "1 Kg", 0.44, "Fruits & Vegetables", ["vegan", "vegetarian", "gluten_free"]),
    ("Apple Royal", "500 Gram", 0.65, "Fruits & Vegetables", ["vegan", "vegetarian", "gluten_free"]),
    ("Carrot", "500 Gram", 0.40, "Fruits & Vegetables", ["vegan", "vegetarian", "gluten_free"]),
    ("Spinach", "1 Kg", 0.99, "Fruits & Vegetables", ["vegan", "vegetarian", "keto", "gluten_free"]),
    ("Broccoli", "500 Gram", 0.99, "Fruits & Vegetables", ["vegan", "vegetarian", "keto", "gluten_free"]),
    ("Al Khair Fresh Chicken", "1.2 Kg", 1.79, "Meat & Poultry", ["gluten_free"]),
    ("Alkhair Fresh Chicken Breast Fillet", "900 Gram", 3.59, "Meat & Poultry", ["keto", "gluten_free"]),
    ("Alwataniya Leg Chicken Fresh", "500 Gram", 0.90, "Meat & Poultry", ["gluten_free"]),
    ("Brazil Beef Kofta", "1 Kg", 7.49, "Meat & Poultry", ["gluten_free"]),
    ("Brazil Beef Mince And Lamb", "500 Gram", 3.75, "Meat & Poultry", ["keto", "gluten_free"]),
    ("Nabil Crispy Chicken Fillet", "900 Gram", 3.69, "Meat & Poultry", []),
    ("Siniora Beef Meatballs", "400 Gram", 1.85, "Meat & Poultry", ["gluten_free"]),
    ("Sadia Chicken Franks 10 Pieces", "340 Gram", 0.75, "Meat & Poultry", []),
    ("Siniora Beef Burger Jumbo", "1 Kg", 4.75, "Meat & Poultry", []),
    ("Fresh Shrimp 40/50", "500 Gram", 5.50, "Meat & Poultry", ["keto", "gluten_free"]),
    ("Nescafe My Cup 3in1 Classic 35pc", "20 Gram", 4.45, "Beverages", ["vegetarian"]),
    ("Marouf Coffee Medium Turkish Cardamom", "250 Gram", 3.25, "Beverages", ["vegan", "vegetarian", "gluten_free"]),
    ("Pepsi Carbonated Drink", "1.95 Liter", 0.85, "Beverages", ["vegan", "vegetarian"]),
    ("Matrix Cola Carbonated Drink", "250 Ml", 0.25, "Beverages", ["vegan", "vegetarian"]),
    ("Kinza Soda Water", "250 Ml", 0.35, "Beverages", ["vegan", "vegetarian", "gluten_free"]),
    ("Ginseng Cranberry Sugar Free Drink", "300 Ml", 0.70, "Beverages", ["vegan", "vegetarian", "keto", "gluten_free"]),
]

COZMO_PRODUCTS = [
    # Hand-curated to Cozmo's real published premium/specialty category
    # mix (fresh food, gourmet groceries, imported/local specialty items).
    ("Almarai Fresh Milk Full Fat", "1 Liter", 1.10, "Dairy & Eggs", ["vegetarian", "gluten_free"]),
    ("Nadec Greek Yogurt", "500 Gram", 2.20, "Dairy & Eggs", ["vegetarian", "gluten_free"]),
    ("Free-Range Eggs 12 Pack", "12 Pieces", 2.75, "Dairy & Eggs", ["vegetarian", "keto", "gluten_free"]),
    ("Organic Baby Spinach", "200 Gram", 1.80, "Fruits & Vegetables", ["vegan", "vegetarian", "keto", "gluten_free"]),
    ("Imported Blueberries", "125 Gram", 3.50, "Fruits & Vegetables", ["vegan", "vegetarian", "gluten_free"]),
    ("Avocado Premium", "1 Piece", 1.20, "Fruits & Vegetables", ["vegan", "vegetarian", "keto", "gluten_free"]),
    ("Grass-Fed Beef Ribeye", "500 Gram", 9.90, "Meat & Poultry", ["keto", "gluten_free"]),
    ("Organic Free-Range Chicken Breast", "500 Gram", 4.50, "Meat & Poultry", ["keto", "gluten_free"]),
    ("Norwegian Salmon Fillet", "300 Gram", 6.80, "Meat & Poultry", ["keto", "gluten_free"]),
    ("Sourdough Artisan Bread", "500 Gram", 2.90, "Bakery", ["vegan", "vegetarian"]),
    ("Gluten-Free Multigrain Bread", "400 Gram", 3.40, "Bakery", ["vegan", "vegetarian", "gluten_free"]),
    ("Kirkland Almonds Roasted", "450 Gram", 5.90, "Snacks", ["vegan", "vegetarian", "keto", "gluten_free"]),
    ("San Pellegrino Sparkling Water", "750 Ml", 1.60, "Beverages", ["vegan", "vegetarian", "gluten_free"]),
    ("Lavazza Ground Coffee", "250 Gram", 4.80, "Beverages", ["vegan", "vegetarian", "gluten_free"]),
    ("Kevala Organic Coconut Oil", "500 Ml", 4.20, "Cooking essentials", ["vegan", "vegetarian", "keto", "gluten_free"]),
]

# City-level coords for hypermarket branches.
HYPERMAX_LOCATION = SHMEISANI
SAFEWAY_LOCATION = KHALDA
COZMO_LOCATION = ABDOUN
