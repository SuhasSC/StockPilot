from datetime import date, timedelta
from pathlib import Path
from pymongo import MongoClient
from pymongo.errors import PyMongoError
import random

random.seed(42)

client = MongoClient(
    "mongodb://127.0.0.1:27017",
    serverSelectionTimeoutMS=5000
)
client.admin.command("ping")
db = client["LLM_DB"]

COLLECTIONS = [
    "products", "inventory", "sales",
    "suppliers", "nl_query_examples"
]
TARGET = 200

# Safety check: do not start if any collection is already over target.
counts = {name: db[name].count_documents({}) for name in COLLECTIONS}
print("Current counts:", counts)

if any(count > TARGET for count in counts.values()):
    raise SystemExit(
        "Stopped safely: a collection already exceeds 200 records. "
        "No records were inserted."
    )

# Existing documents are retained. Use unique IDs for new records.
categories = {
    "Electronics": [
        ("Wireless Mouse", 799), ("Mechanical Keyboard", 2499),
        ("USB-C Hub", 1499), ("Webcam", 1899),
        ("Bluetooth Speaker", 1299), ("Monitor", 8999),
        ("Laptop Stand", 999), ("Power Bank", 1599),
        ("Headphones", 1999), ("HDMI Cable", 399),
    ],
    "Furniture": [
        ("Office Chair", 5499), ("Study Desk", 6999),
        ("Bookshelf", 3299), ("Filing Cabinet", 4499),
        ("Footrest", 899),
    ],
    "Stationery": [
        ("Notebook Pack", 299), ("Ball Pen Set", 149),
        ("A4 Paper Ream", 349), ("Whiteboard Marker", 199),
        ("Stapler", 249), ("File Folder Pack", 199),
    ],
    "Networking": [
        ("Wi-Fi Router", 2499), ("Ethernet Switch", 1999),
        ("LAN Cable", 299), ("USB Wi-Fi Adapter", 699),
    ],
    "Accessories": [
        ("Laptop Backpack", 1799), ("Mouse Pad", 249),
        ("Laptop Sleeve", 899), ("Cable Organizer", 199),
    ],
}

cities = [
    "Bengaluru", "Mysuru", "Davanagere", "Hubballi",
    "Mangaluru", "Belagavi", "Shivamogga", "Tumakuru",
    "Udupi", "Hassan"
]
warehouses = ["WH001", "WH002", "WH003", "WH004", "WH005"]

# Create exactly 200 supplier documents representing 20 supplier
# organizations with 10 branch/contract records per organization.
supplier_names = [
    "Apex Supplies", "Bharat Tech Traders", "Cauvery Distributors",
    "Deccan Office Solutions", "Evergreen Electronics",
    "Falcon Industrial Supply", "Galaxy Business Products",
    "Horizon Tech Supply", "Indus Retail Partners",
    "Jupiter Office Goods", "Kaveri Components",
    "Lotus Digital Supplies", "Metro Wholesale",
    "Nova Equipment House", "Orchid Enterprises",
    "Prime Workspaces", "Quantum Devices",
    "Reliable Stationers", "Southern Tech Mart",
    "Trident Distribution"
]

supplier_docs = []
for i in range(200):
    org_no = i % 20 + 1
    branch_no = i // 20 + 1
    supplier_docs.append({
        "supplier_record_id": f"SREC{i+1:03d}",
        "supplier_id": f"SUP{org_no:03d}",
        "name": supplier_names[org_no - 1],
        "branch_id": f"BR{branch_no:02d}",
        "category_focus": list(categories.keys())[org_no % len(categories)],
        "city": cities[i % len(cities)],
        "state": "Karnataka",
        "country": "India",
        "email": f"supplier{org_no:03d}.branch{branch_no:02d}@example.com",
        "phone": f"+91-90000{org_no:05d}",
        "status": "active" if org_no % 8 else "under_review",
        "created_date": (date(2025, 1, 1) + timedelta(days=i)).isoformat(),
    })

