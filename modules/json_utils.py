import re
import json

def extract_json_string(raw_text):
    """
    Locates the JSON block inside text.
    Handles ```json ... ``` codeblocks or loose text surrounding JSON.
    """
    if not raw_text:
        return ""
        
    raw_text = raw_text.strip()
    
    # 1. Try to extract from ```json ... ``` block
    json_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, re.DOTALL | re.IGNORECASE)
    if json_block_match:
        return json_block_match.group(1).strip()
        
    # 2. Try to find the first '{' and last '}'
    first_brace = raw_text.find('{')
    last_brace = raw_text.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return raw_text[first_brace:last_brace + 1].strip()
        
    return raw_text

def repair_json_formatting(json_str):
    """
    Attempts to clean up common minor JSON syntax anomalies.
    """
    if not json_str:
        return ""
        
    # Remove comments (like // comments)
    json_str = re.sub(r'^\s*//.*$', '', json_str, flags=re.MULTILINE)
    
    # Remove trailing commas inside lists or objects before a closing brace/bracket
    json_str = re.sub(r',\s*\}', '}', json_str)
    json_str = re.sub(r',\s*\]', ']', json_str)
    
    # Replace single quotes enclosing keys/values with double quotes
    # Match 'key': or 'value'
    # Simple replacement if possible, but be careful with apostrophes
    # Let's fix keys first: 'name': -> "name":
    json_str = re.sub(r"\'(\w+)\'\s*:", r'"\1":', json_str)
    
    # Fix unescaped control characters inside strings
    # Especially raw newlines inside JSON string values:
    # We find quotes containing lines that don't end in quotes, and escape the newlines.
    # A safer approximation is replacing actual newlines with \n when inside string blocks:
    # For simplicity, we can escape control chars that JSON loads complains about.
    
    return json_str

def parse_and_validate_json(raw_text, required_keys=None):
    """
    Attempts to extract, repair, parse, and validate JSON.
    Returns:
        tuple (dict, bool): Parsed JSON dictionary and success status.
    """
    cleaned_str = extract_json_string(raw_text)
    
    # Try direct parse
    try:
        data = json.loads(cleaned_str)
        if validate_keys(data, required_keys):
            return data, True
    except Exception:
        pass
        
    # Try repair
    repaired_str = repair_json_formatting(cleaned_str)
    try:
        data = json.loads(repaired_str)
        if validate_keys(data, required_keys):
            return data, True
    except Exception:
        pass
        
    return None, False

def validate_keys(data, required_keys):
    """
    Checks if all required keys exist in the dictionary.
    """
    if not isinstance(data, dict):
        return False
    if not required_keys:
        return True
    return all(key in data for key in required_keys)

def execute_with_retry_and_fallback(llm_call_func, prompt_args, required_keys, fallback_data):
    """
    Orchestrates the GenAI pipeline:
    1. Tries to call the LLM using llm_call_func(*prompt_args).
    2. Parses the result.
    3. If invalid, does ONE self-correction retry call using a correction prompt.
    4. If still invalid, returns the fallback_data.
    """
    # First attempt
    raw_response, raw_metrics = llm_call_func(*prompt_args)
    parsed, success = parse_and_validate_json(raw_response, required_keys)
    
    if success:
        return parsed, raw_metrics
        
    # vLLM/LLM is active but output was malformed. Try retry.
    # Check if we are in local mock mode (if so, fallback will trigger anyway, but let's be safe)
    try:
        system_prompt, user_content = prompt_args[0], prompt_args[1]
        
        # Build strict correction prompt
        correction_system = (
            "You are a strict JSON correction assistant. You must output ONLY a valid JSON object. "
            "Do not include explanations, text wrapper prefaces, or markdown blocks except direct JSON.\n"
            f"Your output MUST contain these keys: {required_keys}"
        )
        correction_user = (
            "Your previous response failed to parse as valid JSON.\n"
            f"Required structure keys: {required_keys}\n"
            f"Failed Response:\n{raw_response}\n\n"
            "Correct the output and return only the repaired valid JSON block."
        )
        
        # Call LLM again
        retry_response, retry_metrics = llm_call_func(correction_system, correction_user)
        parsed_retry, success_retry = parse_and_validate_json(retry_response, required_keys)
        
        if success_retry:
            # Accumulate metrics
            combined_metrics = {
                "latency_seconds": raw_metrics.get("latency_seconds", 0) + retry_metrics.get("latency_seconds", 0),
                "prompt_tokens": raw_metrics.get("prompt_tokens", 0) + retry_metrics.get("prompt_tokens", 0),
                "completion_tokens": raw_metrics.get("completion_tokens", 0) + retry_metrics.get("completion_tokens", 0),
                "tokens_per_second": (raw_metrics.get("completion_tokens", 0) + retry_metrics.get("completion_tokens", 0)) / 
                                     (raw_metrics.get("latency_seconds", 1) + retry_metrics.get("latency_seconds", 1))
            }
            return parsed_retry, combined_metrics
    except Exception:
        pass
        
    # Return fallback
    return fallback_data, raw_metrics
