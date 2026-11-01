import json
import os

class MockOdooDB:
    def __init__(self, filepath="seed_data.json"):
        self.products_by_sku = {}
        self.products_by_id = {}
        self.inventory = []
        self.kb_docs = []
        
        # Graceful error handling in case the file is missing
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found. Running with empty database.")
            return

        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Optimized dictionary comprehensions for O(1) lookups
        products = data.get("products", [])
        self.products_by_sku = {p["sku"]: p for p in products}
        self.products_by_id = {p["product_id"]: p for p in products}
        
        # Lists for inventory and KB search
        self.inventory = data.get("inventory", [])
        self.kb_docs = data.get("kb_docs", [])

    def get_product_by_id(self, product_id: int):
        """Helper method to safely fetch a product."""
        return self.products_by_id.get(product_id)
        
    def get_product_by_sku(self, sku: str):
        """Helper method to safely fetch a product by SKU."""
        return self.products_by_sku.get(sku)

# Initialize a global singleton instance. 
# tools.py will import this specific instance using: `from data_store import db`
db = MockOdooDB()