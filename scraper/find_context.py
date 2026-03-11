with open("product_page.html", "r", encoding="utf-8") as f:
    text = f.read()

index = text.find("Key Ingredients")
if index != -1:
    start = max(0, index - 500)
    end = min(len(text), index + 500)
    print(f"Context around 'Key Ingredients':\n{text[start:end]}")
else:
    print("'Key Ingredients' not found")
