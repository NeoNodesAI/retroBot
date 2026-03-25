"""Response formatting and validation rules for retroBot."""


def format_response_with_disclaimer(response: str) -> str:
    """
    Add mandatory disclaimer to response if not already present.
    
    Args:
        response: The AI-generated response
        
    Returns:
        Response with disclaimer appended
    """
    disclaimer = "This is not investment advice."
    
    # Check if disclaimer already exists
    if disclaimer.lower() not in response.lower():
        # Add disclaimer with proper spacing
        if response.strip():
            response = response.strip() + "\n\n" + disclaimer
        else:
            response = disclaimer
    
    return response


def validate_response(response: str) -> dict:
    """
    Validate response against retroBot rules.
    
    Args:
        response: The AI-generated response
        
    Returns:
        dict with validation results
    """
    issues = []
    
    # Check for follow-up questions
    follow_up_patterns = [
        "would you like",
        "do you want",
        "should i",
        "would you prefer",
        "do you need",
        "is this what you meant",
        "did you mean",
        "shall i",
        "can i help",
        "anything else",
        "let me know if",
    ]
    
    response_lower = response.lower()
    
    for pattern in follow_up_patterns:
        if pattern in response_lower:
            issues.append(f"Contains follow-up question pattern: '{pattern}'")
    
    # Check for yes/no questions
    if "?" in response:
        # More sophisticated check could be added here
        lines = response.split("\n")
        for line in lines:
            if "?" in line and any(word in line.lower() for word in ["would", "should", "do you", "can you"]):
                issues.append(f"Contains potential yes/no question: '{line.strip()}'")
    
    # Check for disclaimer
    if "not investment advice" not in response_lower:
        issues.append("Missing investment advice disclaimer")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "response": response
    }


# Banned phrases that should never appear in responses
BANNED_PHRASES = [
    "Would you like me to",
    "Do you want me to",
    "Should I provide",
    "Should I explain",
    "Is this what you meant",
    "Did you mean",
    "Would you prefer",
    "Do you need",
    "Shall I",
    "Can I help with",
    "Let me know if you'd like",
    "Feel free to ask if",
    "Would it be helpful if",
]


# Required elements in every response
REQUIRED_ELEMENTS = [
    "This is not investment advice."
]


def clean_response(response: str) -> str:
    """
    Clean response by removing banned phrases and ensuring compliance.
    
    Args:
        response: Raw AI response
        
    Returns:
        Cleaned and compliant response
    """
    # Remove any banned phrases
    cleaned = response
    for phrase in BANNED_PHRASES:
        if phrase in cleaned:
            # Remove the entire sentence containing the banned phrase
            sentences = cleaned.split(".")
            cleaned = ".".join([s for s in sentences if phrase not in s])
    
    # Ensure disclaimer is present
    cleaned = format_response_with_disclaimer(cleaned)
    
    return cleaned.strip()

