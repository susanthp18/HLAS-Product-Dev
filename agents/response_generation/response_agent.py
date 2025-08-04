"""
Response Generation Agent

This agent synthesizes retrieved context chunks into high-quality, human-readable answers
with proper citations. It follows strict principles of being grounded in truth, clear,
traceable, and honest about limitations.
"""

import google.generativeai as genai
from typing import List, Dict, Any, Optional
from config import Config
from .models import ResponseRequest, ResponseResult, Citation, CitationStyle, ConfidenceConfig
from agents.retrieval.models import ChunkResult


class ResponseGenerationAgent:
    """
    Agent responsible for generating human-readable responses from retrieved context chunks.
    
    Core Principles:
    1. Grounded in Truth: Only use provided context, never external knowledge
    2. Clarity and Simplicity: Clear, direct language for customers
    3. Traceability and Trust: Every fact must be cited
    4. Honesty about Limitations: Admit when context is insufficient
    """
    
    def __init__(self, gemini_api_key: str = None):
        """Initialize the Response Generation Agent"""
        print("🔧 ResponseGenerationAgent: Initializing...")

        self.gemini_api_key = gemini_api_key or Config.GEMINI_API_KEY

        try:
            genai.configure(api_key=self.gemini_api_key)
            print("✅ ResponseGenerationAgent: Gemini API configured")
        except Exception as e:
            print(f"❌ ResponseGenerationAgent: Failed to configure Gemini API: {str(e)}")
            raise

        # Response generation configuration
        self.generation_config = {
            "temperature": 0.1,  # Low temperature for factual responses
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }

        # Initialize the model
        try:
            self.model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                generation_config=self.generation_config
            )
            print("✅ ResponseGenerationAgent: Gemini model initialized")
        except Exception as e:
            print(f"❌ ResponseGenerationAgent: Failed to initialize Gemini model: {str(e)}")
            raise
    
    def generate_response(self, request: ResponseRequest) -> ResponseResult:
        """
        Generate a response based on the provided context chunks.
        
        Args:
            request: ResponseRequest containing query and context chunks
            
        Returns:
            ResponseResult with generated answer and citations
        """

        # Step 1: Validate input
        if not request or not isinstance(request.original_query, str) or not request.original_query.strip():
            return ResponseResult(
                answer="I need a valid question to provide an answer. Please ask me about insurance products.",
                citations=[],
                confidence_score=0.0,
                context_used=0,
                context_available=0,
                has_sufficient_context=False,
                reasoning="Invalid or empty query provided."
            )

        # Step 2: Validate and prepare context
        if not request.has_context:
            return self._generate_no_context_response(request)
        
        # Step 2: Create citations from context chunks
        citations = self._create_citations(request.context_chunks)
        
        # Step 3: Prepare context for the LLM
        context_text = self._prepare_context_text(request.context_chunks, citations, request.citation_style)
        
        # Step 4: Generate the response using LLM
        try:
            answer = self._generate_answer(request.original_query, context_text, request.citation_style)
            if not answer or not isinstance(answer, str):
                raise ValueError("LLM returned invalid response")
        except Exception as e:
            return ResponseResult(
                answer=f"I apologize, but I encountered an error while processing your question. Please try again or contact customer service. (Error: {str(e)})",
                citations=citations,
                confidence_score=0.0,
                context_used=0,
                context_available=len(request.context_chunks),
                has_sufficient_context=False,
                reasoning=f"Error during response generation: {str(e)}"
            )
        
        # Step 5: Calculate confidence score
        config = request.confidence_config or ConfidenceConfig()
        confidence_score = self._calculate_confidence_score(request.context_chunks, answer, config)
        
        # Step 6: Determine if context is sufficient
        has_sufficient_context = self._assess_context_sufficiency(request.original_query, request.context_chunks, answer, config)
        
        # Step 7: Generate reasoning
        reasoning = self._generate_reasoning(request, answer, confidence_score, has_sufficient_context)
        
        return ResponseResult(
            answer=answer,
            citations=citations,
            confidence_score=confidence_score,
            context_used=len([c for c in citations if self._citation_used_in_answer(c, answer)]),
            context_available=len(request.context_chunks),
            has_sufficient_context=has_sufficient_context,
            reasoning=reasoning
        )
    
    def _generate_no_context_response(self, request: ResponseRequest) -> ResponseResult:
        """Generate response when no context is available"""
        answer = (
            "I don't have enough information in our insurance documents to answer your question. "
            "Please contact our customer service team for assistance, or try rephrasing your question "
            "to be more specific about the insurance product you're interested in."
        )
        
        return ResponseResult(
            answer=answer,
            citations=[],
            confidence_score=0.0,
            context_used=0,
            context_available=0,
            has_sufficient_context=False,
            reasoning="No relevant context chunks were provided by the retrieval system."
        )
    
    def _create_citations(self, context_chunks: List[ChunkResult]) -> List[Citation]:
        """Create citation objects from context chunks"""
        citations = []
        
        for i, chunk in enumerate(context_chunks):
            citation = Citation(
                id=f"cite_{i+1}",
                product_name=chunk.product_name,
                document_type=chunk.document_type,
                source_file=chunk.source_file,
                section_hierarchy=chunk.section_hierarchy or [],
                relevance_score=chunk.relevance_score
            )
            citations.append(citation)
        
        return citations
    
    def _prepare_context_text(self, context_chunks: List[ChunkResult], citations: List[Citation], citation_style: CitationStyle) -> str:
        """Prepare context text with citations for the LLM"""
        context_parts = []
        
        for i, (chunk, citation) in enumerate(zip(context_chunks, citations), 1):
            citation_marker = citation.format_citation(citation_style, i)
            
            # Add source information
            source_info = f"Source {i}: {chunk.product_name} {chunk.document_type}"
            if chunk.section_hierarchy:
                source_info += f" - {' > '.join(chunk.section_hierarchy)}"
            
            context_parts.append(f"{source_info}")
            context_parts.append(f"Content: {chunk.content}")
            context_parts.append(f"Citation: {citation_marker}")
            context_parts.append("---")
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, query: str, context_text: str, citation_style: CitationStyle) -> str:
        """Generate answer using the LLM"""
        
        citation_instruction = self._get_citation_instruction(citation_style)
        
        prompt = f"""You are an insurance customer service assistant. Your job is to answer customer questions based ONLY on the provided insurance document context. Follow these strict rules:

1. ONLY use information from the provided context - never use external knowledge
2. If the context doesn't contain enough information to answer the question, say so clearly
3. Use clear, simple language that customers can understand
4. Cite every piece of information using the citation format: {citation_instruction}
5. Be direct and helpful
6. If multiple products are mentioned, clearly distinguish between them

Customer Question: {query}

Context from Insurance Documents:
{context_text}

Answer the customer's question based ONLY on the provided context. Include proper citations for every fact you mention."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"I apologize, but I encountered an error while processing your question. Please try again or contact customer service. (Error: {str(e)})"
    
    def _get_citation_instruction(self, citation_style: CitationStyle) -> str:
        """Get citation format instruction for the LLM"""
        if citation_style == CitationStyle.NUMBERED:
            return "[1], [2], [3] etc."
        elif citation_style == CitationStyle.INLINE:
            return "(Source: Product Document Type)"
        elif citation_style == CitationStyle.FOOTNOTE:
            return "¹, ², ³ etc."
        return "[1], [2], [3] etc."
    
    def _calculate_confidence_score(self, context_chunks: List[ChunkResult], answer: str, config: ConfidenceConfig) -> float:
        """Calculate confidence score based on context quality and answer completeness"""
        if not context_chunks:
            return 0.0

        # Validate and calculate base confidence from relevance scores
        valid_scores = []
        for chunk in context_chunks:
            if hasattr(chunk, 'relevance_score') and chunk.relevance_score is not None:
                try:
                    score = float(chunk.relevance_score)
                    if 0.0 <= score <= 1.0:  # Validate score is in expected range
                        valid_scores.append(score)
                except (ValueError, TypeError):
                    continue  # Skip invalid scores

        if not valid_scores:
            return 0.0

        avg_relevance = sum(valid_scores) / len(valid_scores)
        confidence = avg_relevance

        # Apply quality adjustments with conflict resolution
        confidence_adjustments = self._analyze_answer_quality(answer, config)

        # Apply adjustments in order of priority (uncertainty overrides specificity)
        if confidence_adjustments['has_uncertainty']:
            confidence *= confidence_adjustments['uncertainty_penalty']
        elif confidence_adjustments['has_specificity']:
            confidence *= confidence_adjustments['specificity_boost']

        # Apply length adjustment
        confidence *= confidence_adjustments['length_factor']

        # Ensure confidence stays within bounds with minimum meaningful threshold
        return max(config.min_confidence_threshold, min(1.0, confidence))

    def _analyze_answer_quality(self, answer: str, config: ConfidenceConfig) -> dict:
        """Comprehensive analysis of answer quality indicators"""
        if not answer or not isinstance(answer, str):
            return {
                'has_uncertainty': True,
                'uncertainty_penalty': config.strong_uncertainty_penalty,
                'has_specificity': False,
                'specificity_boost': 1.0,
                'length_factor': config.very_short_penalty
            }

        answer_lower = answer.lower()
        word_count = len(answer.split())

        # Enhanced uncertainty detection with context awareness
        uncertainty_indicators = [
            # Strong uncertainty
            "don't have enough information", "not enough information", "insufficient information",
            "cannot determine", "unclear", "please contact", "i don't know", "unsure",
            "unable to find", "no information available", "not specified", "not mentioned",

            # Moderate uncertainty (context-dependent)
            "may depend", "might vary", "could be", "possibly", "perhaps", "seems to",
            "appears to", "likely", "probably", "i think", "it depends", "varies",

            # Weak uncertainty (instructional context)
            "you may", "may apply", "may choose", "might want", "could consider"
        ]

        # Specificity indicators with context validation
        specificity_patterns = [
            # Monetary values (with context)
            (r'\$\d+', 'monetary'),
            (r'\d+\s*dollars?', 'monetary'),
            (r'\d+\s*cents?', 'monetary'),

            # Percentages (with context)
            (r'\d+\s*%', 'percentage'),
            (r'\d+\s*percent', 'percentage'),

            # Time periods (with context)
            (r'\d+\s*days?', 'time'),
            (r'\d+\s*months?', 'time'),
            (r'\d+\s*years?', 'time'),
            (r'\d+\s*weeks?', 'time'),

            # Age ranges
            (r'\d+\s*years?\s*old', 'age'),
            (r'age\s*\d+', 'age'),
            (r'between\s*\d+\s*and\s*\d+', 'range')
        ]

        # Analyze uncertainty with severity levels
        uncertainty_score = 0.0
        strong_uncertainty = any(phrase in answer_lower for phrase in uncertainty_indicators[:8])
        moderate_uncertainty = any(phrase in answer_lower for phrase in uncertainty_indicators[8:16])
        weak_uncertainty = any(phrase in answer_lower for phrase in uncertainty_indicators[16:])

        if strong_uncertainty:
            uncertainty_score = config.strong_uncertainty_penalty
        elif moderate_uncertainty and not self._is_instructional_context(answer_lower):
            uncertainty_score = config.moderate_uncertainty_penalty
        elif weak_uncertainty and not self._is_instructional_context(answer_lower):
            uncertainty_score = config.weak_uncertainty_penalty
        else:
            uncertainty_score = 1.0  # No penalty

        # Analyze specificity with context validation
        import re
        specificity_count = 0
        for pattern, category in specificity_patterns:
            matches = re.findall(pattern, answer_lower)
            if matches and self._is_meaningful_specificity(answer_lower, matches, category):
                specificity_count += len(matches)

        # Calculate length factor with adaptive thresholds
        if word_count < 5:
            length_factor = config.very_short_penalty
        elif word_count < 10:
            length_factor = config.short_penalty
        elif word_count < 15:
            length_factor = config.adequate_penalty
        else:
            length_factor = 1.0  # Good length

        return {
            'has_uncertainty': uncertainty_score < 1.0,
            'uncertainty_penalty': uncertainty_score,
            'has_specificity': specificity_count > 0,
            'specificity_boost': min(config.max_specificity_boost, 1.0 + (specificity_count * config.specificity_boost_per_item)),
            'length_factor': length_factor
        }

    def _is_instructional_context(self, answer_lower: str) -> bool:
        """Check if uncertainty phrases are used in instructional context"""
        instructional_indicators = [
            "you may apply", "you may choose", "you may contact", "may be eligible",
            "you might want", "you could consider", "may qualify", "may submit"
        ]
        return any(indicator in answer_lower for indicator in instructional_indicators)

    def _is_meaningful_specificity(self, answer_lower: str, matches: list, category: str) -> bool:
        """Validate that specificity indicators are meaningful, not just mentioned"""
        if category == 'monetary':
            # Check if monetary value is in negative context
            negative_contexts = ["don't have", "no information", "not specified", "unclear"]
            return not any(context in answer_lower for context in negative_contexts)
        elif category == 'time':
            # Check if time period is definitive, not hypothetical
            hypothetical_contexts = ["may take", "might be", "could be", "possibly"]
            return not any(context in answer_lower for context in hypothetical_contexts)
        return True

    def _assess_context_sufficiency(self, query: str, context_chunks: List[ChunkResult], answer: str, config: ConfidenceConfig) -> bool:
        """Assess if the provided context was sufficient to answer the query"""
        if not context_chunks or not answer:
            return False

        # Validate relevance scores and calculate average
        valid_scores = []
        for chunk in context_chunks:
            if hasattr(chunk, 'relevance_score') and chunk.relevance_score is not None:
                try:
                    score = float(chunk.relevance_score)
                    if 0.0 <= score <= 1.0:
                        valid_scores.append(score)
                except (ValueError, TypeError):
                    continue

        if not valid_scores:
            return False

        avg_relevance = sum(valid_scores) / len(valid_scores)

        # Enhanced uncertainty detection
        strong_uncertainty_indicators = [
            "don't have enough information", "not enough information", "insufficient information",
            "cannot determine", "unclear", "please contact", "i don't know", "unsure",
            "unable to find", "no information available", "not specified in", "not mentioned"
        ]

        answer_lower = answer.lower() if isinstance(answer, str) else ""
        has_strong_uncertainty = any(indicator in answer_lower for indicator in strong_uncertainty_indicators)

        # Adaptive relevance threshold based on query complexity
        query_words = len(query.split()) if isinstance(query, str) else 0
        if query_words <= 3:
            relevance_threshold = config.min_relevance_threshold
        elif query_words <= 6:
            relevance_threshold = config.standard_relevance_threshold
        else:
            relevance_threshold = config.complex_query_relevance_threshold

        has_good_relevance = avg_relevance >= relevance_threshold

        # Adaptive substantiveness check based on query type
        word_count = len(answer.split()) if isinstance(answer, str) else 0

        # Different thresholds for different query types
        if any(word in query.lower() for word in ['what', 'how much', 'when', 'where']) if isinstance(query, str) else False:
            min_words = config.factual_query_min_words
        elif any(word in query.lower() for word in ['compare', 'difference', 'versus']) if isinstance(query, str) else False:
            min_words = config.comparison_query_min_words
        else:
            min_words = config.default_min_words

        is_substantive = word_count >= min_words

        # Additional check: ensure answer actually addresses the query
        has_relevant_content = self._answer_addresses_query(query, answer, config)

        return (not has_strong_uncertainty and
                has_good_relevance and
                is_substantive and
                has_relevant_content)

    def _answer_addresses_query(self, query: str, answer: str, config: ConfidenceConfig) -> bool:
        """Check if the answer actually addresses the query"""
        if not isinstance(query, str) or not isinstance(answer, str):
            return False

        query_lower = query.lower()
        answer_lower = answer.lower()

        # Extract key terms from query (excluding common words)
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'what', 'how', 'when', 'where', 'why', 'which', 'who'}
        query_terms = [word for word in query_lower.split() if word not in common_words and len(word) > 2]

        if not query_terms:
            return True  # If no meaningful terms, assume it's addressed

        # Check if sufficient percentage of query terms appear in answer
        matching_terms = sum(1 for term in query_terms if term in answer_lower)
        relevance_ratio = matching_terms / len(query_terms)

        return relevance_ratio >= config.query_term_match_threshold
    
    def _citation_used_in_answer(self, citation: Citation, answer: str) -> bool:
        """Check if a citation is actually used in the answer"""
        if not isinstance(answer, str) or not citation:
            return False

        answer_lower = answer.lower()
        citation_markers = []

        # Safe citation ID parsing
        try:
            if hasattr(citation, 'id') and citation.id:
                # Handle different ID formats safely
                if '_' in citation.id:
                    id_parts = citation.id.split('_')
                    if len(id_parts) > 1 and id_parts[1].isdigit():
                        citation_markers.append(f"[{id_parts[1]}]")
                elif citation.id.isdigit():
                    citation_markers.append(f"[{citation.id}]")
        except (AttributeError, IndexError, ValueError):
            pass  # Skip if ID parsing fails

        # Product name matching with word boundaries to avoid false positives
        if hasattr(citation, 'product_name') and citation.product_name:
            product_name = citation.product_name.lower()
            # Use word boundaries to avoid partial matches like "car" in "scar"
            import re
            if re.search(r'\b' + re.escape(product_name) + r'\b', answer_lower):
                citation_markers.append(product_name)

        # Document type matching with word boundaries
        if hasattr(citation, 'document_type') and citation.document_type:
            # Handle both string and enum types
            if hasattr(citation.document_type, 'value'):
                doc_type = citation.document_type.value.lower()
            else:
                doc_type = str(citation.document_type).lower()
            import re
            if re.search(r'\b' + re.escape(doc_type) + r'\b', answer_lower):
                citation_markers.append(doc_type)

        # Check for meaningful usage (not just mention in negative context)
        if citation_markers:
            for marker in citation_markers:
                if marker in answer_lower:
                    # Ensure it's not in a negative context
                    negative_contexts = [
                        f"no information about {marker}",
                        f"don't have {marker}",
                        f"not mentioned in {marker}",
                        f"unclear from {marker}"
                    ]
                    if not any(neg_context in answer_lower for neg_context in negative_contexts):
                        return True

        return False
    
    def _generate_reasoning(self, request: ResponseRequest, answer: str, confidence_score: float, has_sufficient_context: bool) -> str:
        """Generate reasoning about the response quality"""
        context_summary = request.context_summary
        
        reasoning_parts = []
        reasoning_parts.append(f"Used {context_summary['total_chunks']} context chunks from {len(context_summary['products'])} product(s): {', '.join(context_summary['products'])}")
        reasoning_parts.append(f"Average relevance score: {context_summary['avg_relevance']:.2f}")
        reasoning_parts.append(f"Confidence score: {confidence_score:.2f}")
        
        if has_sufficient_context:
            reasoning_parts.append("Assessment: Sufficient context available to provide a comprehensive answer")
        else:
            reasoning_parts.append("Assessment: Limited context available, answer may be incomplete")
        
        return " | ".join(reasoning_parts)
