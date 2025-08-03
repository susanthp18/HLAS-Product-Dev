"""
Metadata enrichment using LLMs for summaries and hypothetical questions
"""

from typing import List, Optional
import google.generativeai as genai
from .models import DocumentChunk, DocumentType
from config import Config


class MetadataEnricher:
    """Enriches chunks with AI-generated metadata"""
    
    def __init__(self, gemini_api_key: str):
        """Initialize with Gemini API"""
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(Config.GENERATION_MODEL)
    
    def enrich_chunk(self, chunk: DocumentChunk) -> DocumentChunk:
        """Enrich a single chunk with summary and hypothetical questions"""
        # Generate summary
        chunk.summary = self._generate_summary(chunk)
        
        # Generate hypothetical questions
        chunk.hypothetical_questions = self._generate_hypothetical_questions(chunk)
        
        return chunk
    
    def enrich_chunks_batch(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Enrich multiple chunks"""
        enriched_chunks = []
        for chunk in chunks:
            try:
                enriched_chunk = self.enrich_chunk(chunk)
                enriched_chunks.append(enriched_chunk)
            except Exception as e:
                print(f"Error enriching chunk {chunk.chunk_id}: {e}")
                # Return chunk without enrichment if error occurs
                enriched_chunks.append(chunk)
        
        return enriched_chunks
    
    def _generate_summary(self, chunk: DocumentChunk) -> str:
        """Generate a concise summary for the chunk"""
        # For FAQ chunks, the question itself is the perfect summary
        if chunk.document_type == DocumentType.FAQ and chunk.question:
            return chunk.question
        
        # For benefits chunks, extract the benefit name
        if chunk.document_type == DocumentType.BENEFITS_SUMMARY:
            # Try to extract benefit name from the content
            content_lower = chunk.content.lower()
            if 'benefit' in content_lower or 'coverage' in content_lower:
                # Extract the first part before "provides" or "covers"
                parts = chunk.content.split('provides', 1)
                if len(parts) == 1:
                    parts = chunk.content.split('covers', 1)
                if len(parts) > 1:
                    return parts[0].strip()
            
            # Otherwise, create a short summary
            if len(chunk.content) < 100:
                return chunk.content
        
        # For Terms chunks and long content, use LLM to generate summary
        try:
            prompt = f"""Generate a one-sentence summary of this insurance policy content. 
Focus on what specific aspect of coverage or rule this section describes.

Content: {chunk.content[:1000]}...

Summary:"""
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
            # Fallback: use first sentence or first 100 chars
            sentences = chunk.content.split('.')
            if sentences:
                return sentences[0].strip() + '.'
            return chunk.content[:100] + '...'
    
    def _generate_hypothetical_questions(self, chunk: DocumentChunk) -> List[str]:
        """Generate potential questions that this chunk answers"""
        # For FAQ chunks, we already have the actual question
        if chunk.document_type == DocumentType.FAQ and chunk.question:
            # Generate variations of the question
            return self._generate_question_variations(chunk.question, chunk.content)
        
        # For other chunks, generate questions using LLM
        try:
            prompt = self._create_question_generation_prompt(chunk)
            response = self.model.generate_content(prompt)
            
            # Parse questions from response
            questions = []
            for line in response.text.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    # Remove numbering or bullets
                    question = line.lstrip('0123456789.-) ').strip()
                    if question and '?' in question:
                        questions.append(question)
            
            return questions[:5]  # Limit to 5 questions
            
        except Exception as e:
            print(f"Error generating questions: {e}")
            return self._generate_fallback_questions(chunk)
    
    def _create_question_generation_prompt(self, chunk: DocumentChunk) -> str:
        """Create appropriate prompt based on document type"""
        if chunk.document_type == DocumentType.BENEFITS_SUMMARY:
            return f"""Generate 3-5 questions that a customer might ask about this insurance benefit.
Focus on practical questions about coverage amounts, eligibility, and claims.

Benefit details: {chunk.content}

Questions:"""
        
        elif chunk.document_type == DocumentType.TERMS:
            hierarchy = " > ".join(chunk.section_hierarchy) if chunk.section_hierarchy else "General"
            return f"""Generate 3-5 questions that a policyholder might ask about this section of insurance terms.
Focus on understanding coverage, exclusions, and procedures.

Section: {hierarchy}
Content: {chunk.content[:500]}...

Questions:"""
        
        else:
            return f"""Generate 3-5 questions that this insurance content answers.
Make them natural questions a customer would ask.

Content: {chunk.content[:500]}...

Questions:"""
    
    def _generate_question_variations(self, original_question: str, answer: str) -> List[str]:
        """Generate variations of an existing question"""
        variations = [original_question]
        
        # Simple variations
        if 'what' in original_question.lower():
            variations.append(original_question.replace('What', 'Can you explain what'))
        
        if 'how' in original_question.lower():
            variations.append(original_question.replace('How', 'Can you tell me how'))
        
        # Add a more specific question based on the answer
        if 'coverage' in answer.lower() or 'cover' in answer.lower():
            variations.append(f"What does the {self._extract_product_name(original_question)} policy cover?")
        
        return variations[:3]
    
    def _generate_fallback_questions(self, chunk: DocumentChunk) -> List[str]:
        """Generate basic questions when LLM fails"""
        questions = []
        
        if chunk.document_type == DocumentType.BENEFITS_SUMMARY:
            questions.append(f"What is the coverage amount for {chunk.product_name.value} insurance?")
            questions.append(f"How much does {chunk.product_name.value} insurance pay?")
        
        elif chunk.document_type == DocumentType.TERMS:
            if chunk.section_hierarchy:
                section = chunk.section_hierarchy[-1]
                questions.append(f"What are the terms for {section}?")
                questions.append(f"How does {section} work?")
        
        else:
            questions.append(f"What does {chunk.product_name.value} insurance cover?")
        
        return questions
    
    def _extract_product_name(self, text: str) -> str:
        """Extract product name from text"""
        products = ['Car', 'Early', 'Family', 'Home', 'Hospital', 'Maid', 'Travel']
        for product in products:
            if product.lower() in text.lower():
                return product
        return "insurance" 