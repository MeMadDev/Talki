from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging
import json
from .models import MessageLog
from django.conf import settings
from firms.models import Firm, ChatUser
from firms.utils import get_firm_by_phone, get_next_message, get_or_create_chat_user
import requests

logger = logging.getLogger(__name__)

# Create your views here.

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception as e:
            logger.error(f'Error decoding JSON: {e}')
            data = {}
        logger.info(f'Received WhatsApp webhook data: {data}')
        # Parse WhatsApp Business API format
        try:
            entry = data.get('entry', [])[0]
            waba_id = entry.get('id', '')
            change = entry.get('changes', [])[0]
            value = change.get('value', {})
            metadata = value.get('metadata', {})
            firm_phone_number = metadata.get('display_phone_number', '')
            contacts = value.get('contacts', [])
            messages = value.get('messages', [])
            if contacts and messages:
                wa_id = contacts[0].get('wa_id', '')
                profile_name = contacts[0].get('profile', {}).get('name', '')
                msg = messages[0]
                msg_body = msg.get('text', {}).get('body', '')
                msg_type = msg.get('type', '')
                msg_id = msg.get('id', '')
                timestamp = msg.get('timestamp', '')
                
                # Log the incoming message
                MessageLog.objects.create(
                    direction='IN',
                    phone_number=wa_id,
                    message=f"{msg_body}",
                    status='received',
                    whatsapp_business_account_id=waba_id,
                    firm_phone_number=firm_phone_number,
                    user_name=profile_name,
                    message_id=msg_id,
                )
                logger.info(f"Logged WhatsApp message from {wa_id}: {msg_body}")
                
                # Process the message and get response
                firm = get_firm_by_phone(firm_phone_number)
                if firm:
                    chat_user = get_or_create_chat_user(firm, wa_id, profile_name)
                    next_step, response_message = get_next_message(
                        firm,
                        chat_user.current_step,
                        msg_body
                    )
                    
                    if next_step:
                        # Update user's current step
                        chat_user.current_step = next_step
                        chat_user.last_message_received = msg_body
                        chat_user.save()
                        
                        # Send response message
                        send_whatsapp_message(wa_id, response_message)
                        
                        # Log the outgoing message
                        MessageLog.objects.create(
                            direction='OUT',
                            phone_number=wa_id,
                            message=response_message,
                            status='sent',
                            whatsapp_business_account_id=waba_id,
                            firm_phone_number=firm_phone_number,
                            user_name=profile_name,
                        )
            else:
                logger.warning('No contacts or messages found in webhook payload.')
        except Exception as e:
            logger.error(f'Error parsing WhatsApp webhook format: {e}')
        return JsonResponse({'status': 'received'}, status=200)
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def send_message(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            recipient = data.get('recipient')
            message = data.get('message')
            if not recipient or not message:
                return JsonResponse({'error': 'recipient and message are required'}, status=400)
            
            # Send message via WhatsApp API
            success = send_whatsapp_message(recipient, message)
            
            if success:
                # Log the message
                MessageLog.objects.create(
                    direction='OUT',
                    phone_number=recipient,
                    message=message,
                    status='sent',
                )
                return JsonResponse({'status': 'message sent'}, status=200)
            else:
                return JsonResponse({'error': 'Failed to send message'}, status=500)
                
        except Exception as e:
            logger.error(f'Error in send_message: {e}')
            return JsonResponse({'error': 'Invalid request'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)

def send_whatsapp_message(to_number: str, message: str) -> bool:
    """
    Send a WhatsApp message using the configured API.
    
    Args:
        to_number (str): The recipient's phone number
        message (str): The message to send
        
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        response = requests.post(
            settings.WHATSAPP_API_URL,
            json={
                'to': to_number,
                'message': message
            },
            headers={
                'Authorization': f'Bearer {settings.WHATSAPP_API_TOKEN}'
            }
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f'Error sending WhatsApp message: {e}')
        return False