# Insert only missing supplier records, without deleting existing ones.
existing_supplier_records = {
    doc["supplier_record_id"]
    for doc in db["suppliers"].find(
        {"supplier_record_id": {"$exists": True}},
        {"supplier_record_id": 1}
    )
}
new_supplier_docs = [
    doc for doc in supplier_docs
    if doc["supplier_record_id"] not in existing_supplier_records
]
needed = TARGET - counts["suppliers"]
if len(new_supplier_docs) < needed:
    raise RuntimeError("Not enough unique supplier records to reach target.")
if needed:
    db["suppliers"].insert_many(new_supplier_docs[:needed])

supplier_ids = [f"SUP{i:03d}" for i in range(1, 21)]

# Preserve existing products and create missing product IDs.
product_docs = []
catalog = [
    (name, category, price)
    for category, items in categories.items()
    for name, price in items
]
existing_product_ids = {
    doc["product_id"]
    for doc in db["products"].find({}, {"product_id": 1})
}
for n in range(1001, 1201):
    product_id = f"P{n}"
    if product_id in existing_product_ids:
        continue
    name, category, base_price = catalog[(n - 1001) % len(catalog)]
    product_docs.append({
        "product_id": product_id,
        "name": f"{name} {((n - 1001) // len(catalog)) + 1:02d}",
        "category": category,
        "price": base_price,
        "description": f"{name} for business and office use",
        "supplier_id": supplier_ids[(n - 1001) % len(supplier_ids)],
        "created_date": (
            date(2025, 1, 1) + timedelta(days=n - 1001)
        ).isoformat(),
    })

needed = TARGET - counts["products"]
if len(product_docs) < needed:
    raise RuntimeError("Not enough product records to reach target.")
if needed:
    db["products"].insert_many(product_docs[:needed])

# Build inventory for products that do not yet have inventory.
existing_inventory_products = {
    doc["product_id"]
    for doc in db["inventory"].find({}, {"product_id": 1})
}
product_ids = [
    doc["product_id"]
    for doc in db["products"].find({}, {"product_id": 1}).sort("product_id", 1)
]
inventory_docs = []
for i, product_id in enumerate(product_ids):
    if product_id in existing_inventory_products:
        continue
    reorder_level = random.choice([5, 8, 10, 12, 15, 20])
    stock = random.randint(0, 80)
    warehouse = warehouses[i % len(warehouses)]
    city = cities[i % len(cities)]
    inventory_docs.append({
        "product_id": product_id,
        "warehouse_id": warehouse,
        "stock_quantity": stock,
        "reorder_level": reorder_level,
        "location": city,
        "warehouse_location": city,
        "last_updated": (
            date(2026, 1, 1) + timedelta(days=i % 297)
        ).isoformat(),
    })

needed = TARGET - counts["inventory"]
if len(inventory_docs) < needed:
    raise RuntimeError("Not enough inventory records to reach target.")
if needed:
    db["inventory"].insert_many(inventory_docs[:needed])

# Create 200 sales transactions with valid product references.
existing_sale_ids = {
    doc["sale_id"]
    for doc in db["sales"].find(
        {"sale_id": {"$exists": True}}, {"sale_id": 1}
    )
}
product_map = {
    doc["product_id"]: doc
    for doc in db["products"].find({}, {"_id": 0})
}
all_product_ids = sorted(product_map)
sales_docs = []

for n in range(1, 201):
    sale_id = f"SALE{n:04d}"
    if sale_id in existing_sale_ids:
        continue
    product_id = all_product_ids[(n - 1) % len(all_product_ids)]
    product = product_map[product_id]
    quantity = random.randint(1, 5)
    sale_date = date(2026, 1, 1) + timedelta(days=(n * 3) % 297)
    sales_docs.append({
        "sale_id": sale_id,
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_price": product["price"],
        "total_amount": quantity * product["price"],
        "sale_date": sale_date.isoformat(),
        "city": cities[n % len(cities)],
        "status": random.choice(["completed", "completed", "completed", "returned"]),
    })

needed = TARGET - counts["sales"]
if len(sales_docs) < needed:
    raise RuntimeError("Not enough sale IDs to reach target.")
