Future Expansion Plan: AI Health Assistant
Feature: "AI Pharmacist & Product Comparator"
The goal is to transform the dashboard from a passive data viewer into an active decision-support tool.

1. New UI Component: "AI Assistant" Tab
We will add a third tab dedicated to AI interactions.

A. Smart Comparison
User Action: Select 2-3 products from a dropdown (e.g., "Tata 1mg Multivitamin" vs "Revital H").
AI Output: A structured table comparison:
Price per Unit: Calculator (e.g., ₹5/tablet vs ₹8/tablet).
Value Analysis: "Product A is 30% cheaper but has lower user ratings."
Suitability: "Product A is better for general immunity, while Product B focuses on energy."
B. "When to Use?" Consultant
User Action: Select a specific product and ask "When should I take this?" or "Is this safe for seniors?"
AI Output: Summarized guidance based on product metadata and general medical knowledge.
Disclaimer: "I am an AI, not a doctor. Consult a physician before use."
2. Prerequisite: Data Enrichment (The "Detail Crawler")
Technical Challenge: The main listing API does not provide ingredients. Solution: We must build a secondary "Enrichment Scraper".

Phase 1 (Light): Continue scraping listings for Name/Price/Rating (Fast).

Phase 2 (Deep): A background process that picks products from the DB and visits their url one-by-one to extract:

Key Ingredients
Safety Information
Directions for Use
Performance Impact: Scraping 5,000 products will require 5,000 extra requests. We should run this:

Slowly in the background (1 request/3 seconds).
On-demand (only when a user asks about a specific product).
3. Technical Implementation Strategy
LLM Integration: Use OpenAI API (gpt-4o-mini) or Google Gemini API.
Context Injection:
System: You are a helpful medical assistant.
Context: User is asking about [Product Name]. 
Price: [Price], Rating: [Rating].
Question: [User Query]
Streamlit Chat: Use st.chat_message for a conversational interface.
4. Safety & Compliance
Guardrails: The AI must refuse to prescribe dosage for prescription drugs.
Hallucination Check: Strictly ground answers in the scraped data.