"""
Response Generation Agent

This module contains the Response Generation Agent that synthesizes retrieved context
chunks into high-quality, human-readable answers with proper citations.
"""

from .response_agent import ResponseGenerationAgent
from .models import ResponseRequest, ResponseResult, CitationStyle, ConfidenceConfig

__version__ = "0.1.0"
__all__ = ['ResponseGenerationAgent', 'ResponseRequest', 'ResponseResult', 'CitationStyle', 'ConfidenceConfig']
