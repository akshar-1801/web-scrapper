import requests
import json

url = "https://www.1mg.com/pwa-api/api/v5/category/1?page=1&per_page=20"
headers = {
    "x-city": "Mumbai",
    "x-requested-with": "XMLHttpRequest",
    "accept": "application/json",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    print(f"Fetching {url}...")
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Root Keys:", list(data.keys()))
        
        if 'data' in data:
            print("Data Keys:", list(data['data'].keys()))
            
            if 'skus' in data['data']:
                print(f"Found 'skus' with {len(data['data']['skus'])} items")
                if len(data['data']['skus']) > 0:
                    print("Sample Item Keys:", list(data['data']['skus'][0].keys()))
            else:
                print("'skus' not found in data")
                
            if 'products' in data['data']:
                print(f"Found 'products' with {len(data['data']['products'])} items")
        else:
            print("'data' key not found in response")
            
        # Dump a small part to file for inspection if needed
        with open("debug_api_dump.json", "w") as f:
            json.dump(data, f, indent=2)
            print("Dumped response to debug_api_dump.json")
    else:
        print("Response Text:", response.text[:500])
        
except Exception as e:
    print(f"Error: {e}")
