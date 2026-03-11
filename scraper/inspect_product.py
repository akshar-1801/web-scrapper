import requests

url = "https://www.1mg.com/otc/protinex-high-quality-protein-nutritional-drink-for-immunity-strength-zero-added-sugar-creamy-vanilla-powder-otc900814"
headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
with open("product_page.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print(f"Saved to product_page.html. Size: {len(response.text)} bytes")
