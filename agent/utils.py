from typing import Dict, List, Any, Optional
import time
import re

def format_message(role: str, text: str) -> str:
    """Format a message with role label"""
    return f"{role}: {text}\n"

def extract_answer(text: str, answer_format: str = "letter") -> Optional[str]:
    """
    Extract answer from text based on expected format
    
    Args:
        text: Text to extract answer from
        answer_format: Expected format ('letter', 'integer', 'word', etc.)
    """
    # Look for Final Answer: X pattern
    match = re.search(r'Final Answer:\s*([^\n]+)', text, re.IGNORECASE)
    if not match:
        # Fallback to Answer: X
        match = re.search(r'Answer:\s*([^\n]+)', text, re.IGNORECASE)
    
    if not match:
        return None
        
    answer = match.group(1).strip()
    
    # Validate format
    if answer_format == "letter":
        # Extract just the letter if there's extra text
        letter_match = re.search(r'^\*{0,2}([A-Z])\*{0,2}', answer, re.IGNORECASE)
        if letter_match:
            return letter_match.group(1).upper()
    elif answer_format == "integer":
        # Check for work-in-progress indicators
        if re.search(r'Answer:\s*\[(working|calculating|in progress)\]', answer, re.IGNORECASE):
            return None  # Don't count as a real answer
        # Extract just the integer
        int_match = re.search(r'^\*{0,2}(-?\d+)\*{0,2}', answer)
        if int_match:
            return int_match.group(1)
    elif answer_format == "word":
        # Extract just the first word
        word_match = re.search(r'^\*{0,2}([a-zA-Z]+)\*{0,2}', answer)
        if word_match:
            return word_match.group(1)
    else:
        # Return as-is for unknown formats
        return answer
    
    return None

def parse_agent_message(message: Dict[str, str]) -> Dict[str, Any]:
    """
    Parse an agent message to extract the role and content
    
    Args:
        message: Message dictionary with role and content keys
        
    Returns:
        Dictionary with extracted role and content
    """
    result = {
        "original_role": message["role"],
        "original_content": message["content"],
    }
    
    # If message is from assistant or user, try to extract agent role
    if message["role"] in ["assistant", "user"]:
        content = message["content"]
        
        # Try to match "Agent X: content"
        match = re.match(r"^(Agent [AB]):\s*(.*)", content, re.DOTALL)
        if match:
            result["role"] = match.group(1)
            result["content"] = match.group(2).strip()
        else:
            # No explicit agent role, use original
            result["role"] = message["role"]
            result["content"] = content
    else:
        # For system messages, keep as is
        result["role"] = message["role"]
        result["content"] = message["content"]
        
    return result
    
def measure_response_time(func):
    """Decorator to measure response time of a function"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Function {func.__name__} took {elapsed_time:.2f} seconds")
        return result
    return wrapper