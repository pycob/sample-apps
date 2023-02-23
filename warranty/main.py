# INITIALIZATION
import pycob as cob
import pandas as pd
from datetime import datetime
import uuid
from faker import Faker
fake = Faker()


def save_entry(app: cob.App, username: str, object_id: str, name: str, email: str, phone: str, product: str, serial_number: str, purchase_date: str, purchase_location: str, purchase_price: str, description_of_issue: str):
    if object_id is None or object_id == "":
        object_id = str(uuid.uuid4())
        print(f"Creating new entry with object_id: {object_id}")
    else:
        print(f"Updating entry with object_id: {object_id}")

    data = {
        "claim_id": object_id,
        "name": name,
        "email": email,
        "phone": phone,
        "product": product,
        "serial_number": serial_number,
        "purchase_date": purchase_date,
        "purchase_location": purchase_location,
        "purchase_price": purchase_price,
        "description_of_issue": description_of_issue,
    }

    app.store_dict(table_id="claim", object_id=object_id, value=data)

def update_claim_fields(app: cob.App, claim_id: str, new_data: dict):
    data = app.retrieve_dict(table_id="claim", object_id=claim_id)

    print(f"Existing data: {data}")

    for key in new_data:
        data[key] = new_data[key]

    print(f"New data: {data}")

    app.store_dict(table_id="claim", object_id=claim_id, value=data)

# PAGE FUNCTIONS

# File a new warranty claim
def new_warranty_claim(server_request: cob.Request) -> cob.Page:
    page = cob.Page("New Warranty Claim")

    with page.add_card() as card:
        card.add_header("New Warranty Claim")
    
        with card.add_form(action="/save_claim", method="POST") as form:
            form.add_formtext("Name", name="name", placeholder="Name")
            form.add_formtext("Email", name="email", placeholder="Email")
            form.add_formtext("Phone", name="phone", placeholder="Phone")
            form.add_formtext("Product", name="product", placeholder="Product")
            form.add_formtext("Serial Number", name="serial_number", placeholder="Serial Number")
            form.add_formtext("Purchase Date", name="purchase_date", placeholder="Purchase Date")
            form.add_formtext("Purchase Location", name="purchase_location", placeholder="Purchase Location")
            form.add_formtext("Purchase Price", name="purchase_price", placeholder="Purchase Price")
            form.add_formtextarea("Description of Issue", name="description_of_issue", placeholder="Description of Issue")
            form.add_formsubmit("Submit")

    return page

