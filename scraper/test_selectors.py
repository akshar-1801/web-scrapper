import scrapy
from scrapy.http import HtmlResponse

with open("product_page.html", "r", encoding="utf-8") as f:
    html = f.read()

response = HtmlResponse(url="http://example.com", body=html, encoding='utf-8')

def extract_details(response):
    details = {}
    
    # helper to find text after a header
    # The structure seems to be <b>Header:</b> Text... or <div><b>Header</b></div>...
    
    # Let's look for "Key Ingredients"
    # It might be in a div that contains "Key Ingredients"
    
    # Approach 1: Find the node containing the text, then get the next siblings or parent's text
    
    # Using xpath to find the bold tag with "Key Ingredients"
    key_ingredients_header = response.xpath("//strong[contains(text(), 'Key Ingredients')] | //b[contains(text(), 'Key Ingredients')]")
    if key_ingredients_header:
        # The text might be in the following sibling or text node
        # In the soup output, it was followed by the ingredients list.
        # Let's try to get the text of the parent container
        container = key_ingredients_header.xpath("./..")
        details['key_ingredients'] = " ".join(container.xpath(".//text()").getall()).strip()
        
        # But this might include the header itself.
        # Let's try to be more precise if possible, but for now capturing the block is good.
    
    # Let's inspect the Product Description
    # Usually under "Information about..." or "Product highlights"
    description_header = response.xpath("//h2[contains(text(), 'Product highlights')]") # or similar
    if description_header:
         details['description'] = " ".join(description_header.xpath("./following-sibling::ul[1]//text()").getall()).strip()

    # Safety Information
    safety_header = response.xpath("//strong[contains(text(), 'Safety Information')] | //b[contains(text(), 'Safety Information')]")
    if safety_header:
        container = safety_header.xpath("./..")
        details['safety_information'] = " ".join(container.xpath(".//text()").getall()).strip()
        
    # Directions
    directions_header = response.xpath("//strong[contains(text(), 'Directions')] | //b[contains(text(), 'Directions')]")
    if directions_header:
        container = directions_header.xpath("./..")
        details['directions_for_use'] = " ".join(container.xpath(".//text()").getall()).strip()

    return details

details = extract_details(response)
print("Extracted Details:", details)

# Also try to print the HTML around "Key Ingredients" to debug if empty
print("\nHTML around Key Ingredients:")
key_ing = response.xpath("//*[contains(text(), 'Key Ingredients')]")
if key_ing:
    print(key_ing[0].get())
else:
    print("Key Ingredients header not found with xpath")
