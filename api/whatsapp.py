"""
WhatsApp Business API Integration for HLAS Insurance Agent System

Handles WhatsApp webhook verification and message processing.
"""

import json
import os
import requests
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import PlainTextResponse

from .services import InsuranceAgentService


class WhatsAppWebhook:
    """
    WhatsApp Business API webhook handler for the HLAS Insurance Agent System.
    
    Integrates the insurance agent pipeline with WhatsApp messaging.
    """
    
    def __init__(self, agent_service: InsuranceAgentService):
        self.agent_service = agent_service
        
        # WhatsApp configuration from environment variables
        self.verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "Noteasy2guess18+")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
        
        # WhatsApp API base URL
        self.api_base_url = "https://graph.facebook.com/v18.0"
        
        print(f"🔧 WhatsApp Webhook initialized")
        print(f"   Verify Token: {'✅ Set' if self.verify_token else '❌ Missing'}")
        print(f"   Access Token: {'✅ Set' if self.access_token else '❌ Missing'}")
        print(f"   Phone Number ID: {'✅ Set' if self.phone_number_id else '❌ Missing'}")
    
    async def verify_webhook(self, request: Request) -> PlainTextResponse:
        """
        Handle WhatsApp webhook verification (GET request).
        
        Meta sends a GET request with verification parameters.
        We need to respond with the challenge token if verification succeeds.
        """
        try:
            # Get query parameters
            mode = request.query_params.get('hub.mode')
            token = request.query_params.get('hub.verify_token')
            challenge = request.query_params.get('hub.challenge')
            
            print(f"🔍 Webhook verification attempt:")
            print(f"   Mode: {mode}")
            print(f"   Token: {token}")
            print(f"   Challenge: {challenge}")
            
            # Verify the mode and token
            if mode == 'subscribe' and token == self.verify_token:
                print("✅ Webhook verification successful!")
                return PlainTextResponse(content=challenge, status_code=200)
            else:
                print("❌ Webhook verification failed - token mismatch")
                print(f"   Expected: {self.verify_token}")
                print(f"   Received: {token}")
                return PlainTextResponse(content="Verification token mismatch", status_code=403)
                
        except Exception as e:
            print(f"❌ Error during webhook verification: {e}")
            return PlainTextResponse(content=f"Verification error: {str(e)}", status_code=500)
    
    async def handle_webhook(self, request: Request) -> Dict[str, str]:
        """
        Handle incoming WhatsApp messages (POST request).
        
        Processes messages through the insurance agent pipeline and sends responses.
        """
        try:
            # Parse the webhook payload
            body = await request.json()
            print(f"📨 Received WhatsApp webhook: {json.dumps(body, indent=2)}")
            
            # Process each entry in the webhook
            for entry in body.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'messages':
                        await self._process_message_change(change.get('value', {}))
            
            return {"status": "ok"}
            
        except Exception as e:
            print(f"❌ Error processing WhatsApp webhook: {e}")
            raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")
    
    async def _process_message_change(self, value: Dict[str, Any]):
        """Process a message change from WhatsApp webhook."""
        try:
            # Extract messages
            messages = value.get('messages', [])
            
            for message in messages:
                await self._process_single_message(message, value)
                
        except Exception as e:
            print(f"❌ Error processing message change: {e}")
    
    async def _process_single_message(self, message: Dict[str, Any], value: Dict[str, Any]):
        """Process a single WhatsApp message."""
        try:
            # Extract message details
            message_id = message.get('id')
            from_number = message.get('from')
            message_type = message.get('type')
            timestamp = message.get('timestamp')
            
            print(f"📱 Processing message:")
            print(f"   ID: {message_id}")
            print(f"   From: {from_number}")
            print(f"   Type: {message_type}")
            print(f"   Time: {timestamp}")
            
            # Only process text messages
            if message_type == 'text':
                text_content = message.get('text', {}).get('body', '')
                print(f"   Content: {text_content}")
                
                if text_content.strip():
                    # Process through insurance agent pipeline
                    response = await self._process_insurance_query(text_content)
                    
                    # Send response back to WhatsApp
                    await self._send_whatsapp_message(from_number, response)
                else:
                    print("⚠️  Empty message content, skipping")
            else:
                print(f"⚠️  Unsupported message type: {message_type}")
                # Send a helpful message for unsupported types
                await self._send_whatsapp_message(
                    from_number, 
                    "I can only process text messages. Please send your insurance question as text."
                )
                
        except Exception as e:
            print(f"❌ Error processing single message: {e}")
    
    async def _process_insurance_query(self, query: str) -> str:
        """Process a user query through the insurance agent pipeline."""
        try:
            print(f"🤖 Processing insurance query: {query}")
            
            # Process through the agent pipeline
            result = await self.agent_service.process_query(
                query=query,
                max_results=3,  # Limit for WhatsApp (shorter responses)
                include_citations=True,
                include_confidence=False  # Skip confidence for cleaner WhatsApp messages
            )
            
            # Format response for WhatsApp
            response = self._format_whatsapp_response(result)
            print(f"✅ Generated response: {response[:100]}...")
            
            return response
            
        except Exception as e:
            print(f"❌ Error processing insurance query: {e}")
            return "I apologize, but I encountered an error processing your question. Please try again or contact our customer service team."
    
    def _format_whatsapp_response(self, result: Dict[str, Any]) -> str:
        """Format the agent response for WhatsApp messaging."""
        try:
            # Get the main answer
            answer = result.get('answer', 'I apologize, but I could not find an answer to your question.')
            
            # Get citations if available
            citations = result.get('citations', [])
            
            # Format for WhatsApp (keep it concise)
            response_parts = [answer]
            
            # Add sources if available (but keep it short for WhatsApp)
            if citations and len(citations) > 0:
                response_parts.append("\n📚 *Sources:*")
                for i, citation in enumerate(citations[:2], 1):  # Limit to 2 sources for WhatsApp
                    source_info = f"{citation.get('product_name', 'Unknown')} {citation.get('document_type', 'Document')}"
                    response_parts.append(f"[{i}] {source_info}")
            
            # Add helpful footer
            response_parts.append("\n💡 *Need more help?* Ask me about specific insurance products like Car, Travel, Family, Hospital, Maid, Home, or Early insurance.")
            
            return "\n".join(response_parts)
            
        except Exception as e:
            print(f"❌ Error formatting WhatsApp response: {e}")
            return result.get('answer', 'I apologize, but I encountered an error formatting the response.')
    
    async def _send_whatsapp_message(self, to_number: str, message: str):
        """Send a message back to WhatsApp user."""
        try:
            if not self.access_token or not self.phone_number_id:
                print("❌ WhatsApp credentials not configured - cannot send message")
                return
            
            # Prepare the message payload
            url = f"{self.api_base_url}/{self.phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            print(f"📤 Sending WhatsApp message to {to_number}")
            print(f"   Message length: {len(message)} characters")
            
            # Send the message
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                print("✅ WhatsApp message sent successfully")
            else:
                print(f"❌ Failed to send WhatsApp message: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error sending WhatsApp message: {e}")
    
    def get_webhook_info(self) -> Dict[str, Any]:
        """Get webhook configuration information."""
        return {
            "verify_token_configured": bool(self.verify_token),
            "access_token_configured": bool(self.access_token),
            "phone_number_id_configured": bool(self.phone_number_id),
            "webhook_endpoints": {
                "verification": "/webhook (GET)",
                "messages": "/webhook (POST)"
            },
            "supported_message_types": ["text"],
            "agent_integration": "HLAS Insurance Agent Pipeline"
        }
