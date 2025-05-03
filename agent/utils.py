from typing import Dict, List, Any, Optional
import time
import re

def format_message(role: str, text: str) -> str:
    """Format a message with role label"""
    return f"{role}: {text}\n"

def extract_answer(text: str) -> Optional[str]:
    """
    Extract structured answer from text, handling multiple formats and ignoring formatting.
    
    Args:
        text: Text to extract answer from
        final_only: If True, only extract final answers
        
    Returns:
        Extracted answer or None if no answer found
    """
    # Remove markdown formatting to avoid interference
    clean_text = re.sub(r'\*\*|\*|__|\^|_', '', text)
    
    # First look for final answers with word boundary to avoid numbered list confusion
    final_match = re.search(r'\bFinal Answer:\s*([A-F0-9][^.\n]*)', clean_text, re.IGNORECASE)
    if final_match:
        return final_match.group(1).strip()
    
    # Look for intermediate answers with "Answer: X" format with word boundary
    int_match = re.search(r'\bAnswer:\s*([A-F0-9][^.\n]*)', clean_text, re.IGNORECASE)
    if int_match:
        return int_match.group(1).strip()
    
    # For multiple choice, look for option indicators
    mc_match = re.search(r'\b(option|choice)\s+([A-F])\b', clean_text, re.IGNORECASE)
    if mc_match:
        return mc_match.group(2).upper()
    
    # Look for standalone answer options
    standalone_match = re.search(r'\b([A-F])[\.:]', clean_text, re.IGNORECASE)
    if standalone_match:
        return standalone_match.group(1).upper()
    
    # No valid answer found
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