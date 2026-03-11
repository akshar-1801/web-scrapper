import os
from dotenv import load_dotenv
import google.generativeai as genai
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

class AIHelper:
    def __init__(self):
        self.provider = None
        self.model = None
        
        # Check for API keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.google_key = os.getenv("GOOGLE_API_KEY")
        
        if self.openai_key:
            self.provider = "openai"
            self.client = OpenAI(api_key=self.openai_key)
            self.model = "gpt-3.5-turbo" # Cost-effective default
        elif self.google_key:
            self.provider = "google"
            genai.configure(api_key=self.google_key)
            self.model = "gemini-2.5-flash"
        
    def is_configured(self):
        return self.provider is not None

    def get_response(self, system_prompt, user_query):
        if not self.is_configured():
            return "AI API Key not configured. Please add OPENAI_API_KEY or GOOGLE_API_KEY to .env file."
            
        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_query}
                    ]
                )
                return response.choices[0].message.content
                
            elif self.provider == "google":
                model = genai.GenerativeModel(self.model)
                # Gemini doesn't have system prompts in the same way, we can prepend it
                full_prompt = f"{system_prompt}\n\nUser Query: {user_query}"
                response = model.generate_content(full_prompt)
                return response.text
                
        except Exception as e:
            return f"Error calling AI API: {str(e)}"

    def compare_products(self, products_data):
        """
        products_data: List of dictionaries containing product details
        """
        if not products_data:
            return "No products selected for comparison."
            
        system_prompt = """
        You are a helpful health assistant. verify the following products based on their descriptions, ingredients, and key benefits.
        Highlight the key differences, pros, and cons of each.
        Recommend which product is better suited for specific needs (e.g. price sensitive, specific ingredients).
        Format the response in Markdown.
        """
        
        # Format product data for the prompt
        products_str = ""
        for i, p in enumerate(products_data):
            products_str += f"\n\nProduct {i+1}: {p.get('name')}\n"
            products_str += f"Price: {p.get('price')}\n"
            products_str += f"Rating: {p.get('rating')} ({p.get('rating_count')} reviews)\n"
            products_str += f"Description: {p.get('description')}\n"
            products_str += f"Key Ingredients: {p.get('key_ingredients')}\n"
        
        return self.get_response(system_prompt, products_str)

    def consult_health(self, query, product_context=None):
        """
        query: User's question
        product_context: Dictionary of the currently viewed product (optional)
        """
        system_prompt = """
        You are a cautious and helpful health assistant. Answer the user's question about health supplements or medicines.
        ALWAYS include a disclaimer that you are an AI and this is not medical advice.
        If a product context is provided, answer specifically regarding that product.
        """
        
        user_input = query
        if product_context:
            user_input += f"\n\nContext - Selected Product: {product_context.get('name')}\nDetails: {product_context}"
            
        return self.get_response(system_prompt, user_input)