if needed:
    db["sales"].insert_many(sales_docs[:needed])

# Generate 200 distinct natural-language examples for the existing
# semantic search schema: question, collection, filter, description.
query_templates = [
    ("Show all products", "products", {}, "List all products"),
    ("Show all electronics", "products", {"category": "Electronics"}, "Filter products by category"),
    ("Show all furniture", "products", {"category": "Furniture"}, "Filter furniture products"),
    ("Find products below {price} rupees", "products", {"price": {"$lt": 1000}}, "Find products below a price"),
    ("Find products above {price} rupees", "products", {"price": {"$gt": 2000}}, "Find products above a price"),
    ("Show products supplied by {supplier}", "products", {"supplier_id": "SUP001"}, "Filter products by supplier"),
    ("Show products in the {category} category", "products", {"category": "Stationery"}, "Filter products by category"),
    ("Find products costing at least {price} rupees", "products", {"price": {"$gte": 1500}}, "Find products by minimum price"),
    ("Show inventory with low stock", "inventory", {"$expr": {"$lte": ["$stock_quantity", "$reorder_level"]}}, "Find stock at or below reorder level"),
    ("Show inventory with stock above {qty}", "inventory", {"stock_quantity": {"$gt": 20}}, "Find inventory above a quantity"),
    ("Find inventory in {city}", "inventory", {"location": "Bengaluru"}, "Filter inventory by location"),
    ("Show products with stock below {qty}", "inventory", {"stock_quantity": {"$lt": 10}}, "Find inventory below a quantity"),
    ("Find inventory at warehouse {warehouse}", "inventory", {"warehouse_id": "WH001"}, "Filter inventory by warehouse"),
    ("Show inventory with at least {qty} items", "inventory", {"stock_quantity": {"$gte": 15}}, "Find inventory by minimum quantity"),
    ("Find inventory needing reorder", "inventory", {"$expr": {"$lte": ["$stock_quantity", "$reorder_level"]}}, "Identify products requiring reorder"),
]

examples = []
for i in range(200):
    template, collection, query_filter, description = query_templates[i % len(query_templates)]
    price = [500, 1000, 1500, 2000, 3000][i % 5]
    qty = [5, 10, 15, 20, 25][i % 5]
    supplier = supplier_ids[i % len(supplier_ids)]
    category = list(categories.keys())[i % len(categories)]
    city = cities[i % len(cities)]
    warehouse = warehouses[i % len(warehouses)]
    question = template.format(
        price=price, qty=qty, supplier=supplier,
        category=category, city=city, warehouse=warehouse
    )
    # Ensure each question is distinct while retaining a natural-language example.
    question = f"{question} (example {i+1:03d})"
    examples.append({
        "example_id": f"NLQ{i+1:04d}",
        "question": question,
        "collection": collection,
        "filter": query_filter,
        "description": description,
    })

existing_example_ids = {
    doc["example_id"]
    for doc in db["nl_query_examples"].find(
        {"example_id": {"$exists": True}}, {"example_id": 1}
    )
}
new_examples = [
    doc for doc in examples if doc["example_id"] not in existing_example_ids
]
needed = TARGET - counts["nl_query_examples"]
if len(new_examples) < needed:
    raise RuntimeError("Not enough query examples to reach target.")
if needed:
    db["nl_query_examples"].insert_many(new_examples[:needed])

# Final verification.
print("\n===== FINAL COLLECTION COUNTS =====")
failed = False
for name in COLLECTIONS:
    count = db[name].count_documents({})
    print(f"{name}: {count}")
    if count != TARGET:
        failed = True

print("\nDistinct supplier organizations represented:",
      db["suppliers"].distinct("supplier_id").__len__())
print("Products with inventory:",
      db["inventory"].distinct("product_id").__len__())

client.close()

if failed:
    raise SystemExit(
        "Some collections did not reach exactly 200. "
        "No existing records were deleted; inspect the counts above."
    )

print("\nSUCCESS: all five collections contain exactly 200 documents.")
