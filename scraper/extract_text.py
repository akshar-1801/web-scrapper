from bs4 import BeautifulSoup
import re

with open("product_page.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
text = soup.get_text(separator="\n")

# filter out empty lines
lines = [line.strip() for line in text.split("\n") if line.strip()]

with open("product_text.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Extracted {len(lines)} lines of text.")
