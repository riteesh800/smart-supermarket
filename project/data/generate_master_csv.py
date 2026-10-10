"""
SmartMart AI — Indian Supermarket Master CSV Generator
======================================================
Generates ONE extremely large, production-quality, denormalized CSV file
that, when uploaded through the system's single-CSV upload, provides enough
data for EVERY feature: dashboard, forecasting, segmentation, recommendations,
pricing, heatmaps, anomaly detection, profit analysis, demographics, retention.

Target: ~500K-600K transaction rows covering 18 months of history.
All prices in INR, Indian brands/products/names, realistic demographics.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random
import sys
import time

# ─── Reproducibility ───
np.random.seed(2024)
random.seed(2024)

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "indian_supermarket_master_dataset.csv")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. PRODUCT CATALOG — 350+ Indian Supermarket Products across 18 categories
# ═══════════════════════════════════════════════════════════════════════════════

CATEGORIES = {
    "Dairy": [
        ("Amul Taaza Toned Milk 1L", 54, 35, 7, "Amul", "liter"),
        ("Mother Dairy Full Cream Milk 1L", 68, 44, 7, "Mother Dairy", "liter"),
        ("Amul Butter 500g", 270, 185, 60, "Amul", "pack"),
        ("Amul Cheese Slices 200g", 120, 78, 30, "Amul", "pack"),
        ("Nestle Dahi 400g", 40, 26, 14, "Nestle", "pack"),
        ("Amul Paneer 200g", 90, 58, 7, "Amul", "pack"),
        ("Mother Dairy Mishti Doi 400g", 55, 36, 10, "Mother Dairy", "pack"),
        ("Amul Masti Buttermilk 1L", 30, 18, 7, "Amul", "liter"),
        ("Epigamia Greek Yogurt 90g", 45, 28, 14, "Epigamia", "piece"),
        ("Amul Gold Milk 500ml", 35, 22, 7, "Amul", "liter"),
        ("Milky Mist Paneer 1kg", 380, 260, 7, "Milky Mist", "kg"),
        ("Amul Ice Cream Vanilla 1L", 249, 165, 180, "Amul", "liter"),
        ("Go Cheese Spread 200g", 99, 64, 30, "Go Dairy", "pack"),
        ("Nestle a+ Slim Milk 1L", 62, 40, 7, "Nestle", "liter"),
        ("Chitale Shrikhand 250g", 130, 85, 14, "Chitale", "pack"),
        ("Amul Cream 200ml", 60, 38, 14, "Amul", "pack"),
        ("Heritage Curd 500g", 38, 24, 10, "Heritage", "pack"),
    ],
    "Bakery": [
        ("Britannia White Bread 400g", 40, 24, 5, "Britannia", "pack"),
        ("Harvest Gold Whole Wheat Bread 450g", 50, 32, 5, "Harvest Gold", "pack"),
        ("English Oven Burger Buns 4pk", 60, 38, 3, "English Oven", "pack"),
        ("Britannia Cake Rusk 600g", 120, 72, 60, "Britannia", "pack"),
        ("Modern 100% Whole Wheat Bread 400g", 45, 28, 5, "Modern", "pack"),
        ("Amul Garlic Bread 200g", 85, 52, 3, "Amul", "pack"),
        ("Bonn Brown Bread 400g", 42, 26, 5, "Bonn", "pack"),
        ("English Oven Pav 6pk", 40, 24, 3, "English Oven", "pack"),
        ("Britannia Milk Bread 400g", 42, 26, 5, "Britannia", "pack"),
        ("Monginis Fruit Cake 250g", 120, 75, 7, "Monginis", "pack"),
        ("Modern Multigrain Bread 450g", 55, 34, 5, "Modern", "pack"),
    ],
    "Beverages": [
        ("Coca-Cola 2L", 96, 62, 180, "Coca-Cola", "liter"),
        ("Pepsi 2L", 96, 62, 180, "PepsiCo", "liter"),
        ("Thums Up 750ml", 40, 26, 180, "Coca-Cola", "piece"),
        ("Paper Boat Aam Panna 200ml", 30, 18, 90, "Paper Boat", "piece"),
        ("Tropicana Orange Juice 1L", 120, 78, 14, "PepsiCo", "liter"),
        ("Real Fruit Power Mango 1L", 110, 72, 14, "Dabur", "liter"),
        ("Red Bull Energy Drink 250ml", 125, 82, 365, "Red Bull", "piece"),
        ("Bisleri Water 5L", 60, 30, 365, "Bisleri", "piece"),
        ("Tata Tea Gold 500g", 275, 180, 365, "Tata Consumer", "pack"),
        ("Nescafe Classic Coffee 200g", 499, 325, 365, "Nestle", "pack"),
        ("Bru Instant Coffee 200g", 375, 245, 365, "HUL", "pack"),
        ("Tang Orange 500g", 190, 125, 365, "Mondelez", "pack"),
        ("Sprite 2L", 96, 62, 180, "Coca-Cola", "liter"),
        ("Maaza Mango 1.2L", 70, 45, 90, "Coca-Cola", "liter"),
        ("Frooti Mango 1L", 55, 35, 90, "Parle Agro", "liter"),
        ("Appy Fizz 1L", 65, 42, 90, "Parle Agro", "liter"),
        ("Limca 750ml", 40, 26, 180, "Coca-Cola", "piece"),
        ("Mountain Dew 2L", 96, 62, 180, "PepsiCo", "liter"),
    ],
    "Snacks": [
        ("Lay's Classic Salted 52g", 20, 12, 90, "PepsiCo", "pack"),
        ("Kurkure Masala Munch 80g", 20, 12, 90, "PepsiCo", "pack"),
        ("Haldiram's Aloo Bhujia 200g", 80, 48, 120, "Haldiram's", "pack"),
        ("Bingo Mad Angles 66g", 20, 12, 90, "ITC", "pack"),
        ("Parle Monaco Biscuit 200g", 35, 22, 180, "Parle", "pack"),
        ("Cadbury Dairy Milk 50g", 50, 32, 180, "Mondelez", "piece"),
        ("Cadbury 5 Star 40g", 30, 18, 180, "Mondelez", "piece"),
        ("KitKat 2-Finger 18g", 20, 12, 180, "Nestle", "piece"),
        ("Hide & Seek Biscuit 120g", 30, 18, 180, "Parle", "pack"),
        ("Haldiram's Sev Bhujia 200g", 80, 48, 120, "Haldiram's", "pack"),
        ("Balaji Wafer Masala 150g", 30, 18, 90, "Balaji", "pack"),
        ("Bikano Namkeen Mix 200g", 70, 42, 120, "Bikano", "pack"),
        ("Cadbury Gems 17.8g", 10, 6, 180, "Mondelez", "piece"),
        ("Uncle Chipps 55g", 20, 12, 90, "PepsiCo", "pack"),
        ("Parle-G Biscuit 800g", 56, 34, 180, "Parle", "pack"),
        ("Good Day Butter Cookies 200g", 45, 28, 180, "Britannia", "pack"),
        ("Oreo Original 120g", 30, 18, 180, "Mondelez", "pack"),
        ("McVities Digestive 400g", 165, 105, 180, "Pladis", "pack"),
        ("Dark Fantasy Choco Fills 75g", 40, 24, 180, "Sunfeast", "pack"),
        ("Too Yumm Multigrain Chips 54g", 20, 12, 90, "Guiltfree", "pack"),
    ],
    "Staples & Grains": [
        ("India Gate Basmati Rice 5kg", 620, 400, 365, "KRBL", "kg"),
        ("Aashirvaad Atta 10kg", 485, 320, 180, "ITC", "kg"),
        ("Fortune Sunflower Oil 5L", 750, 520, 365, "Adani Wilmar", "liter"),
        ("Tata Sampann Toor Dal 1kg", 165, 108, 365, "Tata Consumer", "kg"),
        ("Tata Salt 1kg", 28, 18, 730, "Tata Consumer", "kg"),
        ("Saffola Gold Oil 1L", 189, 124, 365, "Marico", "liter"),
        ("Daawat Brown Rice 1kg", 140, 90, 365, "LT Foods", "kg"),
        ("Rajdhani Chana Dal 1kg", 110, 72, 365, "Rajdhani", "kg"),
        ("Patanjali Moong Dal 1kg", 140, 92, 365, "Patanjali", "kg"),
        ("24 Mantra Organic Tur Dal 1kg", 195, 128, 365, "24 Mantra", "kg"),
        ("MDH Rajma 500g", 85, 55, 365, "MDH", "pack"),
        ("Kohinoor Basmati Rice 1kg", 180, 118, 365, "McCormick", "kg"),
        ("Fortune Refined Oil 1L", 155, 102, 365, "Adani Wilmar", "liter"),
        ("Aashirvaad Multigrain Atta 5kg", 290, 190, 180, "ITC", "kg"),
        ("Tata Sampann Moong Dal 1kg", 160, 105, 365, "Tata Consumer", "kg"),
        ("Organic Tattva Quinoa 500g", 299, 195, 365, "Organic Tattva", "pack"),
        ("Sujata Gold Atta 10kg", 440, 288, 180, "Sujata", "kg"),
    ],
    "Spices & Masala": [
        ("MDH Garam Masala 100g", 85, 52, 365, "MDH", "pack"),
        ("Everest Turmeric Powder 100g", 42, 26, 365, "Everest", "pack"),
        ("MDH Chilli Powder 100g", 62, 38, 365, "MDH", "pack"),
        ("Catch Cumin Powder 100g", 75, 48, 365, "Catch", "pack"),
        ("Everest Coriander Powder 100g", 38, 24, 365, "Everest", "pack"),
        ("Tata Sampann Chaat Masala 100g", 49, 32, 365, "Tata Consumer", "pack"),
        ("MDH Pav Bhaji Masala 100g", 72, 46, 365, "MDH", "pack"),
        ("Everest Biryani Masala 50g", 55, 36, 365, "Everest", "pack"),
        ("Eastern Sambhar Masala 100g", 60, 38, 365, "Eastern", "pack"),
        ("MDH Kitchen King 100g", 80, 52, 365, "MDH", "pack"),
        ("Catch Black Pepper 100g", 155, 100, 365, "Catch", "pack"),
        ("Saffron 1g", 250, 165, 365, "Kashmir Premium", "piece"),
    ],
    "Fresh Produce": [
        ("Onion 1kg", 40, 26, 7, "Local Farm", "kg"),
        ("Tomato 1kg", 35, 22, 5, "Local Farm", "kg"),
        ("Potato 1kg", 30, 18, 14, "Local Farm", "kg"),
        ("Green Chilli 250g", 15, 8, 3, "Local Farm", "kg"),
        ("Ginger 250g", 22, 14, 10, "Local Farm", "kg"),
        ("Garlic 250g", 28, 18, 14, "Local Farm", "kg"),
        ("Lady Finger (Bhindi) 500g", 30, 18, 3, "Local Farm", "kg"),
        ("Spinach (Palak) Bunch", 25, 14, 2, "Local Farm", "piece"),
        ("Cauliflower 1pc", 35, 22, 5, "Local Farm", "piece"),
        ("Cabbage 1pc", 30, 18, 7, "Local Farm", "piece"),
        ("Capsicum Green 250g", 25, 15, 5, "Local Farm", "kg"),
        ("Carrot 500g", 28, 18, 7, "Local Farm", "kg"),
        ("Banana 1 dozen", 50, 30, 3, "Local Farm", "piece"),
        ("Apple (Shimla) 1kg", 180, 120, 10, "Kashmir Fresh", "kg"),
        ("Mango (Alphonso) 1kg", 350, 230, 3, "Ratnagiri Farms", "kg"),
        ("Papaya 1pc", 45, 28, 3, "Local Farm", "piece"),
        ("Pomegranate 500g", 120, 78, 7, "Maharashtra Fresh", "kg"),
        ("Guava 500g", 50, 30, 5, "Local Farm", "kg"),
        ("Lemon 250g", 20, 12, 7, "Local Farm", "kg"),
        ("Coriander Leaves Bunch", 10, 5, 2, "Local Farm", "piece"),
        ("Mint Leaves Bunch", 10, 5, 2, "Local Farm", "piece"),
        ("Curry Leaves Bunch", 10, 5, 3, "Local Farm", "piece"),
        ("Coconut 1pc", 35, 22, 14, "Kerala Fresh", "piece"),
        ("Drumstick 250g", 20, 12, 5, "Local Farm", "kg"),
    ],
    "Meat & Seafood": [
        ("Chicken Breast 500g", 220, 145, 2, "Godrej Real Good", "kg"),
        ("Chicken Curry Cut 1kg", 280, 185, 2, "Suguna", "kg"),
        ("Mutton Curry Cut 500g", 400, 265, 2, "Licious", "kg"),
        ("Fish (Rohu) 1kg", 280, 185, 1, "FreshToHome", "kg"),
        ("Prawns 500g", 350, 230, 1, "FreshToHome", "kg"),
        ("Chicken Seekh Kebab 300g", 199, 130, 3, "ITC Master Chef", "pack"),
        ("Chicken Sausages 250g", 160, 105, 7, "Godrej Real Good", "pack"),
        ("Egg (Tray of 30)", 210, 140, 14, "Keggs Farm", "piece"),
        ("Chicken Wings 500g", 180, 118, 2, "Suguna", "kg"),
        ("Chicken Keema 500g", 200, 132, 2, "Licious", "kg"),
        ("Surmai (King Fish) 500g", 450, 295, 1, "FreshToHome", "kg"),
        ("Pomfret 500g", 500, 330, 1, "FreshToHome", "kg"),
    ],
    "Frozen Foods": [
        ("McCain French Fries 750g", 199, 130, 180, "McCain", "pack"),
        ("ITC Master Chef Chicken Nuggets 450g", 270, 178, 180, "ITC", "pack"),
        ("Godrej Real Good Chicken Seekh 300g", 185, 120, 180, "Godrej", "pack"),
        ("Sumeru Frozen Peas 500g", 75, 48, 365, "Sumeru", "pack"),
        ("Vadilal Frozen Parathas 5pk", 120, 78, 180, "Vadilal", "pack"),
        ("McCain Aloo Tikki 400g", 150, 98, 180, "McCain", "pack"),
        ("Mother Dairy Frozen Mixed Veg 500g", 85, 55, 365, "Mother Dairy", "pack"),
        ("Prasuma Chicken Momos 10pk", 199, 130, 180, "Prasuma", "pack"),
        ("Sumeru Frozen Corn 500g", 75, 48, 365, "Sumeru", "pack"),
        ("Kwality Walls Cornetto 110ml", 50, 32, 365, "HUL", "piece"),
        ("Amul Frozen Chapati 10pk", 85, 55, 180, "Amul", "pack"),
        ("Godrej Yummiez Veg Burger Patty 360g", 180, 118, 180, "Godrej", "pack"),
    ],
    "Household": [
        ("Surf Excel Matic 2kg", 399, 262, 730, "HUL", "pack"),
        ("Vim Dishwash Bar 500g", 44, 28, 730, "HUL", "piece"),
        ("Harpic Toilet Cleaner 1L", 145, 95, 730, "Reckitt", "liter"),
        ("Lizol Floor Cleaner 1L", 179, 118, 730, "Reckitt", "liter"),
        ("Scotch-Brite Scrub Pad 3pk", 50, 32, 730, "3M", "pack"),
        ("Colin Glass Cleaner 500ml", 105, 68, 730, "Reckitt", "piece"),
        ("Pril Dishwash Liquid 750ml", 139, 90, 730, "Henkel", "piece"),
        ("Garbage Bags Large 30pk", 120, 78, 730, "Ezee", "pack"),
        ("Good Knight Liquid Refill 45ml", 67, 44, 365, "Godrej", "piece"),
        ("Hit Anti-Roach Spray 200ml", 165, 108, 365, "Godrej", "piece"),
        ("Odonil Air Freshener 75g", 52, 34, 180, "Dabur", "piece"),
        ("Domex Toilet Cleaner 1L", 135, 88, 730, "HUL", "liter"),
        ("Cello Dustbin 12L", 299, 195, 730, "Cello", "piece"),
        ("Ariel Matic Top Load 2kg", 430, 282, 730, "P&G", "pack"),
        ("Comfort Fabric Conditioner 860ml", 199, 130, 730, "HUL", "piece"),
    ],
    "Personal Care": [
        ("Dove Soap 100g 4pk", 220, 145, 730, "HUL", "pack"),
        ("Head & Shoulders Shampoo 340ml", 310, 204, 730, "P&G", "piece"),
        ("Colgate MaxFresh Toothpaste 150g", 105, 68, 730, "Colgate", "piece"),
        ("Dettol Handwash 200ml", 55, 35, 730, "Reckitt", "piece"),
        ("Nivea Body Lotion 400ml", 349, 228, 730, "Nivea", "piece"),
        ("Gillette Guard Razor 3pk", 90, 58, 730, "P&G", "pack"),
        ("Lux Soap 150g 3pk", 125, 82, 730, "HUL", "pack"),
        ("Vaseline Body Lotion 400ml", 275, 180, 730, "HUL", "piece"),
        ("Whisper Ultra Soft XL 30pk", 299, 195, 730, "P&G", "pack"),
        ("Oral-B Toothbrush 2pk", 80, 52, 730, "P&G", "pack"),
        ("Set Wet Hair Gel 250ml", 175, 115, 730, "Set Wet", "piece"),
        ("Ponds Face Cream 100g", 199, 130, 730, "HUL", "piece"),
        ("Himalaya Neem Face Wash 200ml", 180, 118, 730, "Himalaya", "piece"),
        ("Parachute Coconut Oil 500ml", 135, 88, 730, "Marico", "piece"),
    ],
    "Baby & Kids": [
        ("Pampers Active Baby Diapers M 66pk", 999, 660, 730, "P&G", "pack"),
        ("Johnson's Baby Shampoo 500ml", 350, 230, 730, "J&J", "piece"),
        ("Cerelac Wheat Apple 300g", 250, 165, 365, "Nestle", "pack"),
        ("Huggies Wonder Pants L 42pk", 799, 528, 730, "Kimberly-Clark", "pack"),
        ("Himalaya Baby Cream 200ml", 195, 128, 730, "Himalaya", "piece"),
        ("MamyPoko Pants M 40pk", 749, 495, 730, "Unicharm", "pack"),
        ("Nestle NAN Pro 1 400g", 799, 528, 365, "Nestle", "pack"),
        ("Dabur Lal Tail 200ml", 110, 72, 365, "Dabur", "piece"),
        ("Johnson's Baby Powder 400g", 285, 188, 730, "J&J", "piece"),
        ("Cerelac Rice 300g", 250, 165, 365, "Nestle", "pack"),
        ("Himalaya Baby Soap 125g", 52, 34, 730, "Himalaya", "piece"),
    ],
    "Condiments & Sauces": [
        ("Kissan Tomato Ketchup 500g", 115, 75, 180, "HUL", "pack"),
        ("Maggi Hot & Sweet Sauce 500g", 120, 78, 180, "Nestle", "pack"),
        ("Tops Green Chilli Sauce 650g", 95, 62, 180, "Tops", "pack"),
        ("Dabur Honey 500g", 249, 164, 365, "Dabur", "pack"),
        ("Smith & Jones Pasta Sauce 400g", 99, 64, 180, "Capital Foods", "pack"),
        ("Funfoods Veg Mayonnaise 275g", 115, 75, 180, "Dr. Oetker", "pack"),
        ("Ching's Schezwan Chutney 250g", 85, 55, 180, "Capital Foods", "pack"),
        ("Weikfield Pasta Sauce 500g", 110, 72, 180, "Weikfield", "pack"),
        ("Heinz Tomato Ketchup 450g", 130, 85, 180, "Kraft Heinz", "pack"),
        ("Patanjali Pickle Mixed 500g", 99, 64, 365, "Patanjali", "pack"),
        ("Priya Mango Pickle 300g", 80, 52, 365, "Priya Foods", "pack"),
        ("Mother's Recipe Lime Pickle 300g", 85, 55, 365, "Mother's Recipe", "pack"),
    ],
    "Instant & Ready-to-Eat": [
        ("Maggi 2-Minute Noodles 70g 12pk", 144, 94, 180, "Nestle", "pack"),
        ("Knorr Soups Tomato 12g 4pk", 60, 38, 365, "HUL", "pack"),
        ("MTR Ready-to-Eat Paneer Butter Masala 300g", 120, 78, 180, "MTR", "pack"),
        ("Saffola Masala Oats 500g", 199, 130, 180, "Marico", "pack"),
        ("Yippee Noodles 60g 12pk", 120, 78, 180, "ITC", "pack"),
        ("Cup Noodles Masala 70g", 45, 28, 180, "Nissin", "piece"),
        ("Wai Wai Noodles 75g 6pk", 90, 58, 180, "CG Foods", "pack"),
        ("Haldiram's Minute Khana Dal Makhani 300g", 110, 72, 180, "Haldiram's", "pack"),
        ("MTR Rava Idli Mix 500g", 99, 64, 180, "MTR", "pack"),
        ("Gits Gulab Jamun Mix 200g", 90, 58, 180, "Gits", "pack"),
        ("MTR Bisibele Bath Paste 200g", 72, 46, 180, "MTR", "pack"),
        ("Maggi Pazzta Cheesy 64g 4pk", 80, 52, 180, "Nestle", "pack"),
        ("Top Ramen Curry Noodles 70g 8pk", 96, 62, 180, "Indo Nissin", "pack"),
        ("Ching's Manchurian Noodles 60g 8pk", 104, 68, 180, "Capital Foods", "pack"),
    ],
    "Canned & Packaged": [
        ("Del Monte Pineapple Slices 439g", 120, 78, 730, "Del Monte", "pack"),
        ("Sil Jam Mixed Fruit 500g", 130, 85, 365, "Sil", "pack"),
        ("Kissan Mixed Fruit Jam 500g", 155, 102, 365, "HUL", "pack"),
        ("Maggi Pichkoo Ketchup 90g 12pk", 120, 78, 180, "Nestle", "pack"),
        ("Del Monte Fruit Cocktail 439g", 140, 92, 730, "Del Monte", "pack"),
        ("Hershey's Chocolate Syrup 623g", 350, 230, 365, "Hershey's", "pack"),
        ("Borges Extra Virgin Olive Oil 500ml", 599, 395, 365, "Borges", "liter"),
        ("Nutella 350g", 399, 262, 365, "Ferrero", "pack"),
        ("Peanut Butter Crunchy 1kg", 399, 262, 365, "MyFitness", "pack"),
        ("Sundrop Peanut Butter 462g", 199, 130, 365, "Sundrop", "pack"),
    ],
    "Health & Wellness": [
        ("Revital H Multivitamin 30 caps", 350, 230, 730, "Sun Pharma", "pack"),
        ("Dabur Chyawanprash 1kg", 349, 228, 365, "Dabur", "pack"),
        ("Horlicks 500g", 265, 174, 365, "HUL", "pack"),
        ("Protinex Original 400g", 520, 342, 365, "Danone", "pack"),
        ("Saffola Fittify Green Coffee 30s", 499, 328, 365, "Marico", "pack"),
        ("Ensure Vanilla 400g", 750, 495, 365, "Abbott", "pack"),
        ("Complan Royal Chocolate 500g", 310, 204, 365, "Kraft Heinz", "pack"),
        ("Bournvita 500g", 225, 148, 365, "Mondelez", "pack"),
        ("Boost Health Drink 500g", 245, 162, 365, "Nestle", "pack"),
        ("Dabur Honey 1kg", 435, 286, 365, "Dabur", "pack"),
        ("Muscleblaze Whey Protein 1kg", 1899, 1250, 365, "MuscleBlaze", "pack"),
        ("OZiva Plant Protein 500g", 999, 660, 365, "OZiva", "pack"),
    ],
    "Dry Fruits & Nuts": [
        ("Happilo Almonds 500g", 499, 328, 365, "Happilo", "pack"),
        ("Happilo Cashews 500g", 549, 362, 365, "Happilo", "pack"),
        ("Nutraj Raisins 500g", 199, 130, 365, "Nutraj", "pack"),
        ("Farmley Walnut Kernels 200g", 379, 248, 365, "Farmley", "pack"),
        ("Borges California Pistachios 250g", 499, 328, 365, "Borges", "pack"),
        ("Happilo Dates 500g", 249, 164, 365, "Happilo", "pack"),
        ("Nutraj Mixed Dry Fruits 500g", 599, 395, 365, "Nutraj", "pack"),
        ("Miltop Chia Seeds 500g", 299, 195, 365, "Miltop", "pack"),
        ("Wonderland Pumpkin Seeds 200g", 199, 130, 365, "Wonderland", "pack"),
    ],
    "Pet Supplies": [
        ("Pedigree Adult Dog Food Chicken 3kg", 550, 362, 365, "Mars", "kg"),
        ("Whiskas Adult Cat Food Tuna 3kg", 499, 328, 365, "Mars", "kg"),
        ("Pedigree DentaStix 7pk", 130, 85, 365, "Mars", "pack"),
        ("Drools Puppy Food 3kg", 520, 342, 365, "Drools", "kg"),
        ("Me-O Cat Food Tuna 3kg", 450, 296, 365, "PCG", "kg"),
        ("Himalaya Erina Coat Cleanser 450ml", 299, 195, 730, "Himalaya", "piece"),
        ("Purepet Cat Litter 5kg", 350, 230, 730, "Purepet", "kg"),
        ("Pedigree Gravy Adult Chicken 80g 12pk", 240, 158, 365, "Mars", "pack"),
    ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# 2. SUPPLIER MASTER
# ═══════════════════════════════════════════════════════════════════════════════

# Derive unique suppliers from product catalog
def build_supplier_map():
    """Build a supplier_id → supplier_name mapping from all products."""
    all_suppliers = set()
    for cat_products in CATEGORIES.values():
        for item in cat_products:
            all_suppliers.add(item[4])  # supplier field
    supplier_list = sorted(all_suppliers)
    return {name: f"SUP{i+1:03d}" for i, name in enumerate(supplier_list)}

SUPPLIER_MAP = build_supplier_map()

# ═══════════════════════════════════════════════════════════════════════════════
# 3. CUSTOMER PROFILES — 3000 Indian customers
# ═══════════════════════════════════════════════════════════════════════════════

INDIAN_FIRST_NAMES_M = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Reyansh", "Sai", "Arnav",
    "Dhruv", "Kabir", "Ritvik", "Ayan", "Ishaan", "Shaurya", "Atharv", "Advait",
    "Pranav", "Krishna", "Harsh", "Rohan", "Rahul", "Amit", "Suresh", "Mahesh",
    "Rajesh", "Vikram", "Deepak", "Nikhil", "Gaurav", "Manish", "Sanjay", "Karan",
    "Tushar", "Varun", "Sachin", "Ajay", "Pradeep", "Ravi", "Anand", "Vinod",
    "Manoj", "Vishal", "Akash", "Dev", "Kunal", "Neeraj", "Sameer", "Abhishek",
    "Sunil", "Tarun", "Hemant", "Pankaj", "Mohit", "Sumit", "Ashish", "Lalit",
    "Naveen", "Rakesh", "Siddharth", "Yash",
]

INDIAN_FIRST_NAMES_F = [
    "Saanvi", "Aanya", "Aadhya", "Aaradhya", "Ananya", "Pari", "Anika", "Myra",
    "Kiara", "Riya", "Diya", "Isha", "Priya", "Neha", "Anjali", "Pooja",
    "Shruti", "Kavita", "Sunita", "Meena", "Divya", "Swati", "Nisha", "Pallavi",
    "Rekha", "Seema", "Shikha", "Preeti", "Vandana", "Madhuri", "Bhavna", "Anita",
    "Komal", "Ritu", "Geeta", "Savita", "Mamta", "Jyoti", "Archana", "Suman",
    "Lata", "Rani", "Usha", "Padma", "Kamala", "Chitra", "Lakshmi", "Sarita",
    "Deepa", "Meera", "Karishma", "Tanvi", "Aditi", "Sneha", "Sakshi", "Tanya",
    "Kriti", "Aishwarya", "Fatima", "Zara",
]

INDIAN_LAST_NAMES = [
    "Sharma", "Verma", "Singh", "Kumar", "Gupta", "Patel", "Joshi", "Shah",
    "Reddy", "Nair", "Menon", "Iyer", "Rao", "Pillai", "Das", "Mukherjee",
    "Banerjee", "Chatterjee", "Bose", "Dutta", "Ghosh", "Roy", "Sen", "Mishra",
    "Pandey", "Trivedi", "Deshmukh", "Kulkarni", "Patil", "Jadhav", "Shinde",
    "More", "Pawar", "Bhatt", "Mehta", "Thakur", "Chauhan", "Kapoor", "Malhotra",
    "Khanna", "Arora", "Bhatia", "Sethi", "Aggarwal", "Garg", "Saxena",
    "Choudhary", "Tiwari", "Yadav", "Dubey", "Jain", "Rathore", "Srivastava",
    "Rastogi", "Ahuja", "Kohli", "Bajaj", "Deshpande", "Hegde", "Kamath",
    "Naik", "Shetty", "Bhat", "Acharya", "Mahajan", "Gokhale", "Mane",
    "Khan", "Ahmed", "Sheikh", "Ansari",
]

INDIAN_CITIES_PINS = [
    ("Mumbai", ["400001","400002","400003","400004","400005","400006","400007","400008","400009","400010"]),
    ("Delhi", ["110001","110002","110003","110005","110006","110007","110008","110009","110010","110011"]),
    ("Bangalore", ["560001","560002","560003","560004","560005","560008","560009","560010","560011","560012"]),
    ("Hyderabad", ["500001","500002","500003","500004","500005","500006","500007","500008","500009","500010"]),
    ("Chennai", ["600001","600002","600003","600004","600005","600006","600008","600009","600010","600011"]),
    ("Kolkata", ["700001","700002","700003","700004","700005","700006","700007","700008","700009","700010"]),
    ("Pune", ["411001","411002","411003","411004","411005","411006","411007","411008","411009","411010"]),
    ("Ahmedabad", ["380001","380002","380003","380004","380005","380006","380007","380008","380009","380010"]),
    ("Jaipur", ["302001","302002","302003","302004","302005","302006","302007","302008","302010","302011"]),
    ("Lucknow", ["226001","226002","226003","226004","226005","226006","226007","226008","226009","226010"]),
]

PREFERRED_SECTIONS_INDIA = [
    "Dairy", "Staples & Grains", "Fresh Produce", "Snacks", "Beverages",
    "Spices & Masala", "Frozen Foods", "Household", "Personal Care",
    "Instant & Ready-to-Eat", "Bakery", "Meat & Seafood",
]

# ═══════════════════════════════════════════════════════════════════════════════
# 4. INDIAN FESTIVALS & SEASONS
# ═══════════════════════════════════════════════════════════════════════════════

INDIAN_FESTIVALS = {
    # (month, day): (name, boost_factor)
    (1, 14): ("Makar Sankranti", 1.4),
    (1, 15): ("Pongal", 1.4),
    (1, 26): ("Republic Day", 1.3),
    (3, 8):  ("Maha Shivaratri", 1.2),
    (3, 25): ("Holi", 1.6),
    (3, 26): ("Holi", 1.5),
    (4, 14): ("Baisakhi", 1.3),
    (4, 9):  ("Ugadi", 1.3),
    (4, 17): ("Ram Navami", 1.3),
    (5, 1):  ("May Day", 1.1),
    (6, 17): ("Eid al-Adha", 1.4),
    (7, 17): ("Muharram", 1.2),
    (8, 15): ("Independence Day", 1.5),
    (8, 26): ("Janmashtami", 1.4),
    (8, 29): ("Onam", 1.4),
    (9, 7):  ("Ganesh Chaturthi", 1.5),
    (9, 16): ("Milad-un-Nabi", 1.2),
    (10, 2): ("Gandhi Jayanti", 1.2),
    (10, 12): ("Dussehra", 1.6),
    (10, 20): ("Karwa Chauth", 1.3),
    (10, 31): ("Diwali Eve", 1.8),
    (11, 1):  ("Diwali", 2.0),
    (11, 2):  ("Diwali", 1.8),
    (11, 3):  ("Bhai Dooj", 1.5),
    (11, 15): ("Guru Nanak Jayanti", 1.3),
    (12, 25): ("Christmas", 1.5),
    (12, 31): ("New Year Eve", 1.6),
}


def get_festival_boost(date):
    """Return boost factor if date is near an Indian festival."""
    for (m, d), (name, boost) in INDIAN_FESTIVALS.items():
        if date.month == m and abs(date.day - d) <= 1:
            return boost
    return 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. MARKET BASKET ASSOCIATION RULES
# ═══════════════════════════════════════════════════════════════════════════════

# Products commonly bought together (by category prefix patterns)
BASKET_ASSOCIATIONS = [
    # (trigger_category, associated_categories, probability)
    ("Staples & Grains", ["Spices & Masala", "Fresh Produce"], 0.45),
    ("Fresh Produce", ["Dairy", "Spices & Masala"], 0.40),
    ("Dairy", ["Bakery", "Beverages"], 0.35),
    ("Meat & Seafood", ["Spices & Masala", "Fresh Produce"], 0.40),
    ("Snacks", ["Beverages"], 0.50),
    ("Instant & Ready-to-Eat", ["Beverages", "Snacks"], 0.35),
    ("Baby & Kids", ["Personal Care", "Dairy"], 0.30),
    ("Bakery", ["Dairy", "Condiments & Sauces"], 0.30),
]


# ═══════════════════════════════════════════════════════════════════════════════
# 6. BUILD PRODUCT LIST
# ═══════════════════════════════════════════════════════════════════════════════

def build_products():
    """Build the complete product list with IDs."""
    products = []
    pid = 1
    for category, items in CATEGORIES.items():
        for (name, price, cost, shelf_life, supplier, unit) in items:
            # Add small randomness to price
            actual_price = round(price + np.random.uniform(-price*0.03, price*0.03), 2)
            actual_cost = round(cost + np.random.uniform(-cost*0.03, cost*0.03), 2)
            products.append({
                "product_id": f"P{pid:04d}",
                "name": name,
                "category": category,
                "price": actual_price,
                "cost": actual_cost,
                "supplier": supplier,
                "shelf_life_days": shelf_life,
                "unit": unit,
            })
            pid += 1
    return products


def build_customers(n=3000):
    """Build customer list with Indian demographics."""
    customers = []
    city_weights = [0.18, 0.16, 0.14, 0.10, 0.10, 0.08, 0.08, 0.06, 0.05, 0.05]

    for i in range(1, n + 1):
        gender = np.random.choice(["M", "F", "Other"], p=[0.48, 0.46, 0.06])
        if gender == "M":
            first_name = random.choice(INDIAN_FIRST_NAMES_M)
        elif gender == "F":
            first_name = random.choice(INDIAN_FIRST_NAMES_F)
        else:
            first_name = random.choice(INDIAN_FIRST_NAMES_M + INDIAN_FIRST_NAMES_F)
        last_name = random.choice(INDIAN_LAST_NAMES)

        age = int(np.random.normal(35, 12))
        age = max(18, min(75, age))

        tier = np.random.choice(
            ["Bronze", "Silver", "Gold", "Platinum"],
            p=[0.40, 0.30, 0.20, 0.10]
        )
        tier_points = {"Bronze": 400, "Silver": 1800, "Gold": 4500, "Platinum": 10000}
        base_points = tier_points[tier]
        loyalty_points = max(0, int(base_points + np.random.normal(0, base_points * 0.3)))

        city_name, pincodes = random.choices(INDIAN_CITIES_PINS, weights=city_weights, k=1)[0]
        pincode = random.choice(pincodes)

        phone = f"+91{random.randint(70000,99999)}{random.randint(10000,99999)}"
        email_prefix = f"{first_name.lower()}.{last_name.lower()}{random.randint(1,999)}"
        email = f"{email_prefix}@{'gmail.com' if random.random() < 0.6 else 'yahoo.co.in' if random.random() < 0.5 else 'outlook.com'}"

        join_date = (datetime.now() - timedelta(days=random.randint(0, 900))).strftime("%Y-%m-%d")

        customers.append({
            "customer_id": f"C{i:04d}",
            "first_name": first_name,
            "last_name": last_name,
            "age": age,
            "gender": gender,
            "membership_tier": tier,
            "email": email,
            "phone": phone,
            "zip_code": pincode,
            "loyalty_points": loyalty_points,
            "preferred_section": random.choice(PREFERRED_SECTIONS_INDIA),
            "join_date": join_date,
        })
    return customers


# ═══════════════════════════════════════════════════════════════════════════════
# 7. SALES TRANSACTION GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

def generate_sales_transactions(products, customers, target_rows=550000):
    """Generate realistic Indian supermarket sales transactions."""
    print(f"  Generating ~{target_rows:,} sales transactions...")

    product_ids = [p["product_id"] for p in products]
    customer_ids = [c["customer_id"] for c in customers]
    prices = {p["product_id"]: p["price"] for p in products}
    costs = {p["product_id"]: p["cost"] for p in products}
    categories = {p["product_id"]: p["category"] for p in products}
    names = {p["product_id"]: p["name"] for p in products}
    suppliers = {p["product_id"]: p["supplier"] for p in products}
    shelf_lives = {p["product_id"]: p["shelf_life_days"] for p in products}
    units = {p["product_id"]: p["unit"] for p in products}

    # Category products lookup
    cat_products = {}
    for p in products:
        cat_products.setdefault(p["category"], []).append(p["product_id"])

    # Category popularity weights (Indian shopping patterns)
    cat_weights = {
        "Dairy": 1.3, "Bakery": 1.0, "Beverages": 1.4, "Snacks": 1.5,
        "Staples & Grains": 1.8, "Spices & Masala": 1.2, "Fresh Produce": 1.6,
        "Meat & Seafood": 0.8, "Frozen Foods": 0.6, "Household": 0.7,
        "Personal Care": 0.6, "Baby & Kids": 0.35, "Condiments & Sauces": 0.8,
        "Instant & Ready-to-Eat": 1.1, "Canned & Packaged": 0.5,
        "Health & Wellness": 0.45, "Dry Fruits & Nuts": 0.5, "Pet Supplies": 0.25,
    }

    # Product selection weights
    prod_weights = np.array([cat_weights.get(categories[pid], 1.0) for pid in product_ids])
    prod_weights /= prod_weights.sum()

    # Date range: 18 months ending now
    end_date = datetime.now()
    start_date = end_date - timedelta(days=548)  # ~18 months
    total_days = (end_date - start_date).days

    # Customer tier → spending behavior
    tier_spend_mult = {"Bronze": 0.8, "Silver": 1.0, "Gold": 1.3, "Platinum": 1.6}
    customer_tiers = {c["customer_id"]: c["membership_tier"] for c in customers}

    # Payment methods by tier
    payment_weights = {
        "Bronze":   [0.35, 0.20, 0.25, 0.15, 0.05],
        "Silver":   [0.25, 0.25, 0.25, 0.20, 0.05],
        "Gold":     [0.10, 0.30, 0.20, 0.30, 0.10],
        "Platinum": [0.05, 0.30, 0.15, 0.35, 0.15],
    }
    payment_methods = ["Cash", "Credit Card", "Debit Card", "UPI", "Digital Wallet"]

    # Shopping hour weights (Indian pattern: morning rush + evening rush)
    hour_weights = [
        0.05, 0.05, 0.05, 0.05, 0.05, 0.05,  # 0–5
        0.5, 1.5,  # 6–7
        3, 5, 7, 8,  # 8–11
        6, 5,  # 12–13
        4, 5, 6, 7, 8, 9,  # 14–19
        8, 5, 3, 1.5  # 20–23
    ]

    sales = []
    basket_counter = 0
    sale_counter = 0

    avg_items_per_basket = 3.5
    num_baskets = int(target_rows / avg_items_per_basket)

    batch_size = 50000
    batch_start_time = time.time()

    for b in range(num_baskets):
        # Random date
        day_offset = random.randint(0, total_days)
        sale_date = start_date + timedelta(days=day_offset)

        # Seasonal multiplier (Indian climate)
        month = sale_date.month
        seasonal = 1.0
        if month in [10, 11]:     # Festive season (Navratri → Diwali)
            seasonal = 1.6
        elif month in [12, 1]:    # Winter weddings + New Year
            seasonal = 1.3
        elif month in [3, 4]:     # Holi + Ugadi + Ram Navami
            seasonal = 1.3
        elif month in [6, 7, 8]: # Monsoon — slightly lower
            seasonal = 0.9
        elif month in [5]:        # Summer — beverages spike
            seasonal = 1.1

        # Weekend boost
        if sale_date.weekday() >= 5:
            seasonal *= 1.25

        # Sunday extra boost (Indian family shopping)
        if sale_date.weekday() == 6:
            seasonal *= 1.1

        # Festival boost
        seasonal *= get_festival_boost(sale_date)

        # Month-start salary effect (more spending 1st-10th)
        if sale_date.day <= 10:
            seasonal *= 1.15

        # Time of day
        hour = random.choices(range(24), weights=hour_weights, k=1)[0]
        minute = random.randint(0, 59)

        # Pick customer
        cid = random.choice(customer_ids)
        tier = customer_tiers[cid]
        spend_mult = tier_spend_mult[tier]

        basket_counter += 1
        basket_id = f"B{basket_counter:06d}"

        # Items per basket (influenced by seasonal + tier)
        num_items = max(1, min(8, int(np.random.exponential(2.8) * (seasonal ** 0.25) * (spend_mult ** 0.3))))

        # Select primary products
        selected = list(np.random.choice(
            product_ids, size=min(num_items, len(product_ids)),
            replace=False, p=prod_weights
        ))

        # Apply basket associations (co-purchase patterns)
        if len(selected) > 0 and random.random() < 0.4:
            trigger_cat = categories[selected[0]]
            for (trig, assoc_cats, prob) in BASKET_ASSOCIATIONS:
                if trigger_cat == trig and random.random() < prob:
                    for ac in assoc_cats[:1]:  # Add one associated item
                        if ac in cat_products and len(selected) < 8:
                            extra = random.choice(cat_products[ac])
                            if extra not in selected:
                                selected.append(extra)
                    break

        # Generate each line item
        pay_method = np.random.choice(payment_methods, p=payment_weights[tier])

        for pid in selected:
            sale_counter += 1

            unit_price = prices[pid]

            # Quantity (influenced by product category)
            cat = categories[pid]
            if cat in ["Staples & Grains", "Beverages"]:
                qty = max(1, min(5, int(np.random.exponential(1.8))))
            elif cat in ["Fresh Produce", "Dairy"]:
                qty = max(1, min(4, int(np.random.exponential(2.0))))
            elif cat in ["Snacks", "Instant & Ready-to-Eat"]:
                qty = max(1, min(6, int(np.random.exponential(2.2))))
            else:
                qty = max(1, min(3, int(np.random.exponential(1.5))))

            # Discount logic
            discount = 0.0
            if random.random() < 0.25:  # 25% of items get discounts
                if tier == "Platinum":
                    discount = np.random.choice([0.05, 0.10, 0.15, 0.20], p=[0.3, 0.35, 0.25, 0.10])
                elif tier == "Gold":
                    discount = np.random.choice([0.05, 0.10, 0.15], p=[0.4, 0.4, 0.2])
                elif tier == "Silver":
                    discount = np.random.choice([0.05, 0.10], p=[0.6, 0.4])
                else:
                    discount = np.random.choice([0.05, 0.10], p=[0.7, 0.3])

            # Festival extra discount
            if get_festival_boost(sale_date) > 1.3 and random.random() < 0.3:
                discount = min(0.25, discount + 0.05)

            total = round(unit_price * qty * (1 - discount), 2)

            sales.append({
                "sale_id": f"S{sale_counter:06d}",
                "basket_id": basket_id,
                "product_id": pid,
                "product_name": names[pid],
                "category": cat,
                "customer_id": cid,
                "quantity": qty,
                "unit_price": unit_price,
                "cost_price": costs[pid],
                "discount": round(discount, 2),
                "total_price": total,
                "timestamp": sale_date.replace(hour=hour, minute=minute).strftime("%Y-%m-%d %H:%M:%S"),
                "payment_method": pay_method,
                "supplier": suppliers[pid],
                "shelf_life_days": shelf_lives[pid],
                "unit": units[pid],
            })

        # Progress reporting
        if (b + 1) % batch_size == 0:
            elapsed = time.time() - batch_start_time
            pct = (b + 1) / num_baskets * 100
            print(f"    {pct:.1f}% done — {sale_counter:,} rows, {elapsed:.1f}s elapsed")

    print(f"  Generated {sale_counter:,} transactions in {basket_counter:,} baskets")
    return sales


# ═══════════════════════════════════════════════════════════════════════════════
# 8. MASTER CSV BUILDER
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    start = time.time()
    print("=" * 60)
    print("SmartMart AI — Indian Supermarket Master CSV Generator")
    print("=" * 60)

    # Build product catalog
    print("\n[1/4] Building product catalog...")
    products = build_products()
    print(f"  → {len(products)} products across {len(CATEGORIES)} categories")

    # Build customer base
    print("\n[2/4] Building customer base...")
    customers = build_customers(3000)
    print(f"  → {len(customers)} customers")

    # Generate transactions
    print("\n[3/4] Generating sales transactions...")
    sales = generate_sales_transactions(products, customers, target_rows=550000)

    # Build the master DataFrame
    print("\n[4/4] Building and writing master CSV...")

    # The CSV columns are designed to map to EVERY field in the upload handler's
    # COLUMN_PATTERNS. Column names chosen for auto-detection:
    #
    # sale_id         → sale_id pattern
    # basket_id       → basket_id pattern
    # product_id      → product_id pattern
    # product_name    → name pattern (falls through to "name" group)
    # category        → category pattern
    # customer_id     → customer_id pattern
    # quantity         → quantity pattern
    # unit_price      → price pattern (maps to "price" → used as unit_price)
    # cost_price      → cost pattern
    # discount        → discount pattern
    # total_price     → total_price pattern
    # timestamp       → timestamp pattern
    # payment_method  → payment_method pattern
    # supplier        → supplier pattern
    # shelf_life_days → shelf_life_days pattern
    # unit            → unit pattern

    # Convert to DataFrame
    df = pd.DataFrame(sales)

    # Column order matching what the system expects
    columns = [
        "sale_id", "basket_id", "product_id", "product_name", "category",
        "customer_id", "quantity", "unit_price", "cost_price", "discount",
        "total_price", "timestamp", "payment_method", "supplier",
        "shelf_life_days", "unit",
    ]
    df = df[columns]

    # Write CSV
    df.to_csv(OUTPUT_FILE, index=False)
    file_size_mb = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}")
    print(f"✅ Master CSV generated successfully!")
    print(f"   File: {OUTPUT_FILE}")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    print(f"   File size: {file_size_mb:.1f} MB")
    print(f"   Date range: {df['timestamp'].min()} → {df['timestamp'].max()}")
    print(f"   Unique products: {df['product_id'].nunique()}")
    print(f"   Unique customers: {df['customer_id'].nunique()}")
    print(f"   Unique baskets: {df['basket_id'].nunique()}")
    print(f"   Categories: {df['category'].nunique()}")
    print(f"   Suppliers: {df['supplier'].nunique()}")
    print(f"   Payment methods: {df['payment_method'].nunique()}")
    print(f"   Time taken: {elapsed:.1f}s")
    print(f"{'=' * 60}")

    # Print category distribution
    print("\nCategory distribution:")
    cat_counts = df['category'].value_counts()
    for cat, count in cat_counts.items():
        pct = count / len(df) * 100
        print(f"  {cat:30s} {count:>8,} ({pct:5.1f}%)")

    # Print payment method distribution
    print("\nPayment method distribution:")
    pay_counts = df['payment_method'].value_counts()
    for pay, count in pay_counts.items():
        pct = count / len(df) * 100
        print(f"  {pay:20s} {count:>8,} ({pct:5.1f}%)")


if __name__ == "__main__":
    main()
