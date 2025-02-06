import re

def extract_session_id(session_str: str):
    """
    Extracts the session ID from Dialogflow's context string.
    """
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string
    
    return ""

def get_str_from_food_dict(food_dict: dict):
    """
    Converts a food dictionary into a readable order summary.
    """
    return ", ".join([f"{int(value)} {key}" for key, value in food_dict.items])

if __name__=="__main__":
    print(get_str_from_food_dict({"samosa":2, "chole":5}))
    


