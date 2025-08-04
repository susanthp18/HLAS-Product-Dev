"""
Data models for Intent Router Agent
"""

from dataclasses import dataclass
from typing import List
from enum import Enum
import json


class PrimaryIntent(Enum):
    """Primary intent classifications for user queries"""
    PRODUCT_INQUIRY = "PRODUCT_INQUIRY"
    COMPARISON_INQUIRY = "COMPARISON_INQUIRY"
    PURCHASE_INQUIRY = "PURCHASE_INQUIRY"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"
    CHITCHAT = "CHITCHAT"


@dataclass
class IntentClassification:
    """
    Structured output from intent classification
    
    This represents the "internal command" passed to the Orchestrator
    """
    primary_intent: PrimaryIntent
    product_focus: List[str]
    entities: List[str]
    is_purchase_intent: bool
    original_query: str
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            "primary_intent": self.primary_intent.value,
            "product_focus": self.product_focus,
            "entities": self.entities,
            "is_purchase_intent": self.is_purchase_intent,
            "original_query": self.original_query
        }, indent=2)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "primary_intent": self.primary_intent.value,
            "product_focus": self.product_focus,
            "entities": self.entities,
            "is_purchase_intent": self.is_purchase_intent,
            "original_query": self.original_query
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'IntentClassification':
        """Create from dictionary"""
        return cls(
            primary_intent=PrimaryIntent(data["primary_intent"]),
            product_focus=data["product_focus"],
            entities=data["entities"],
            is_purchase_intent=data["is_purchase_intent"],
            original_query=data["original_query"]
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> 'IntentClassification':
        """Create from JSON string"""
        data = json.loads(json_str)
        return cls.from_dict(data)


# Product mapping for consistent naming
PRODUCT_MAPPING = {
    # Standard product names
    "car": "Car",
    "early": "Early", 
    "family": "Family",
    "home": "Home",
    "hospital": "Hospital",
    "maid": "Maid",
    "travel": "Travel",
    
    # Alternative names and aliases
    "vehicle": "Car",
    "auto": "Car",
    "automobile": "Car",
    "motor": "Car",
    "car protect360": "Car",
    "car protect 360": "Car",
    
    "early protect360": "Early",
    "early protect 360": "Early",
    "early protect360 plus": "Early",
    "early protect 360 plus": "Early",
    
    "family protect360": "Family",
    "family protect 360": "Family",
    
    "house": "Home",
    "property": "Home",
    "home protect360": "Home",
    "home protect 360": "Home",
    
    "medical": "Hospital",
    "health": "Hospital",
    "hospital protect360": "Hospital",
    "hospital protect 360": "Hospital",
    
    "domestic helper": "Maid",
    "helper": "Maid",
    "domestic worker": "Maid",
    "foreign domestic worker": "Maid",
    "fdw": "Maid",
    "maid protect360": "Maid",
    "maid protect 360": "Maid",
    "maid protect360 pro": "Maid",
    "maid protect 360 pro": "Maid",
    
    "trip": "Travel",
    "vacation": "Travel",
    "holiday": "Travel",
    "overseas": "Travel",
    "travel protect360": "Travel",
    "travel protect 360": "Travel"
}

# Common entities for better extraction
COMMON_ENTITIES = {
    # Coverage types
    "coverage", "cover", "protection", "benefit", "benefits",
    "liability", "personal liability", "third party liability",
    "medical expenses", "medical coverage", "hospital expenses",
    "surgical expenses", "accident coverage", "accidental damage",
    
    # Car specific
    "windscreen", "windshield", "excess", "deductible", "ncd", 
    "no claim discount", "transport allowance", "towing",
    "workshop", "authorized workshop", "own damage",
    
    # Travel specific
    "covid", "covid-19", "coronavirus", "trip cancellation",
    "trip interruption", "baggage", "luggage", "delay",
    "medical evacuation", "repatriation",
    
    # Home specific
    "contents", "household contents", "renovation", "fixtures",
    "fittings", "valuables", "jewellery", "jewelry", "theft",
    "fire", "flood", "burst pipe",
    
    # Maid specific
    "replacement maid", "replacement helper", "work permit",
    "repatriation", "personal accident",
    
    # General
    "premium", "price", "cost", "quote", "claim", "claims",
    "policy", "terms", "conditions", "exclusions", "waiting period",
    "sum insured", "limit", "limits", "age limit"
}
