"""
Synthetic Supermarket Data Generator — V2 (Expanded)
Generates realistic datasets: products, customers, sales, inventory, suppliers
200+ products, 2000 customers, 50k transactions, 15 categories
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random
import hashlib

np.random.seed(42)
random.seed(42)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

# ──────────────────────────── PRODUCTS (200+ across 15 categories) ────────────────────────────

CATEGORIES = {
    "Dairy": [
        ("Whole Milk 1L", 3.49, 7), ("Skim Milk 1L", 3.29, 7), ("Cheddar Cheese 200g", 4.99, 14),
        ("Greek Yogurt 500g", 5.49, 10), ("Butter 250g", 3.99, 21), ("Cream Cheese 200g", 4.29, 14),
        ("Mozzarella 300g", 5.99, 10), ("Cottage Cheese 250g", 3.79, 10), ("Heavy Cream 500ml", 4.49, 7),
        ("Parmesan Wedge 150g", 6.99, 30), ("Flavored Yogurt 4pk", 4.29, 14), ("Goat Cheese 150g", 5.49, 14),
        ("Almond Milk 1L", 4.49, 14), ("Oat Milk 1L", 4.99, 14),
    ],
    "Bakery": [
        ("White Bread Loaf", 2.49, 5), ("Whole Wheat Bread", 2.99, 5), ("Croissants 4pk", 4.49, 3),
        ("Bagels 6pk", 3.99, 4), ("Sourdough Loaf", 4.99, 5), ("Muffins 4pk", 5.49, 3),
        ("Dinner Rolls 8pk", 3.49, 4), ("Ciabatta Bread", 3.99, 3), ("Rye Bread Loaf", 3.49, 5),
        ("Pita Bread 6pk", 2.99, 5), ("Tortillas 10pk", 3.29, 7), ("Brioche Buns 4pk", 4.99, 3),
        ("Banana Bread Loaf", 5.99, 4), ("Focaccia Bread", 4.49, 3),
    ],
    "Beverages": [
        ("Orange Juice 1L", 3.99, 14), ("Cola 2L", 2.49, 180), ("Sparkling Water 1L", 1.99, 365),
        ("Green Tea 20pk", 4.49, 365), ("Coffee Beans 500g", 9.99, 180), ("Energy Drink 250ml", 2.99, 365),
        ("Apple Juice 1L", 3.49, 14), ("Coconut Water 500ml", 3.29, 180), ("Lemonade 1L", 2.99, 14),
        ("Iced Tea 1L", 2.79, 14), ("Kombucha 330ml", 3.99, 30), ("Protein Shake 4pk", 8.99, 180),
        ("Craft Root Beer 330ml", 2.49, 365), ("Mineral Water 6pk", 5.99, 365),
    ],
    "Snacks": [
        ("Potato Chips 150g", 3.49, 90), ("Chocolate Bar 100g", 2.99, 180), ("Mixed Nuts 200g", 5.99, 120),
        ("Granola Bars 6pk", 4.49, 180), ("Popcorn 100g", 2.49, 90), ("Pretzels 200g", 3.29, 120),
        ("Trail Mix 250g", 5.49, 120), ("Rice Cakes 12pk", 3.29, 180), ("Cheese Crackers 200g", 3.79, 90),
        ("Dark Chocolate 85% 100g", 4.99, 365), ("Fruit Snacks 10pk", 4.29, 180), ("Tortilla Chips 200g", 3.49, 90),
        ("Protein Bars 4pk", 6.99, 180), ("Veggie Straws 150g", 3.99, 90),
    ],
    "Produce": [
        ("Bananas 1kg", 1.99, 5), ("Apples 1kg", 3.49, 10), ("Tomatoes 500g", 2.99, 7),
        ("Lettuce Head", 1.99, 5), ("Carrots 1kg", 2.49, 14), ("Potatoes 2kg", 3.99, 21),
        ("Onions 1kg", 2.29, 21), ("Avocados 3pk", 4.99, 5), ("Bell Peppers 3pk", 3.99, 7),
        ("Cucumbers 2pk", 2.49, 7), ("Spinach 250g", 3.49, 5), ("Broccoli Head", 2.99, 7),
        ("Sweet Potatoes 1kg", 3.49, 14), ("Mushrooms 200g", 3.29, 5), ("Garlic 3pk", 1.99, 21),
        ("Strawberries 250g", 4.99, 3), ("Blueberries 125g", 3.99, 5), ("Lemons 6pk", 2.99, 14),
    ],
    "Meat": [
        ("Chicken Breast 500g", 7.99, 3), ("Ground Beef 500g", 8.49, 3), ("Pork Chops 400g", 6.99, 3),
        ("Salmon Fillet 300g", 11.99, 2), ("Turkey Slices 200g", 5.49, 5), ("Bacon 200g", 5.99, 7),
        ("Italian Sausage 4pk", 7.49, 5), ("Lamb Chops 400g", 12.99, 3), ("Shrimp 300g", 9.99, 2),
        ("Deli Ham 200g", 4.99, 7), ("Beef Steak 300g", 13.99, 3), ("Chicken Wings 500g", 6.49, 3),
        ("Ground Turkey 500g", 7.99, 3), ("Tilapia Fillets 400g", 8.49, 2),
    ],
    "Frozen": [
        ("Frozen Pizza", 5.99, 180), ("Ice Cream 1L", 6.49, 365), ("Frozen Vegetables 500g", 3.49, 365),
        ("Fish Sticks 400g", 4.99, 180), ("Frozen Berries 300g", 5.49, 365), ("Frozen Fries 1kg", 3.99, 365),
        ("Frozen Burritos 4pk", 5.99, 180), ("Frozen Waffles 8pk", 4.49, 180), ("Ice Cream Bars 6pk", 7.49, 365),
        ("Frozen Dumplings 400g", 6.49, 180), ("Frozen Mac & Cheese", 4.99, 180), ("Frozen Chicken Nuggets 500g", 6.99, 180),
    ],
    "Household": [
        ("Paper Towels 6pk", 7.99, 730), ("Dish Soap 500ml", 3.49, 730), ("Laundry Detergent 1L", 8.99, 730),
        ("Trash Bags 30pk", 5.99, 730), ("Sponges 4pk", 2.99, 730), ("All-Purpose Cleaner 750ml", 4.49, 730),
        ("Toilet Paper 12pk", 9.99, 730), ("Aluminum Foil 30m", 3.99, 730), ("Plastic Wrap 60m", 3.49, 730),
        ("Glass Cleaner 750ml", 3.99, 730), ("Bleach 1L", 2.99, 730), ("Dryer Sheets 80pk", 4.99, 730),
    ],
    "Personal Care": [
        ("Shampoo 400ml", 5.99, 730), ("Conditioner 400ml", 5.99, 730), ("Body Wash 500ml", 4.99, 730),
        ("Toothpaste 150g", 3.49, 730), ("Deodorant 75g", 4.49, 730), ("Hand Soap 250ml", 2.99, 730),
        ("Moisturizer 200ml", 7.99, 730), ("Sunscreen SPF50 100ml", 9.99, 730), ("Razor Blades 4pk", 8.99, 730),
        ("Lip Balm 2pk", 2.99, 730), ("Dental Floss 50m", 2.49, 730), ("Face Wash 150ml", 6.99, 730),
    ],
    "Baby & Kids": [
        ("Diapers Size 3 40pk", 14.99, 730), ("Baby Wipes 80pk", 3.99, 730), ("Baby Formula 400g", 19.99, 365),
        ("Baby Food Puree 4pk", 4.99, 180), ("Sippy Cup", 5.99, 730), ("Baby Lotion 200ml", 4.99, 730),
        ("Kids Cereal 300g", 4.49, 180), ("Juice Boxes 8pk", 3.99, 180), ("Animal Crackers 200g", 3.29, 180),
        ("Kids Toothpaste 75g", 2.99, 730),
    ],
    "Pet Supplies": [
        ("Dog Food 2kg", 12.99, 365), ("Cat Food 1.5kg", 10.99, 365), ("Dog Treats 200g", 4.99, 180),
        ("Cat Litter 5kg", 8.99, 730), ("Pet Shampoo 250ml", 5.99, 730), ("Dog Chew Toys", 3.99, 730),
        ("Cat Treats 100g", 3.49, 180), ("Pet Vitamins 60ct", 9.99, 365), ("Dog Leash", 7.99, 730),
        ("Cat Scratching Post", 14.99, 730),
    ],
    "Condiments & Sauces": [
        ("Ketchup 500ml", 2.99, 180), ("Mustard 250ml", 2.49, 180), ("Mayonnaise 400ml", 3.99, 180),
        ("Soy Sauce 250ml", 3.49, 365), ("Hot Sauce 150ml", 3.99, 365), ("BBQ Sauce 500ml", 3.99, 180),
        ("Olive Oil 500ml", 7.99, 365), ("Balsamic Vinegar 250ml", 5.99, 365), ("Salad Dressing 350ml", 3.49, 120),
        ("Pasta Sauce 500ml", 3.99, 365), ("Ranch Dressing 350ml", 3.49, 120), ("Maple Syrup 250ml", 6.99, 365),
    ],
    "Canned Goods": [
        ("Canned Tomatoes 400g", 1.99, 730), ("Canned Beans 400g", 1.49, 730), ("Canned Corn 340g", 1.79, 730),
        ("Canned Tuna 170g", 2.49, 730), ("Canned Soup 400ml", 2.99, 730), ("Canned Chickpeas 400g", 1.69, 730),
        ("Coconut Milk 400ml", 2.49, 730), ("Canned Pineapple 400g", 2.29, 730), ("Canned Sardines 120g", 2.99, 730),
        ("Canned Peaches 400g", 2.49, 730),
    ],
    "Pasta & Grains": [
        ("Spaghetti 500g", 1.99, 730), ("Penne 500g", 1.99, 730), ("Brown Rice 1kg", 3.49, 730),
        ("White Rice 2kg", 4.99, 730), ("Quinoa 500g", 5.99, 730), ("Oats 1kg", 3.99, 365),
        ("Couscous 500g", 2.99, 730), ("Egg Noodles 500g", 2.49, 365), ("Fusilli 500g", 1.99, 730),
        ("Basmati Rice 1kg", 4.49, 730), ("Flour 1kg", 1.99, 730), ("Cornmeal 500g", 2.49, 730),
    ],
    "Health & Wellness": [
        ("Multivitamins 60ct", 12.99, 730), ("Vitamin C 1000mg 30ct", 7.99, 730),
        ("Fish Oil 60ct", 9.99, 730), ("Probiotics 30ct", 14.99, 365),
        ("Protein Powder 500g", 19.99, 365), ("Electrolyte Powder 20pk", 8.99, 365),
        ("Melatonin 5mg 30ct", 5.99, 730), ("Zinc 50mg 60ct", 6.99, 730),
        ("Collagen Powder 300g", 16.99, 365), ("Turmeric Capsules 60ct", 11.99, 730),
    ],
}

SUPPLIERS = [
    {"name": "FreshFarms Co.", "email": "orders@freshfarms.com", "lead_time": 3, "reliability": 0.95},
    {"name": "Global Foods Inc.", "email": "supply@globalfoods.com", "lead_time": 5, "reliability": 0.88},
    {"name": "Daily Dairy Ltd.", "email": "sales@dailydairy.com", "lead_time": 2, "reliability": 0.97},
    {"name": "Baker's Best", "email": "hello@bakersbest.com", "lead_time": 1, "reliability": 0.93},
    {"name": "Pacific Beverages", "email": "orders@pacificbev.com", "lead_time": 4, "reliability": 0.91},
    {"name": "SnackMaster Corp.", "email": "supply@snackmaster.com", "lead_time": 5, "reliability": 0.86},
    {"name": "Green Valley Produce", "email": "fresh@greenvalley.com", "lead_time": 1, "reliability": 0.96},
    {"name": "Prime Meats", "email": "orders@primemeats.com", "lead_time": 2, "reliability": 0.94},
    {"name": "Arctic Frozen Foods", "email": "supply@arcticfoods.com", "lead_time": 4, "reliability": 0.89},
    {"name": "HomeClean Supplies", "email": "sales@homeclean.com", "lead_time": 7, "reliability": 0.85},
    {"name": "Nature's Harvest", "email": "info@naturesharvest.com", "lead_time": 3, "reliability": 0.92},
    {"name": "Quality Foods Dist.", "email": "orders@qualityfoods.com", "lead_time": 4, "reliability": 0.90},
    {"name": "BabyCare Direct", "email": "supply@babycare.com", "lead_time": 5, "reliability": 0.87},
    {"name": "PetPals Wholesale", "email": "orders@petpals.com", "lead_time": 6, "reliability": 0.84},
    {"name": "WellLife Nutrition", "email": "sales@welllife.com", "lead_time": 5, "reliability": 0.91},
]

# Map categories to preferred suppliers
CATEGORY_SUPPLIERS = {
    "Dairy": ["Daily Dairy Ltd.", "FreshFarms Co.", "Nature's Harvest"],
    "Bakery": ["Baker's Best", "Quality Foods Dist."],
    "Beverages": ["Pacific Beverages", "Global Foods Inc."],
    "Snacks": ["SnackMaster Corp.", "Quality Foods Dist."],
    "Produce": ["Green Valley Produce", "FreshFarms Co.", "Nature's Harvest"],
    "Meat": ["Prime Meats", "FreshFarms Co."],
    "Frozen": ["Arctic Frozen Foods", "Global Foods Inc."],
    "Household": ["HomeClean Supplies", "Quality Foods Dist."],
    "Personal Care": ["HomeClean Supplies", "WellLife Nutrition"],
    "Baby & Kids": ["BabyCare Direct", "Quality Foods Dist."],
    "Pet Supplies": ["PetPals Wholesale", "Quality Foods Dist."],
    "Condiments & Sauces": ["Global Foods Inc.", "Nature's Harvest"],
    "Canned Goods": ["Global Foods Inc.", "Quality Foods Dist."],
    "Pasta & Grains": ["Global Foods Inc.", "Nature's Harvest"],
    "Health & Wellness": ["WellLife Nutrition", "Nature's Harvest"],
}


def generate_suppliers():
    suppliers = []
    for i, s in enumerate(SUPPLIERS, 1):
        suppliers.append({
            "supplier_id": f"SUP{i:03d}",
            "name": s["name"],
            "contact_email": s["email"],
            "lead_time_days": s["lead_time"],
            "reliability_score": round(s["reliability"] + np.random.uniform(-0.03, 0.03), 2),
        })
    return pd.DataFrame(suppliers)


def generate_products():
    products = []
    pid = 1
    for category, items in CATEGORIES.items():
        possible_suppliers = CATEGORY_SUPPLIERS.get(category, ["Quality Foods Dist."])
        for name, price, shelf_life in items:
            products.append({
                "product_id": f"P{pid:04d}",
                "name": name,
                "category": category,
                "price": round(price + np.random.uniform(-0.30, 0.30), 2),
                "cost": round(price * np.random.uniform(0.45, 0.65), 2),
                "supplier": random.choice(possible_suppliers),
                "shelf_life_days": shelf_life,
                "unit": random.choice(["piece", "pack", "kg", "liter"]),
            })
            pid += 1
    return pd.DataFrame(products)


# ──────────────────────────── CUSTOMERS ────────────────────────────

FIRST_NAMES = [
    "James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda",
    "David", "Elizabeth", "William", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
    "Thomas", "Sarah", "Christopher", "Karen", "Daniel", "Lisa", "Matthew", "Nancy",
    "Anthony", "Betty", "Mark", "Margaret", "Andrew", "Sandra", "Steven", "Ashley",
    "Paul", "Dorothy", "Joshua", "Kimberly", "Kenneth", "Emily", "Kevin", "Donna",
    "Brian", "Michelle", "George", "Carol", "Timothy", "Amanda", "Ronald", "Melissa",
    "Edward", "Deborah", "Jason", "Stephanie", "Jeffrey", "Rebecca", "Ryan", "Sharon",
    "Jacob", "Laura", "Gary", "Cynthia", "Nicholas", "Kathleen", "Eric", "Amy",
    "Jonathan", "Angela", "Stephen", "Shirley", "Larry", "Anna", "Justin", "Brenda",
    "Raymond", "Emma", "Samuel", "Olivia", "Benjamin", "Sophia", "Gregory", "Isabella",
    "Frank", "Mia", "Alexander", "Charlotte", "Patrick", "Amelia", "Jack", "Harper",
    "Dennis", "Evelyn", "Jerry", "Abigail", "Tyler", "Ella", "Aaron", "Scarlett",
    "Henry", "Grace", "Douglas", "Chloe", "Peter", "Victoria", "Adam", "Riley",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
    "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson",
    "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker",
    "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores",
    "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz", "Parker",
    "Cruz", "Edwards", "Collins", "Reyes", "Stewart", "Morris", "Morales", "Murphy",
]

ZIP_CODES = [
    "10001", "10002", "10003", "10010", "10011", "10012", "10013", "10014",
    "10016", "10017", "10018", "10019", "10020", "10021", "10022", "10023",
    "10024", "10025", "10026", "10027", "10028", "10029", "10030", "10031",
]

SECTIONS = ["Produce", "Dairy", "Meat", "Bakery", "Beverages", "Frozen", "Snacks", "Household"]


def generate_customers(n=2000):
    customers = []
    for i in range(1, n + 1):
        age = int(np.random.normal(42, 15))
        age = max(18, min(80, age))
        tier = np.random.choice(
            ["Bronze", "Silver", "Gold", "Platinum"],
            p=[0.40, 0.30, 0.20, 0.10]
        )
        # Loyalty points correlate with tier
        tier_points = {"Bronze": 500, "Silver": 2000, "Gold": 5000, "Platinum": 12000}
        base_points = tier_points[tier]
        loyalty_points = max(0, int(base_points + np.random.normal(0, base_points * 0.3)))

        phone_num = f"({random.randint(200,999)}) {random.randint(200,999)}-{random.randint(1000,9999)}"

        customers.append({
            "customer_id": f"C{i:04d}",
            "first_name": random.choice(FIRST_NAMES),
            "last_name": random.choice(LAST_NAMES),
            "age": age,
            "gender": np.random.choice(["M", "F", "Other"], p=[0.4, 0.4, 0.2]),
            "membership_tier": tier,
            "email": f"customer{i}@email.com",
            "phone": phone_num,
            "zip_code": random.choice(ZIP_CODES),
            "loyalty_points": loyalty_points,
            "preferred_section": random.choice(SECTIONS),
            "join_date": (datetime.now() - timedelta(days=random.randint(0, 840))).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(customers)


# ──────────────────────────── SALES (50k, 2 years, basket IDs) ────────────────────────────

HOLIDAYS = {
    # month-day patterns that get boosted
    (1, 1): 1.3,    # New Year
    (2, 14): 1.2,   # Valentine's
    (4, 20): 1.2,   # Easter approx
    (5, 27): 1.3,   # Memorial Day approx
    (7, 4): 1.5,    # July 4th
    (9, 4): 1.3,    # Labor Day approx
    (10, 31): 1.3,  # Halloween
    (11, 23): 1.8,  # Thanksgiving approx
    (12, 24): 1.8,  # Christmas Eve
    (12, 25): 1.5,  # Christmas
    (12, 31): 1.4,  # New Year's Eve
}


def get_holiday_boost(date):
    for (m, d), boost in HOLIDAYS.items():
        if date.month == m and abs(date.day - d) <= 2:
            return boost
    return 1.0


def generate_sales(products_df, customers_df, n=50000):
    product_ids = products_df["product_id"].tolist()
    customer_ids = customers_df["customer_id"].tolist()
    prices = dict(zip(products_df["product_id"], products_df["price"]))
    categories = dict(zip(products_df["product_id"], products_df["category"]))

    # Category popularity weights
    cat_weights = {
        "Dairy": 1.2, "Bakery": 1.1, "Beverages": 1.3, "Snacks": 1.0,
        "Produce": 1.4, "Meat": 0.9, "Frozen": 0.8, "Household": 0.6,
        "Personal Care": 0.5, "Baby & Kids": 0.4, "Pet Supplies": 0.35,
        "Condiments & Sauces": 0.7, "Canned Goods": 0.65, "Pasta & Grains": 0.75,
        "Health & Wellness": 0.45,
    }

    # Product weights based on category popularity
    prod_weights = np.array([cat_weights.get(categories[pid], 1.0) for pid in product_ids])
    prod_weights /= prod_weights.sum()

    # Dynamic date range: ~15.5 months ending now
    end_date = datetime.now()
    start_date = end_date - timedelta(days=470)
    total_days = (end_date - start_date).days

    # Generate basket-grouped sales
    sales = []
    basket_counter = 0
    sale_counter = 0

    # Generate by creating baskets (each basket = 1 shopping trip)
    num_baskets = n // 3  # avg ~3 items per basket
    for _ in range(num_baskets):
        day_offset = random.randint(0, total_days)
        sale_date = start_date + timedelta(days=day_offset)
        month = sale_date.month

        # Seasonal multiplier
        seasonal = 1.0
        if month in [6, 7, 8]:
            seasonal = 1.3
        elif month in [11, 12]:
            seasonal = 1.5
        elif month in [1, 2]:
            seasonal = 0.8

        # Weekend boost
        if sale_date.weekday() >= 5:
            seasonal *= 1.2

        # Holiday boost
        seasonal *= get_holiday_boost(sale_date)

        # Time of day (shopping hours pattern)
        hour_weights = [0]*8 + [3,5,7,9,10,10,9,8,7,6,5,3,2,1]  # 8am-9pm
        hour = random.choices(range(24), weights=[w if w > 0 else 0.1 for w in (hour_weights + [0.1]*max(0,24-len(hour_weights)))[:24]])[0]
        minute = random.randint(0, 59)

        cid = random.choice(customer_ids)
        basket_counter += 1
        basket_id = f"B{basket_counter:06d}"

        # Items in basket: 1-6, influenced by seasonal
        num_items = max(1, min(6, int(np.random.exponential(2.5) * (seasonal ** 0.3))))

        selected_products = np.random.choice(product_ids, size=num_items, replace=False, p=prod_weights)

        for pid in selected_products:
            sale_counter += 1
            quantity = max(1, int(np.random.exponential(2) * seasonal))
            quantity = min(quantity, 10)

            unit_price = prices[pid]
            discount = np.random.choice([0, 0, 0, 0.05, 0.10, 0.15], p=[0.5, 0.2, 0.1, 0.1, 0.07, 0.03])
            final_price = round(unit_price * (1 - discount), 2)

            sales.append({
                "sale_id": f"S{sale_counter:06d}",
                "basket_id": basket_id,
                "product_id": pid,
                "customer_id": cid,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount": discount,
                "total_price": round(final_price * quantity, 2),
                "timestamp": sale_date.replace(hour=hour, minute=minute).strftime("%Y-%m-%d %H:%M:%S"),
                "payment_method": np.random.choice(
                    ["Cash", "Credit Card", "Debit Card", "Digital Wallet"],
                    p=[0.15, 0.35, 0.25, 0.25]
                ),
            })

    return pd.DataFrame(sales)


# ──────────────────────────── INVENTORY ────────────────────────────

def generate_inventory(products_df):
    inventory = []
    for _, row in products_df.iterrows():
        current_stock = random.randint(5, 200)
        max_stock = random.randint(current_stock + 20, 350)
        reorder_point = random.randint(10, 50)
        last_restock = datetime.now() - timedelta(days=random.randint(0, 45))

        inventory.append({
            "product_id": row["product_id"],
            "current_stock": current_stock,
            "max_stock": max_stock,
            "reorder_point": reorder_point,
            "last_restock_date": last_restock.strftime("%Y-%m-%d"),
            "warehouse_location": f"Aisle-{random.randint(1, 30)}-Shelf-{random.choice('ABCDEFGH')}",
        })
    return pd.DataFrame(inventory)


# ──────────────────────────── MAIN ────────────────────────────

def main():
    print("=" * 50)
    print("SmartMart Data Generator V2")
    print("=" * 50)

    print("\nGenerating suppliers...")
    suppliers = generate_suppliers()
    suppliers.to_csv(os.path.join(OUTPUT_DIR, "suppliers.csv"), index=False)
    print(f"  -> {len(suppliers)} suppliers")

    print("Generating products...")
    products = generate_products()
    products.to_csv(os.path.join(OUTPUT_DIR, "products.csv"), index=False)
    print(f"  -> {len(products)} products across {products['category'].nunique()} categories")

    print("Generating customers...")
    customers = generate_customers(2000)
    customers.to_csv(os.path.join(OUTPUT_DIR, "customers.csv"), index=False)
    print(f"  -> {len(customers)} customers")

    print("Generating sales transactions...")
    sales = generate_sales(products, customers, 50000)
    sales.to_csv(os.path.join(OUTPUT_DIR, "sales.csv"), index=False)
    print(f"  -> {len(sales)} transactions in {sales['basket_id'].nunique()} baskets")

    print("Generating inventory...")
    inventory = generate_inventory(products)
    inventory.to_csv(os.path.join(OUTPUT_DIR, "inventory.csv"), index=False)
    print(f"  -> {len(inventory)} inventory records")

    print(f"\nAll data saved to: {OUTPUT_DIR}")
    print("Done!")


if __name__ == "__main__":
    main()
