with open("product_page.html", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "Key Ingredients" in line:
        print(f"Found 'Key Ingredients' on line {i+1}")
        print(f"Content: {line.strip()[:100]}...")
