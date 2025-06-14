from .models import Firm, ChatUser
from typing import Optional, Tuple
import re

def get_firm_by_phone(phone_number: str) -> Optional[Firm]:
    """
    Get a firm by its phone number.
    
    Args:
        phone_number (str): The phone number to search for
        
    Returns:
        Optional[Firm]: The firm if found, None otherwise
    """
    try:
        return Firm.objects.get(phone_number=phone_number, status=True)
    except Firm.DoesNotExist:
        return None

def get_next_message(firm: Firm, current_step: str, user_input: str) -> Tuple[str, str]:
    """
    Get the next message based on the current step and user input.
    
    Args:
        firm (Firm): The firm object
        current_step (str): The current step ID
        user_input (str): The user's input message
        
    Returns:
        Tuple[str, str]: A tuple containing (next_step_id, message_to_send)
    """
    flow = firm.flow
    if not flow or 'steps' not in flow:
        return None, "No flow configured for this firm."
    
    # Find the current step in the flow
    current_step_data = next(
        (step for step in flow['steps'] if step['id'] == current_step),
        None
    )
    
    if not current_step_data:
        return None, "Invalid step in conversation flow."
    
    # Handle the next step logic
    next_step = current_step_data.get('next')
    
    # If next is a string, it's a direct next step
    if isinstance(next_step, str):
        return next_step, get_message_for_step(flow, next_step)
    
    # If next is a list, it's a pattern-based routing
    if isinstance(next_step, list):
        for pattern_data in next_step:
            pattern = pattern_data.get('pattern', '')
            try:
                if re.match(pattern, user_input.strip()):
                    next_step_id = pattern_data.get('next')
                    return next_step_id, get_message_for_step(flow, next_step_id)
            except re.error:
                # If pattern is invalid, try direct string matching
                if pattern == user_input.strip():
                    next_step_id = pattern_data.get('next')
                    return next_step_id, get_message_for_step(flow, next_step_id)
    
    return None, "No valid next step found in the flow."

def get_message_for_step(flow: dict, step_id: str) -> str:
    """
    Get the message for a specific step.
    
    Args:
        flow (dict): The flow configuration
        step_id (str): The step ID to get the message for
        
    Returns:
        str: The message for the step
    """
    step = next(
        (step for step in flow['steps'] if step['id'] == step_id),
        None
    )
    return step.get('message', '') if step else ''

def get_or_create_chat_user(firm: Firm, phone_number: str, profile_name: str) -> ChatUser:
    """
    Get or create a chat user for the given firm and phone number.
    
    Args:
        firm (Firm): The firm object
        phone_number (str): The user's phone number
        profile_name (str): The user's profile name
        
    Returns:
        ChatUser: The chat user object
    """
    chat_user, created = ChatUser.objects.get_or_create(
        firm=firm,
        phone_number=phone_number,
        defaults={
            'profile_name': profile_name,
            'current_step': firm.first_step or 'start'
        }
    )
    return chat_user 