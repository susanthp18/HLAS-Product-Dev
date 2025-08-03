"""
Intent Router Agent

The intelligent switchboard operator that analyzes user queries and routes them
to the appropriate specialized agents based on intent classification.
"""

import json
import re
from typing import Optional, List, Dict, Any
import google.generativeai as genai

from .models import IntentClassification, PrimaryIntent, PRODUCT_MAPPING, COMMON_ENTITIES
from config import Config


class IntentRouterAgent:
    """
    Intent Router Agent for HL Assurance
    
    Analyzes user queries to determine:
    - Primary intent (what the user wants to do)
    - Product focus (which insurance products are relevant)
    - Key entities (important concepts mentioned)
    - Purchase intent flag
    """
    
    def __init__(self, gemini_api_key: str = None):
        """Initialize the Intent Router Agent"""
        self.gemini_api_key = gemini_api_key or Config.GEMINI_API_KEY
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel(Config.GENERATION_MODEL)
        
        # Known products
        self.products = ["Car", "Early", "Family", "Home", "Hospital", "Maid", "Travel"]
        
    def classify_intent(self, user_query: str) -> IntentClassification:
        """
        Classify user intent and extract relevant information
        
        Args:
            user_query: Raw user query string
            
        Returns:
            IntentClassification object with structured analysis
        """
        try:
            # Get LLM classification
            llm_result = self._get_llm_classification(user_query)
            
            # Parse and validate the result
            classification = self._parse_and_validate(llm_result, user_query)
            
            # Enhance with rule-based improvements
            enhanced_classification = self._enhance_classification(classification, user_query)
            
            return enhanced_classification
            
        except Exception as e:
            print(f"Error in intent classification: {e}")
            # Return fallback classification
            return self._create_fallback_classification(user_query)
    
    def _get_llm_classification(self, user_query: str) -> str:
        """Get classification from Gemini LLM"""
        
        prompt = self._build_classification_prompt(user_query)
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"LLM classification error: {e}")
            raise
    
    def _build_classification_prompt(self, user_query: str) -> str:
        """Build the classification prompt for Gemini"""
        
        prompt = f"""You are an expert intent classification agent for HL Assurance, an insurance company. Your task is to analyze a user's query and classify it according to a predefined JSON schema. Your output MUST be a valid JSON object and nothing else.

First, understand the possible intents:
- `PRODUCT_INQUIRY`: The user is asking about the features, benefits, terms, or coverage of one or more specific insurance products.
- `COMPARISON_INQUIRY`: The user explicitly wants to compare two or more products or features.
- `PURCHASE_INQUIRY`: The user expresses a clear intent to buy, get a quote, or start an application process.
- `GENERAL_INQUIRY`: The user asks a high-level question about the company, claim procedures in general, or contact information, not specific to one product's benefits.
- `CHITCHAT`: The user is making a greeting, expressing thanks, or engaging in non-inquisitive conversation.

The products you know about are: {self.products}.

Your response MUST be a JSON object with the following structure:
{{
  "primary_intent": "...",
  "product_focus": ["...", "..."],
  "entities": ["...", "..."],
  "is_purchase_intent": true/false,
  "original_query": "..."
}}

Here are some examples:

---
User Query: "What is the windscreen excess for Car Protect360?"
{{
  "primary_intent": "PRODUCT_INQUIRY",
  "product_focus": ["Car"],
  "entities": ["windscreen excess"],
  "is_purchase_intent": false,
  "original_query": "What is the windscreen excess for Car Protect360?"
}}
---
User Query: "I want to get a quote for my helper."
{{
  "primary_intent": "PURCHASE_INQUIRY",
  "product_focus": ["Maid"],
  "entities": ["quote", "helper"],
  "is_purchase_intent": true,
  "original_query": "I want to get a quote for my helper."
}}
---
User Query: "How does the personal liability cover in the Home insurance compare to the one in the Maid insurance?"
{{
  "primary_intent": "COMPARISON_INQUIRY",
  "product_focus": ["Home", "Maid"],
  "entities": ["personal liability", "cover"],
  "is_purchase_intent": false,
  "original_query": "How does the personal liability cover in the Home insurance compare to the one in the Maid insurance?"
}}
---
User Query: "How do I make a claim?"
{{
  "primary_intent": "GENERAL_INQUIRY",
  "product_focus": [],
  "entities": ["claim"],
  "is_purchase_intent": false,
  "original_query": "How do I make a claim?"
}}
---
User Query: "Tell me about your travel and car policies"
{{
  "primary_intent": "PRODUCT_INQUIRY",
  "product_focus": ["Travel", "Car"],
  "entities": ["policies"],
  "is_purchase_intent": false,
  "original_query": "Tell me about your travel and car policies"
}}
---
User Query: "Thank you"
{{
  "primary_intent": "CHITCHAT",
  "product_focus": [],
  "entities": [],
  "is_purchase_intent": false,
  "original_query": "Thank you"
}}
---
User Query: "What's the difference between Family and Hospital medical coverage?"
{{
  "primary_intent": "COMPARISON_INQUIRY",
  "product_focus": ["Family", "Hospital"],
  "entities": ["medical coverage"],
  "is_purchase_intent": false,
  "original_query": "What's the difference between Family and Hospital medical coverage?"
}}
---
User Query: "I need insurance for my domestic worker"
{{
  "primary_intent": "PURCHASE_INQUIRY",
  "product_focus": ["Maid"],
  "entities": ["insurance", "domestic worker"],
  "is_purchase_intent": true,
  "original_query": "I need insurance for my domestic worker"
}}
---
User Query: "What are your office hours?"
{{
  "primary_intent": "GENERAL_INQUIRY",
  "product_focus": [],
  "entities": ["office hours"],
  "is_purchase_intent": false,
  "original_query": "What are your office hours?"
}}
---

Now, analyze the following user query. Remember to only output the JSON object.

User Query: "{user_query}"
"""
        return prompt
    
    def _parse_and_validate(self, llm_response: str, original_query: str) -> IntentClassification:
        """Parse LLM response and validate the structure"""
        
        try:
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                json_str = llm_response
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate required fields
            required_fields = ["primary_intent", "product_focus", "entities", "is_purchase_intent", "original_query"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate primary_intent
            try:
                primary_intent = PrimaryIntent(data["primary_intent"])
            except ValueError:
                print(f"Invalid primary_intent: {data['primary_intent']}, defaulting to GENERAL_INQUIRY")
                primary_intent = PrimaryIntent.GENERAL_INQUIRY
            
            # Validate and normalize product_focus
            product_focus = self._normalize_products(data["product_focus"])
            
            # Validate entities (ensure it's a list)
            entities = data["entities"] if isinstance(data["entities"], list) else []
            
            # Validate is_purchase_intent
            is_purchase_intent = bool(data["is_purchase_intent"])
            
            return IntentClassification(
                primary_intent=primary_intent,
                product_focus=product_focus,
                entities=entities,
                is_purchase_intent=is_purchase_intent,
                original_query=original_query
            )
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            print(f"LLM Response: {llm_response}")
            raise
    
    def _normalize_products(self, products: List[str]) -> List[str]:
        """Normalize product names to standard format"""
        normalized = []
        for product in products:
            if isinstance(product, str):
                # Check if it's already a valid product
                if product in self.products:
                    normalized.append(product)
                else:
                    # Try to map from alternative names
                    mapped = PRODUCT_MAPPING.get(product.lower())
                    if mapped and mapped in self.products:
                        normalized.append(mapped)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(normalized))
    
    def _enhance_classification(self, classification: IntentClassification, user_query: str) -> IntentClassification:
        """Enhance classification with rule-based improvements"""
        
        # Enhanced entity extraction
        enhanced_entities = self._extract_additional_entities(user_query, classification.entities)
        
        # Enhanced product detection
        enhanced_products = self._detect_additional_products(user_query, classification.product_focus)
        
        # Enhanced purchase intent detection
        enhanced_purchase_intent = self._detect_purchase_intent(user_query, classification.is_purchase_intent)
        
        return IntentClassification(
            primary_intent=classification.primary_intent,
            product_focus=enhanced_products,
            entities=enhanced_entities,
            is_purchase_intent=enhanced_purchase_intent,
            original_query=classification.original_query
        )
    
    def _extract_additional_entities(self, query: str, existing_entities: List[str]) -> List[str]:
        """Extract additional entities using rule-based approach"""
        
        query_lower = query.lower()
        entities = set(existing_entities)  # Use set to avoid duplicates
        
        # Check for common entities
        for entity in COMMON_ENTITIES:
            if entity in query_lower:
                entities.add(entity)
        
        # Extract specific patterns
        # Numbers with currency
        currency_pattern = r'\$[\d,]+|\d+\s*dollars?'
        currency_matches = re.findall(currency_pattern, query_lower)
        entities.update(currency_matches)
        
        # Age patterns
        age_pattern = r'\d+\s*years?\s*old|\d+\s*yo'
        age_matches = re.findall(age_pattern, query_lower)
        entities.update(age_matches)
        
        return list(entities)
    
    def _detect_additional_products(self, query: str, existing_products: List[str]) -> List[str]:
        """Detect additional products using rule-based approach"""
        
        query_lower = query.lower()
        products = set(existing_products)
        
        # Check for product mentions in the mapping
        for alias, product in PRODUCT_MAPPING.items():
            if alias in query_lower and product in self.products:
                products.add(product)
        
        return list(products)
    
    def _detect_purchase_intent(self, query: str, existing_intent: bool) -> bool:
        """Detect purchase intent using rule-based approach"""
        
        if existing_intent:
            return True
        
        query_lower = query.lower()
        
        # Purchase keywords
        purchase_keywords = [
            "buy", "purchase", "get", "need", "want", "quote", "apply",
            "sign up", "enroll", "subscribe", "interested in buying",
            "how much", "cost", "price", "premium", "looking for"
        ]
        
        return any(keyword in query_lower for keyword in purchase_keywords)
    
    def _create_fallback_classification(self, user_query: str) -> IntentClassification:
        """Create a fallback classification when LLM fails"""
        
        return IntentClassification(
            primary_intent=PrimaryIntent.GENERAL_INQUIRY,
            product_focus=[],
            entities=[],
            is_purchase_intent=False,
            original_query=user_query
        )
