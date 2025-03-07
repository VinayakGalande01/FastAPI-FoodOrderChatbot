# Import the regular expression module
import re

# Function to extract session ID from a Dialogflow context string
def extract_session_id(session_str: str):
    """
    Extracts the session ID from Dialogflow's context string.
    """
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)   # Search for session ID pattern
    if match:
        extracted_string = match.group(1) # Extract the session ID from the matched group
        return extracted_string
    
    return ""  # Return empty string if no match is found


# Function to convert a dictionary of food items into a human-readable order summary
def get_str_from_food_dict(food_dict: dict):
    """
    Converts a food dictionary into a readable order summary.
    """
    # Example input: {"samosa": 2, "chole": 5} --> Output: "2 samosa, 5 chole"
    return ", ".join([f"{int(value)} {key}" for key, value in food_dict.items]) # Format order summary

# Main function to test the get_str_from_food_dict function
if __name__=="__main__":
    print(get_str_from_food_dict({"samosa":2, "chole":5}))
    


