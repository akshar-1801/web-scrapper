import requests
import json

url = "https://www.1mg.com/pwa-api/api/v5/category/194?page=1&per_page=20"
headers = {
    "x-city": "Mumbai",
    "x-requested-with": "XMLHttpRequest",
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.get(url, headers=headers)
    data = response.json()
    
    widgets = data.get('data', {}).get('widgets', [])
    for widget in widgets:
        if widget.get('type') == 'sku_card':
            print(json.dumps(widget, indent=2))
            break
except Exception as e:
    print(f"Error: {e}")
