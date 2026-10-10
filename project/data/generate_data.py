"""
Synthetic Indian Supermarket Data Generator — V3 (Indian Edition)
Generates realistic Indian datasets: products, customers, sales, inventory, suppliers
250+ products (real Indian brands & INR prices), 2000 customers, 50k transactions, 15 categories
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

# ──────────────────────────── PRODUCTS (250+ across 15 categories, real INR prices) ────────────────────────────

CATEGORIES = {
    "Dairy": [
        ("Amul Taaza Toned Milk 1L", 54, 3),
        ("Amul Gold Full Cream Milk 1L", 72, 3),
        ("Mother Dairy Cow Milk 500ml", 32, 3),
        ("Amul Butter 100g", 58, 30),
        ("Amul Paneer 200g", 90, 5),
        ("Amul Masti Dahi 400g", 35, 7),
        ("Amul Cheese Slices 100g (5 Slices)", 55, 30),
        ("Mother Dairy Fresh Curd 1kg", 65, 5),
        ("Nestle Milkmaid 400g", 155, 365),
        ("Amul Fresh Cream 200ml", 40, 7),
        ("Amul Lassi Mango 200ml", 25, 5),
        ("Epigamia Greek Yogurt 90g", 45, 10),
        ("Gowardhan Paneer 1kg", 380, 5),
        ("Amul Shrikhand Kesar 100g", 50, 10),
        ("Britannia Cream Cheese 180g", 99, 30),
        ("Mother Dairy Mishti Doi 100g", 30, 5),
    ],
    "Staples & Grains": [
        ("Aashirvaad Whole Wheat Atta 5kg", 280, 180),
        ("Aashirvaad Multigrain Atta 5kg", 310, 180),
        ("India Gate Basmati Rice 1kg", 120, 365),
        ("Daawat Rozana Basmati Rice 5kg", 420, 365),
        ("Tata Sampann Toor Dal 1kg", 165, 365),
        ("Tata Sampann Chana Dal 1kg", 115, 365),
        ("Tata Sampann Moong Dal 1kg", 145, 365),
        ("Tata Sampann Urad Dal 1kg", 160, 365),
        ("Fortune Soyabean Oil 1L", 160, 180),
        ("Fortune Sunflower Oil 1L", 145, 180),
        ("Tata Salt 1kg", 28, 730),
        ("Tata Rock Salt 1kg", 32, 730),
        ("MDH Rajma 500g", 85, 365),
        ("Saffola Gold Oil 1L", 195, 180),
        ("24 Mantra Organic Tur Dal 1kg", 195, 365),
        ("Kohinoor Super Value Basmati 5kg", 450, 365),
        ("Pillsbury Chakki Fresh Atta 5kg", 265, 180),
        ("MTR Rava 500g", 40, 180),
        ("MTR Besan 500g", 55, 180),
        ("Rajdhani Maida 1kg", 42, 180),
    ],
    "Bakery": [
        ("Britannia White Bread 400g", 40, 3),
        ("Britannia Whole Wheat Bread 400g", 50, 3),
        ("Amul Butter Croissants 3pk", 120, 2),
        ("English Oven Milk Bread 400g", 50, 3),
        ("Modern Bread 400g", 42, 3),
        ("Britannia Burger Buns 4pk", 55, 3),
        ("Harvest Gold Whole Wheat 450g", 45, 3),
        ("Bonn Brown Bread 400g", 38, 3),
        ("Theobroma Brownie 60g", 85, 5),
        ("Monginis Cake Slice", 65, 2),
        ("Britannia Pav 6pk", 45, 3),
        ("English Oven Hot Dog Rolls 4pk", 60, 3),
        ("Harvest Gold Fruit Bread 400g", 55, 3),
        ("Local Fresh Naan 4pk", 40, 1),
    ],
    "Beverages": [
        ("Tata Tea Gold 500g", 290, 365),
        ("Tata Tea Premium 250g", 120, 365),
        ("Brooke Bond Taj Mahal 250g", 195, 365),
        ("Bru Instant Coffee 50g", 110, 365),
        ("Nescafe Classic Coffee 50g", 155, 365),
        ("Coca-Cola 2L", 95, 180),
        ("Pepsi 2L", 95, 180),
        ("Thums Up 750ml", 40, 180),
        ("Frooti Mango Drink 1L", 70, 90),
        ("Maaza Mango Drink 1.2L", 80, 90),
        ("Sprite 750ml", 40, 180),
        ("Paper Boat Aam Panna 200ml", 30, 90),
        ("Real Fruit Juice Mixed Fruit 1L", 115, 90),
        ("Tropicana Orange Juice 1L", 110, 30),
        ("Red Bull Energy Drink 250ml", 125, 365),
        ("Bisleri Water 1L", 22, 365),
        ("Kinley Water 1L", 22, 365),
        ("Rooh Afza Sharbat 750ml", 150, 365),
    ],
    "Snacks & Namkeen": [
        ("Lays Magic Masala 52g", 20, 90),
        ("Lays Classic Salted 52g", 20, 90),
        ("Kurkure Masala Munch 100g", 30, 90),
        ("Haldiram's Bhujia 400g", 125, 120),
        ("Haldiram's Aloo Bhujia 200g", 65, 120),
        ("Haldiram's Moong Dal 200g", 55, 120),
        ("Parle-G Glucose Biscuit 250g", 25, 180),
        ("Britannia Good Day 250g", 55, 180),
        ("Britannia 50-50 Maska Chaska 120g", 30, 180),
        ("Oreo Original 120g", 30, 180),
        ("Hide & Seek Chocolate 120g", 35, 180),
        ("Bingo Mad Angles 72.5g", 20, 90),
        ("Cadbury Dairy Milk 50g", 50, 365),
        ("5 Star Chocolate 40g", 30, 365),
        ("KitKat 4 Finger 37.3g", 35, 365),
        ("Dark Fantasy Choco Fills 75g", 40, 180),
        ("Britannia Marie Gold 250g", 35, 180),
        ("Bikano Namkeen Mixture 200g", 60, 120),
    ],
    "Fruits & Vegetables": [
        ("Banana Robusta 1 dozen", 50, 3),
        ("Apple Shimla 1kg", 180, 7),
        ("Tomato (Tamatar) 1kg", 40, 5),
        ("Onion (Pyaaz) 1kg", 35, 14),
        ("Potato (Aloo) 1kg", 30, 21),
        ("Green Chilli (Hari Mirch) 250g", 15, 5),
        ("Carrot (Gajar) 500g", 35, 7),
        ("Cucumber (Kheera) 500g", 25, 5),
        ("Capsicum Green 250g", 30, 7),
        ("Spinach (Palak) 250g", 20, 2),
        ("Coriander (Dhaniya) 100g", 10, 2),
        ("Ginger (Adrak) 250g", 25, 7),
        ("Lemon (Nimbu) 250g", 20, 7),
        ("Lady Finger (Bhindi) 500g", 30, 3),
        ("Cauliflower (Phool Gobi) 1pc", 35, 5),
        ("Cabbage (Patta Gobi) 1pc", 25, 7),
        ("Mango Alphonso 1kg (seasonal)", 350, 3),
        ("Pomegranate (Anaar) 500g", 90, 7),
        ("Guava (Amrood) 500g", 40, 5),
        ("Papaya 1kg", 45, 3),
    ],
    "Meat & Seafood": [
        ("Chicken Breast 500g", 200, 2),
        ("Chicken Curry Cut 1kg", 280, 2),
        ("Chicken Drumsticks 500g", 160, 2),
        ("Mutton Curry Cut 500g", 450, 2),
        ("Fish Rohu (Whole) 1kg", 280, 1),
        ("Prawns Medium 500g", 350, 1),
        ("Chicken Seekh Kebab 250g", 180, 3),
        ("Chicken Sausages 250g", 140, 5),
        ("Eggs White (12pc)", 75, 10),
        ("Eggs White (30pc)", 180, 10),
        ("Mutton Keema 500g", 400, 2),
        ("Fish Pomfret 500g", 380, 1),
        ("Chicken Nuggets Frozen 250g", 150, 30),
        ("Surimi Crab Sticks 200g", 160, 30),
    ],
    "Frozen Foods": [
        ("McCain French Fries 450g", 125, 365),
        ("McCain Veggie Nuggets 325g", 120, 365),
        ("ITC Master Chef Frozen Paratha 5pc", 85, 180),
        ("Sumeru Frozen Peas 500g", 75, 365),
        ("Sumeru Frozen Mixed Vegetables 500g", 95, 365),
        ("Amul Ice Cream Vanilla 750ml", 195, 365),
        ("Kwality Walls Cornetto 110ml", 50, 365),
        ("Mother Dairy Ice Cream Mango Dolly", 20, 365),
        ("ITC Master Chef Chicken Seekh Kebab 200g", 155, 180),
        ("Godrej Yummiez Veg Burger Patty 360g", 170, 180),
        ("Vadilal Kulfi Stick", 30, 365),
        ("Prasuma Chicken Momos 10pc", 175, 180),
    ],
    "Household & Cleaning": [
        ("Surf Excel Easy Wash 1kg", 130, 730),
        ("Surf Excel Matic Top Load 1kg", 260, 730),
        ("Vim Dishwash Bar 200g", 20, 730),
        ("Vim Dishwash Gel 500ml", 99, 730),
        ("Harpic Toilet Cleaner 500ml", 88, 730),
        ("Lizol Floor Cleaner 500ml", 110, 730),
        ("Colin Glass Cleaner 500ml", 90, 730),
        ("Scotch-Brite Scrub Pad 3pk", 45, 730),
        ("Domex Toilet Cleaner 500ml", 82, 730),
        ("Ezee Liquid Detergent 1kg", 195, 730),
        ("Pril Dishwash Liquid 500ml", 99, 730),
        ("Hit Cockroach Spray 200ml", 165, 730),
        ("Odonil Air Freshener 75g", 49, 365),
        ("Garbage Bags Medium 30pc", 55, 730),
    ],
    "Personal Care": [
        ("Dettol Original Soap 125g", 42, 730),
        ("Dove Beauty Bar 100g", 64, 730),
        ("Clinic Plus Shampoo 340ml", 185, 730),
        ("Head & Shoulders Shampoo 340ml", 315, 730),
        ("Colgate Strong Teeth 200g", 99, 730),
        ("Colgate MaxFresh 80g", 60, 730),
        ("Pepsodent Germicheck 200g", 95, 730),
        ("Nivea Body Lotion 200ml", 210, 730),
        ("Vaseline Intensive Care 200ml", 175, 730),
        ("Himalaya Face Wash 150ml", 180, 730),
        ("Lifebuoy Handwash 190ml", 42, 730),
        ("Whisper Ultra Clean XL 30 Pads", 295, 730),
        ("Gillette Guard Razor 1pc", 45, 730),
        ("Parachute Coconut Oil 200ml", 98, 365),
        ("Dabur Amla Hair Oil 180ml", 95, 365),
        ("Set Wet Hair Gel 250ml", 160, 730),
    ],
    "Masala & Spices": [
        ("MDH Garam Masala 100g", 72, 365),
        ("MDH Chana Masala 100g", 60, 365),
        ("Everest Tikka Masala 100g", 80, 365),
        ("Everest Sambhar Masala 100g", 55, 365),
        ("Catch Red Chilli Powder 200g", 75, 365),
        ("Catch Turmeric Powder (Haldi) 200g", 52, 365),
        ("Catch Coriander Powder (Dhaniya) 200g", 58, 365),
        ("Tata Sampann Cumin Powder (Jeera) 100g", 68, 365),
        ("Saffola Masala Oats 500g", 130, 180),
        ("MTR Puliogare Paste 200g", 60, 365),
        ("MTR Rava Idli Mix 500g", 95, 180),
        ("Eastern Sambar Powder 100g", 50, 365),
        ("MDH Pav Bhaji Masala 100g", 65, 365),
        ("Catch Black Pepper (Kali Mirch) 100g", 145, 365),
    ],
    "Ready to Eat & Instant": [
        ("Maggi 2-Minute Noodles 70g", 14, 180),
        ("Maggi 2-Minute Noodles 4pk", 56, 180),
        ("Top Ramen Curry Noodles 70g", 12, 180),
        ("Yippee Magic Masala 70g", 14, 180),
        ("MTR Ready to Eat Paneer Butter Masala 300g", 110, 180),
        ("MTR Ready to Eat Dal Makhani 300g", 95, 180),
        ("Haldiram's Minute Khana Biryani 300g", 120, 90),
        ("Knorr Soup Tomato 53g", 45, 365),
        ("Knorr Soup Hot & Sour 41g", 50, 365),
        ("Ching's Schezwan Noodles 60g", 20, 180),
        ("ACT II Popcorn Classic Salted 30g", 20, 180),
        ("MTR Vermicelli 950g", 60, 180),
    ],
    "Condiments & Sauces": [
        ("Kissan Tomato Ketchup 500g", 99, 180),
        ("Kissan Mixed Fruit Jam 500g", 145, 180),
        ("Maggi Hot & Sweet Sauce 500g", 110, 180),
        ("Ching's Schezwan Chutney 250g", 75, 180),
        ("Smith & Jones Pasta Sauce 400g", 99, 180),
        ("Veeba Mayonnaise 250g", 89, 120),
        ("Funfoods Peanut Butter 400g", 199, 365),
        ("Soy Sauce Ching's 200ml", 55, 365),
        ("Tops Green Chilli Sauce 650g", 65, 365),
        ("Kissan Peanut Butter Crunchy 350g", 175, 365),
        ("Del Monte Olive Oil 500ml", 349, 365),
        ("Borges Extra Virgin Olive Oil 500ml", 549, 365),
    ],
    "Baby & Kids": [
        ("Cerelac Stage 1 (6 months) 300g", 240, 365),
        ("Cerelac Stage 2 Wheat Apple 300g", 250, 365),
        ("Johnson's Baby Soap 75g", 52, 730),
        ("Johnson's Baby Shampoo 200ml", 175, 730),
        ("Himalaya Baby Lotion 200ml", 145, 730),
        ("Himalaya Baby Diaper Rash Cream 50g", 110, 730),
        ("Pampers Diapers M (66 Count)", 999, 730),
        ("MamyPoko Pants L (44 Count)", 849, 730),
        ("Horlicks Junior 500g", 305, 365),
        ("Bournvita 5 Star Magic 500g", 220, 365),
        ("Complan Chocolate 500g", 265, 365),
        ("Dabur Gripe Water 125ml", 55, 730),
    ],
    "Health & Wellness": [
        ("Dabur Chyawanprash 500g", 210, 365),
        ("Dabur Honey 500g", 220, 365),
        ("Saffola Fittify Hi Protein Slim Meal Shake 420g", 599, 365),
        ("Himalaya Ashvagandha 60 Tablets", 175, 730),
        ("Revital H Multivitamin 30 Capsules", 350, 730),
        ("Centrum Multivitamin 30 Tablets", 499, 730),
        ("Protinex Health Drink 400g", 450, 365),
        ("Ensure Vanilla 400g", 650, 365),
        ("Zandu Balm 8ml", 30, 730),
        ("Volini Pain Relief Spray 40g", 120, 730),
        ("Crocin Advance 20 Tablets", 28, 730),
        ("Dettol Antiseptic Liquid 125ml", 58, 730),
    ],
}

# ──────────────────────────── INDIAN SUPPLIERS (Real FMCG Companies) ────────────────────────────

SUPPLIERS = [
    {"name": "Amul (GCMMF)", "email": "orders@amul.coop", "lead_time": 2, "reliability": 0.97},
    {"name": "Hindustan Unilever Ltd", "email": "supply@hul.co.in", "lead_time": 3, "reliability": 0.96},
    {"name": "ITC Limited", "email": "orders@itcportal.com", "lead_time": 3, "reliability": 0.95},
    {"name": "Nestle India Ltd", "email": "supply@in.nestle.com", "lead_time": 4, "reliability": 0.94},
    {"name": "Britannia Industries", "email": "orders@britannia.co.in", "lead_time": 2, "reliability": 0.95},
    {"name": "Parle Products Pvt Ltd", "email": "supply@parle.biz", "lead_time": 2, "reliability": 0.93},
    {"name": "Dabur India Ltd", "email": "orders@dabur.com", "lead_time": 4, "reliability": 0.92},
    {"name": "Godrej Consumer Products", "email": "supply@godrej.com", "lead_time": 3, "reliability": 0.93},
    {"name": "Marico Ltd", "email": "orders@marico.com", "lead_time": 3, "reliability": 0.91},
    {"name": "Haldiram's", "email": "supply@haldirams.com", "lead_time": 2, "reliability": 0.94},
    {"name": "MDH Spices", "email": "orders@mdhspices.com", "lead_time": 3, "reliability": 0.92},
    {"name": "Tata Consumer Products", "email": "supply@tataconsumer.com", "lead_time": 3, "reliability": 0.96},
    {"name": "Patanjali Ayurved Ltd", "email": "orders@patanjali.com", "lead_time": 4, "reliability": 0.88},
    {"name": "Mother Dairy", "email": "supply@motherdairy.com", "lead_time": 1, "reliability": 0.96},
    {"name": "McCain India", "email": "orders@mccain.co.in", "lead_time": 5, "reliability": 0.90},
    {"name": "PepsiCo India", "email": "supply@pepsicoindia.com", "lead_time": 4, "reliability": 0.92},
    {"name": "Coca-Cola India", "email": "orders@coca-cola.co.in", "lead_time": 4, "reliability": 0.93},
    {"name": "Himalaya Wellness", "email": "supply@himalayawellness.com", "lead_time": 4, "reliability": 0.91},
    {"name": "Procter & Gamble India", "email": "supply@pg.co.in", "lead_time": 3, "reliability": 0.95},
    {"name": "Reckitt India", "email": "orders@reckitt.co.in", "lead_time": 3, "reliability": 0.94},
]

# Map categories to preferred suppliers
CATEGORY_SUPPLIERS = {
    "Dairy": ["Amul (GCMMF)", "Mother Dairy", "Nestle India Ltd"],
    "Staples & Grains": ["Tata Consumer Products", "ITC Limited", "Hindustan Unilever Ltd"],
    "Bakery": ["Britannia Industries", "ITC Limited", "Parle Products Pvt Ltd"],
    "Beverages": ["Tata Consumer Products", "PepsiCo India", "Coca-Cola India", "Nestle India Ltd"],
    "Snacks & Namkeen": ["Haldiram's", "Parle Products Pvt Ltd", "PepsiCo India", "Britannia Industries"],
    "Fruits & Vegetables": ["Mother Dairy", "Godrej Consumer Products"],
    "Meat & Seafood": ["Godrej Consumer Products", "Mother Dairy"],
    "Frozen Foods": ["McCain India", "ITC Limited", "Amul (GCMMF)"],
    "Household & Cleaning": ["Hindustan Unilever Ltd", "Reckitt India", "Godrej Consumer Products"],
    "Personal Care": ["Hindustan Unilever Ltd", "Procter & Gamble India", "Himalaya Wellness", "Dabur India Ltd"],
    "Masala & Spices": ["MDH Spices", "Tata Consumer Products", "ITC Limited"],
    "Ready to Eat & Instant": ["Nestle India Ltd", "ITC Limited", "Haldiram's"],
    "Condiments & Sauces": ["Hindustan Unilever Ltd", "Nestle India Ltd", "ITC Limited"],
    "Baby & Kids": ["Nestle India Ltd", "Hindustan Unilever Ltd", "Himalaya Wellness", "Procter & Gamble India"],
    "Health & Wellness": ["Dabur India Ltd", "Himalaya Wellness", "Patanjali Ayurved Ltd"],
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
        possible_suppliers = CATEGORY_SUPPLIERS.get(category, ["Tata Consumer Products"])
        for name, price, shelf_life in items:
            products.append({
                "product_id": f"P{pid:04d}",
                "name": name,
                "category": category,
                "price": round(price + np.random.uniform(-price * 0.05, price * 0.05), 2),
                "cost": round(price * np.random.uniform(0.50, 0.70), 2),
                "supplier": random.choice(possible_suppliers),
                "shelf_life_days": shelf_life,
                "unit": random.choice(["piece", "pack", "kg", "liter"]),
            })
            pid += 1
    return pd.DataFrame(products)


# ──────────────────────────── CUSTOMERS (Indian names, cities, PIN codes) ────────────────────────────

FIRST_NAMES_MALE = [
    "Aarav", "Amit", "Rahul", "Rajesh", "Suresh", "Vikram", "Arun", "Manoj",
    "Deepak", "Sanjay", "Ravi", "Pradeep", "Ajay", "Vijay", "Nitin", "Rohit",
    "Karan", "Arjun", "Varun", "Gaurav", "Sahil", "Pankaj", "Nikhil", "Vivek",
    "Anand", "Harsh", "Kunal", "Mohit", "Sachin", "Tushar", "Vishal", "Aditya",
    "Dev", "Ishaan", "Kabir", "Lakshay", "Manish", "Naveen", "Om", "Pranav",
    "Rakesh", "Shubham", "Tarun", "Umesh", "Yash", "Rohan", "Akash", "Chirag",
    "Dhruv", "Eshaan", "Farhan", "Ganesh", "Hari", "Jatin", "Krishna", "Lalit",
    "Mukesh", "Neeraj", "Prakash", "Rajat", "Sunil", "Tanmay", "Utkarsh", "Vihaan",
]

FIRST_NAMES_FEMALE = [
    "Priya", "Neha", "Anjali", "Pooja", "Sunita", "Kavita", "Divya", "Meena",
    "Rashmi", "Swati", "Nisha", "Ritu", "Shweta", "Pallavi", "Anita", "Deepika",
    "Isha", "Shruti", "Tanvi", "Aditi", "Bhavna", "Chitra", "Garima", "Jyoti",
    "Komal", "Lata", "Manju", "Namrata", "Parul", "Renu", "Shalini", "Tara",
    "Usha", "Vidya", "Yamini", "Aishwarya", "Bhoomika", "Chetna", "Disha", "Ekta",
    "Falguni", "Geeta", "Harsha", "Ila", "Juhi", "Kirti", "Leela", "Madhuri",
    "Nandini", "Payal", "Rani", "Sarita", "Trisha", "Uma", "Vrinda", "Zara",
    "Aanya", "Myra", "Saanvi", "Riya", "Ananya", "Aarohi", "Khushi", "Pihu",
]

LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Singh", "Patel", "Kumar", "Reddy", "Rao",
    "Das", "Mishra", "Mehta", "Joshi", "Shah", "Nair", "Menon", "Pillai",
    "Iyer", "Yadav", "Chauhan", "Tiwari", "Pandey", "Dubey", "Saxena", "Agarwal",
    "Banerjee", "Mukherjee", "Chatterjee", "Bose", "Sen", "Roy", "Ghosh", "Dey",
    "Kulkarni", "Deshmukh", "Patil", "Jadhav", "More", "Pawar", "Thakur", "Chowdhury",
    "Rathore", "Kaur", "Gill", "Bhatia", "Khanna", "Malhotra", "Kapoor", "Arora",
    "Sinha", "Prasad", "Mohan", "Srinivasan", "Naidu", "Hegde", "Bhatt", "Choudhary",
    "Rajan", "Goyal", "Garg", "Mittal", "Rastogi", "Trivedi", "Deshpande", "Nayak",
]

# Indian cities with PIN codes and state info
CITIES = [
    {"city": "Mumbai", "state": "Maharashtra", "pins": ["400001", "400050", "400053", "400069", "400072", "400076", "400080", "400092"]},
    {"city": "Delhi", "state": "Delhi", "pins": ["110001", "110011", "110017", "110025", "110034", "110044", "110048", "110062"]},
    {"city": "Bangalore", "state": "Karnataka", "pins": ["560001", "560008", "560011", "560034", "560038", "560043", "560068", "560078"]},
    {"city": "Hyderabad", "state": "Telangana", "pins": ["500001", "500003", "500013", "500018", "500029", "500033", "500038", "500049"]},
    {"city": "Chennai", "state": "Tamil Nadu", "pins": ["600001", "600010", "600017", "600024", "600032", "600040", "600078", "600096"]},
    {"city": "Pune", "state": "Maharashtra", "pins": ["411001", "411004", "411011", "411016", "411021", "411028", "411038", "411048"]},
    {"city": "Kolkata", "state": "West Bengal", "pins": ["700001", "700006", "700012", "700019", "700027", "700032", "700053", "700064"]},
    {"city": "Ahmedabad", "state": "Gujarat", "pins": ["380001", "380006", "380013", "380015", "380022", "380027", "380052", "380058"]},
    {"city": "Jaipur", "state": "Rajasthan", "pins": ["302001", "302004", "302012", "302015", "302017", "302019", "302020", "302021"]},
    {"city": "Lucknow", "state": "Uttar Pradesh", "pins": ["226001", "226003", "226010", "226012", "226016", "226020", "226022", "226025"]},
    {"city": "Chandigarh", "state": "Chandigarh", "pins": ["160001", "160009", "160011", "160014", "160017", "160019", "160022", "160036"]},
    {"city": "Kochi", "state": "Kerala", "pins": ["682001", "682011", "682016", "682018", "682020", "682024", "682026", "682030"]},
]

SECTIONS = ["Fruits & Vegetables", "Dairy", "Meat & Seafood", "Bakery", "Beverages", "Frozen Foods", "Snacks & Namkeen", "Household & Cleaning", "Staples & Grains"]


def generate_customers(n=2000):
    customers = []
    for i in range(1, n + 1):
        age = int(np.random.normal(35, 12))
        age = max(18, min(75, age))
        gender = np.random.choice(["M", "F", "Other"], p=[0.45, 0.45, 0.10])

        if gender == "M":
            first_name = random.choice(FIRST_NAMES_MALE)
        elif gender == "F":
            first_name = random.choice(FIRST_NAMES_FEMALE)
        else:
            first_name = random.choice(FIRST_NAMES_MALE + FIRST_NAMES_FEMALE)

        last_name = random.choice(LAST_NAMES)

        tier = np.random.choice(
            ["Bronze", "Silver", "Gold", "Platinum"],
            p=[0.40, 0.30, 0.20, 0.10]
        )
        # Loyalty points correlate with tier
        tier_points = {"Bronze": 500, "Silver": 2000, "Gold": 5000, "Platinum": 12000}
        base_points = tier_points[tier]
        loyalty_points = max(0, int(base_points + np.random.normal(0, base_points * 0.3)))

        city_info = random.choice(CITIES)
        pin_code = random.choice(city_info["pins"])
        phone_num = f"+91 {random.randint(70000, 99999)}{random.randint(10000, 99999)}"
        email_name = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}"
        email = f"{email_name}@{random.choice(['gmail.com', 'yahoo.co.in', 'outlook.com', 'hotmail.com', 'rediffmail.com'])}"

        customers.append({
            "customer_id": f"C{i:04d}",
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "gender": gender,
            "membership_tier": tier,
            "email": email,
            "phone": phone_num,
            "zip_code": pin_code,
            "loyalty_points": loyalty_points,
            "preferred_section": random.choice(SECTIONS),
            "join_date": (datetime.now() - timedelta(days=random.randint(0, 840))).strftime("%Y-%m-%d"),
        })
    return pd.DataFrame(customers)


# ──────────────────────────── SALES (50k, ~15.5 months, basket IDs) ────────────────────────────

# Indian festivals and holidays that boost sales
HOLIDAYS = {
    (1, 14): 1.3,    # Makar Sankranti / Pongal
    (1, 26): 1.4,    # Republic Day
    (3, 8): 1.2,     # Holi (approx)
    (3, 25): 1.3,    # Holi (approx)
    (4, 14): 1.2,    # Baisakhi
    (8, 15): 1.4,    # Independence Day
    (8, 26): 1.3,    # Janmashtami (approx)
    (9, 19): 1.3,    # Ganesh Chaturthi (approx)
    (10, 2): 1.3,    # Gandhi Jayanti
    (10, 12): 1.6,   # Dussehra (approx)
    (10, 24): 1.5,   # Karwa Chauth (approx)
    (11, 1): 2.0,    # Diwali (approx) — massive boost
    (11, 2): 1.8,    # Diwali (day after)
    (11, 15): 1.3,   # Guru Nanak Jayanti (approx)
    (12, 25): 1.4,   # Christmas
    (12, 31): 1.3,   # New Year's Eve
    (1, 1): 1.2,     # New Year
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

    # Category popularity weights (adjusted for Indian shopping patterns)
    cat_weights = {
        "Dairy": 1.4, "Staples & Grains": 1.5, "Bakery": 0.8, "Beverages": 1.2,
        "Snacks & Namkeen": 1.3, "Fruits & Vegetables": 1.4, "Meat & Seafood": 0.7,
        "Frozen Foods": 0.6, "Household & Cleaning": 0.8, "Personal Care": 0.7,
        "Masala & Spices": 1.0, "Ready to Eat & Instant": 0.9,
        "Condiments & Sauces": 0.7, "Baby & Kids": 0.4, "Health & Wellness": 0.5,
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

        # Seasonal multiplier (Indian patterns: festive season boost Oct-Nov, summer demand Jun-Jul)
        seasonal = 1.0
        if month in [6, 7]:
            seasonal = 1.2   # Summer — beverages, ice cream
        elif month in [10, 11]:
            seasonal = 1.6   # Festive season — Navratri, Dussehra, Diwali
        elif month in [12]:
            seasonal = 1.3   # Year-end / Christmas / New Year
        elif month in [3]:
            seasonal = 1.2   # Holi
        elif month in [1, 2]:
            seasonal = 0.85  # Post-festive lull

        # Weekend boost
        if sale_date.weekday() >= 5:
            seasonal *= 1.2

        # Holiday boost
        seasonal *= get_holiday_boost(sale_date)

        # Time of day (shopping hours pattern — Indian timing)
        hour_weights = [0]*7 + [2, 4, 6, 8, 10, 8, 6, 5, 4, 5, 7, 9, 8, 5, 3, 1, 0]  # 7am-11pm
        hour = random.choices(range(24), weights=[w if w > 0 else 0.1 for w in (hour_weights + [0.1]*max(0,24-len(hour_weights)))[:24]])[0]
        minute = random.randint(0, 59)

        cid = random.choice(customer_ids)
        basket_counter += 1
        basket_id = f"B{basket_counter:06d}"

        # Items in basket: 1-8, influenced by seasonal
        num_items = max(1, min(8, int(np.random.exponential(2.5) * (seasonal ** 0.3))))

        selected_products = np.random.choice(product_ids, size=num_items, replace=False, p=prod_weights)

        for pid in selected_products:
            sale_counter += 1
            quantity = max(1, int(np.random.exponential(2) * seasonal))
            quantity = min(quantity, 10)

            unit_price = prices[pid]
            discount = np.random.choice([0, 0, 0, 0.05, 0.10, 0.15, 0.20], p=[0.45, 0.15, 0.10, 0.12, 0.10, 0.05, 0.03])
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
                    ["Cash", "Credit Card", "Debit Card", "UPI", "Net Banking"],
                    p=[0.15, 0.15, 0.20, 0.40, 0.10]
                ),
            })

    return pd.DataFrame(sales)


# ──────────────────────────── INVENTORY ────────────────────────────

WAREHOUSE_LOCATIONS = [
    "Mumbai Hub - Aisle {a} Shelf {s}",
    "Delhi Warehouse - Aisle {a} Shelf {s}",
    "Bangalore DC - Aisle {a} Shelf {s}",
    "Hyderabad Hub - Aisle {a} Shelf {s}",
    "Chennai Warehouse - Aisle {a} Shelf {s}",
    "Pune DC - Aisle {a} Shelf {s}",
    "Kolkata Hub - Aisle {a} Shelf {s}",
    "Ahmedabad Warehouse - Aisle {a} Shelf {s}",
]


def generate_inventory(products_df):
    inventory = []
    for _, row in products_df.iterrows():
        current_stock = random.randint(5, 200)
        max_stock = random.randint(current_stock + 20, 350)
        reorder_point = random.randint(10, 50)
        last_restock = datetime.now() - timedelta(days=random.randint(0, 45))

        warehouse = random.choice(WAREHOUSE_LOCATIONS).format(
            a=random.randint(1, 25),
            s=random.choice("ABCDEFGH")
        )

        inventory.append({
            "product_id": row["product_id"],
            "current_stock": current_stock,
            "max_stock": max_stock,
            "reorder_point": reorder_point,
            "last_restock_date": last_restock.strftime("%Y-%m-%d"),
            "warehouse_location": warehouse,
        })
    return pd.DataFrame(inventory)


# ──────────────────────────── MAIN ────────────────────────────

def main():
    print("=" * 55)
    print("  SmartMart Indian Data Generator V3")
    print("  Real Indian brands, INR prices, Indian demographics")
    print("=" * 55)

    print("\nGenerating suppliers (Indian FMCG companies)...")
    suppliers = generate_suppliers()
    suppliers.to_csv(os.path.join(OUTPUT_DIR, "suppliers.csv"), index=False)
    print(f"  -> {len(suppliers)} suppliers")

    print("Generating products (Indian brands, INR prices)...")
    products = generate_products()
    products.to_csv(os.path.join(OUTPUT_DIR, "products.csv"), index=False)
    print(f"  -> {len(products)} products across {products['category'].nunique()} categories")

    print("Generating customers (Indian demographics)...")
    customers = generate_customers(2000)
    customers.to_csv(os.path.join(OUTPUT_DIR, "customers.csv"), index=False)
    print(f"  -> {len(customers)} customers across {len(CITIES)} cities")

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
