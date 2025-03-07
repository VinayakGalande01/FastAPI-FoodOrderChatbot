# FastAPI framework for building APIs
from fastapi import FastAPI
# Handles incoming HTTP requests
from fastapi import Request
# Returns responses in JSON format
from fastapi.responses import JSONResponse
# Custom database helper module
import db_helper
# Custom utility helper module
import generic_helper

# Creating a FastAPI app instance
app = FastAPI()

# Dictionary to store ongoing orders associated with session IDs
inprogress_orders = {}

# Define an endpoint to handle incoming webhook requests
@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request body payload
    payload = await request.json()

    # Extract the necessary information from the payload i.e.(Dialogflow Webhook request)
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName'] # Extract intent name
    parameters = payload['queryResult']['parameters'] # Extract user-provided parameters
    output_contexts = payload['queryResult']['outputContexts'] # Extract session context
    
    # Extract session ID from the context to track user session
    session_id = generic_helper.extract_session_id(output_contexts[0]["name"])

    # Dictionary mapping intent names to their corresponding handler functions
    intent_handler_dict = {
        'order.add-context:ongoing-order': add_to_order,
        'order.remove - context: ongoing-order': remove_from_order,
        'order.complete-context: ongoing order': complete_order,
        'track.order- context: ongoing-tracking': track_order
    }

    # Call the appropriate function based on the identified intent
    return intent_handler_dict[intent](parameters, session_id)

# Function to save the order to the database
def save_to_db(order: dict):
    # Get the next available order ID from the database
    next_order_id = db_helper.get_next_order_id()

    # Insert individual items along with quantity in orders table
    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )
        # If inserting an item fails, return an error code
        if rcode == -1:
            return -1

    # Now insert order tracking status i.e. Insert order tracking status as "in progress"
    db_helper.insert_order_tracking(next_order_id, "in progress")

    # Return the assigned order ID
    return next_order_id


# Function to complete an order
def complete_order(parameters: dict, session_id: str):
    # Check if there's an in-progress order for the session
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
    else:
        # Retrieve order details and attempt to save it to the database
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)
        # If there is an error saving the order, notify the user
        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                               "Please place a new order again"
        else:
            # Retrieve total order price from the database
            order_total = db_helper.get_total_order_price(order_id)

            fulfillment_text = f"Awesome. We have placed your order. " \
                               f"Here is your order id # {order_id}. " \
                               f"Your order total is {order_total} which you can pay at the time of delivery!"

        # Remove the completed order from the in-progress dictionary
        del inprogress_orders[session_id]

    # Return fulfillment response
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# Function to add items to an ongoing order
def add_to_order(parameters: dict, session_id: str):
    # Extract food items and their quantities from user input
    food_items = parameters["food_item"]
    quantities = parameters["number"]

    # Validate input data: Ensure food items and quantities match in length
    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry I didn't understand. Can you please specify food items and quantities clearly?"
    else:
        # Convert food items and quantities into a dictionary
        new_food_dict = dict(zip(food_items, quantities))

        # If session already exists, update the order; otherwise,create a new order
        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict

        # Generate a summary of the current order
        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far you have: {order_str}. Do you need anything else?"

    # Return fulfillment response
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


# Function to remove items from an ongoing order
def remove_from_order(parameters: dict, session_id: str):
    # Check if the session exists in the in-progress orders
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
        })

    # Extract food items to be removed
    food_items = parameters["food-item"]
    current_order = inprogress_orders[session_id]

    removed_items = []
    no_such_items = []

    # Iterate through the items to remove them if they exist in the order
    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    # Constructs the response message
    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulfillment_text = f' Your current order does not have {",".join(no_such_items)}'

    # if the order is now empty, notify the user
    if len(current_order.keys()) == 0:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    # Return fulfillment response
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

# Function to track an order's status
def track_order(parameters: dict, session_id: str):
    # Retrieve the order ID from user input
    order_id = int(parameters['order_id'])
    order_status = db_helper.get_order_status(order_id)
    
    # Construct a response based on the order status
    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"

    # Return fulfillment response
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
