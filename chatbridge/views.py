from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import json
from .models import MessageLog

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
            # Here, you would call the WhatsApp Business API to send the message
            logger.info(f'Sending message to {recipient}: {message}')
            MessageLog.objects.create(
                direction='OUT',
                phone_number=recipient,
                message=message,
                status='sent (mocked)',
            )
            return JsonResponse({'status': 'message sent (mocked)'}, status=200)
        except Exception as e:
            logger.error(f'Error in send_message: {e}')
            return JsonResponse({'error': 'Invalid request'}, status=400)
    return JsonResponse({'error': 'Invalid method'}, status=405)