def sample_warranty_claim(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Sample Warranty Claim")

    with page.add_card() as card:
        card.add_header("Sample Warranty Claim")
    
        with card.add_form(action="/save_claim", method="POST") as form:
            form.add_formtext("Name", name="name", placeholder="Name", value=fake.name())
            form.add_formtext("Email", name="email", placeholder="Email", value=fake.email())
            form.add_formtext("Phone", name="phone", placeholder="Phone", value=fake.phone_number())
            form.add_formtext("Product", name="product", placeholder="Product", value="Example Product")
            form.add_formtext("Serial Number", name="serial_number", placeholder="Serial Number", value=fake.ean())
            form.add_formtext("Purchase Date", name="purchase_date", placeholder="Purchase Date", value=fake.date())
            form.add_formtext("Purchase Location", name="purchase_location", placeholder="Purchase Location", value=fake.city())
            form.add_formtext("Purchase Price", name="purchase_price", placeholder="Purchase Price", value=str(fake.pricetag()))
            form.add_formtextarea("Description of Issue", name="description_of_issue", placeholder="Description of Issue")
            form.add_formsubmit("Submit")

    return page

def save_claim(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Save Claim")

    # Get the form data
    name = server_request.params("name")
    email = server_request.params("email")
    phone = server_request.params("phone")
    product = server_request.params("product")
    serial_number = server_request.params("serial_number")
    purchase_date = server_request.params("purchase_date")
    purchase_location = server_request.params("purchase_location")
    purchase_price = server_request.params("purchase_price")
    description_of_issue = server_request.params("description_of_issue")

    claim_id = server_request.params("claim_id")

    # Save the form data
    save_entry(server_request.app, server_request.get_username(), claim_id, name, email, phone, product, serial_number, purchase_date, purchase_location, purchase_price, description_of_issue)

    return page

def update_claim(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Update Claim")

    # Get the form data
    claim_id = server_request.params("claim_id")

    status = server_request.params("status")
    tracking_number = server_request.params("tracking_number")

    # Save the form data
    update_claim_fields(server_request.app, claim_id, {"status": status, "tracking_number": tracking_number})

    page.add_header("Claim Updated")

    return page

# Update an existing warranty claim
def update_warranty_claim(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Update Warranty Claim")

    claim_id = server_request.params("claim_id")

    if claim_id is None or claim_id == "":
        page.add_alert("No claim_id provided", "Error", "red")
        return page

    data = server_request.retrieve_dict(table_id="claim", object_id=claim_id)

    if data is None:
        page.add_alert("Claim not found", "Error", "red")
        return page

    with page.add_card() as card:
        card.add_header("Update Warranty Claim")
    
        with card.add_list() as list:
            list.add_listitem(f'<b>Name:</b> {data["name"]}')
            list.add_listitem(f'<b>Email:</b> {data["email"]}')
            list.add_listitem(f'<b>Phone:</b> {data["phone"]}')
            list.add_listitem(f'<b>Product:</b> {data["product"]}')
            list.add_listitem(f'<b>Serial Number:</b> {data["serial_number"]}')
            list.add_listitem(f'<b>Purchase Date:</b> {data["purchase_date"]}')
            list.add_listitem(f'<b>Purchase Location:</b> {data["purchase_location"]}')
            list.add_listitem(f'<b>Purchase Price:</b> {data["purchase_price"]}')
            list.add_listitem(f'<b>Description of Issue:</b> {data["description_of_issue"]}')            

        card.add_header("Claim Status", size=3)

        with card.add_form(action="/update_claim", method="POST") as form:
            # Pass the object_id to the form so we can update the entry
            form.add_formhidden("claim_id", value=claim_id)

            options = [
                {"label": "New", "value": "new"},
                {"label": "Investigating", "value": "investigating"},
                {"label": "Replacement Sent", "value": "replacement_sent"},
                {"label": "Closed", "value": "closed"},
            ]

            form.add_formselect("Status", name="status", options=options)
            form.add_formtext("Tracking Number", name="tracking_number", placeholder="Tracking Number", value=data["tracking_number"] if "tracking_number" in data else "")
            form.add_formsubmit("Submit")

    return page

def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Warranty Claim", image="https://storage.googleapis.com/img.pycob.com/screenshot/warranty.png")
    page.add_header("Warranty Claim")
    
    survey_results = app.list_objects(table_id="claim")

    df = pd.DataFrame(survey_results)

    action_buttons = [
        cob.Rowaction("{product}", "/data?product={product}", open_in_new_window=False),
        cob.Rowaction("{serial_number}", "/data?serial_number={serial_number}", open_in_new_window=False),
        cob.Rowaction("Update Status", "/update_warranty_claim?claim_id={claim_id}", open_in_new_window=False),
    ]

    page.add_datagrid(df, action_buttons=action_buttons)

    page.add_link("View the source code for this app", f"https://www.pycob.com/view_code?code_owner=warranty")

    return page

def edit_entry(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Edit Entry")

    object_id = server_request.params("object_id")

    data = server_request.retrieve_dict(table_id="survey", object_id=object_id)

    with page.add_card() as card:
        card.add_header("Edit Entry")
    
        with card.add_form(action="/", method="POST") as form:
            # Pass the object_id to the form so we can update the entry
            form.add_formhidden("object_id", value=object_id)
            form.add_formtext("Field 1", name="field1", placeholder="Field 1", value=data['field1'])
            form.add_formtext("Field 2", name="field2", placeholder="Field 2", value=data['field2'])
            form.add_formtext("Field 3", name="field3", placeholder="Field 3", value=data['field3'])
            form.add_formsubmit("Save")

    return page

def delete_entry(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Delete Entry")

    object_id = server_request.params("object_id")

    with page.add_card() as card:
        card.add_header("Delete Entry?")

        with card.add_form(action="/", method="POST") as form:
            form.add_formhidden("object_id", value=object_id)
            form.add_formhidden("confirm_delete", value="true")
            form.add_formsubmit("Delete")

    return page

def add_entry(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Add Entry")

    with page.add_card() as card:
        card.add_header("Add Entry")
    
        with card.add_form(action="/", method="POST") as form:
            form.add_formtext("Field 1", name="field1", placeholder="Field 1")
            form.add_formtext("Field 2", name="field2", placeholder="Field 2")
            form.add_formtext("Field 3", name="field3", placeholder="Field 3")
            form.add_formsubmit("Save")

    return page

# APP CONFIGURATION

app = cob.App("Warranty Claims Manager", use_built_in_auth=True)

app.register_function(home, show_in_navbar=False, footer_category=None)
app.register_function(new_warranty_claim, show_in_navbar=True, require_login=False, footer_category="Customer-Facing")
app.register_function(sample_warranty_claim, show_in_navbar=True, require_login=False, footer_category="Demo")
# In a production app, set the require_login=True for the following functions
app.register_function(update_warranty_claim, show_in_navbar=False, require_login=False, footer_category="Internal")
app.register_function(save_claim, show_in_navbar=False, require_login=False, footer_category=None)
app.register_function(update_claim, show_in_navbar=False, require_login=False, footer_category=None)
app.register_function(edit_entry, show_in_navbar=False, require_login=False, footer_category=None)
app.register_function(delete_entry, show_in_navbar=False, require_login=False, footer_category=None)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
