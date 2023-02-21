# INITIALIZATION: Do not delete this comment
import pycob as cob
import pandas as pd
from datetime import datetime
import uuid

def save_entry(app: cob.App, username, object_id, field1, field2, field3):
    # Using an existing object_id will overwrite the data
    # Or otherwise create a new entry    
    if object_id is None or object_id == "":
        object_id = str(uuid.uuid4())

    data = {
        "object_id": object_id,
        "timestamp": datetime.now().isoformat(),
        "username": username,
        "field1": field1,
        "field2": field2,
        "field3": field3
    }
    app.store_dict(table_id="survey", object_id=object_id, value=data)

# PAGE FUNCTIONS: Do not delete this comment
def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Home")
    page.add_header("Survey Results")
    
    object_id = server_request.params("object_id")
    field1 = server_request.params("field1")
    field2 = server_request.params("field2")
    field3 = server_request.params("field3")

    if field1 and field2 and field3:
        save_entry(server_request.app, server_request.get_username(), object_id, field1, field2, field3)

        with page.add_card() as card:
            card.add_header("Saved")
            card.add_text(f"Field 1: {field1}")
            card.add_text(f"Field 2: {field2}")
            card.add_text(f"Field 3: {field3}")

    if server_request.params("confirm_delete") == "true":
        server_request.delete_dict(table_id="survey", object_id=object_id)

        with page.add_card() as card:
            card.add_header("Deleted")
            card.add_text(f"Object ID: {object_id}")

    app = server_request.app # type: cob.App

    survey_results = app.list_objects(table_id="survey")

    df = pd.DataFrame(survey_results)

    action_buttons = [
        cob.Rowaction("Edit", "/edit_entry?object_id={object_id}", open_in_new_window=False),
        cob.Rowaction("Delete", "/delete_entry?object_id={object_id}", open_in_new_window=False),
    ]

    page.add_datagrid(df, action_buttons=action_buttons)

    page.add_link("Add Entry", "/add_entry")
    page.add_link("View the source code for this app", f"https://github.com/pycob/example-survey/blob/main/main.py")

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

app = cob.App("Survey Template", use_built_in_auth=True)

app.register_function(home, show_in_navbar=False)
app.register_function(add_entry, show_in_navbar=True, require_login=False)
app.register_function(edit_entry, show_in_navbar=False, require_login=False)
app.register_function(delete_entry, show_in_navbar=False, require_login=False)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
