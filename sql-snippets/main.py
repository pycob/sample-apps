# To use pycob, make sure to run `pip install pycob` in your terminal.
import pycob as cob
import pandas as pd
import datetime
import uuid

# List of admin usernames.
# TODO: Change this to the list of usernames of your admins.
admin_users = ["admin"]

# HELPER FUNCTIONS

# PAGE FUNCTIONS
# Each page function takes in a server_request object and returns a page object.
# The server_request object contains information about the request that was made to the server, including query parameters, form data, and the username of the user who is logged in.
# The page object contains information about the page that will be displayed to the user.
    
def create_snippet(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Create Snippet")

    # Get the username of the user who is logged in.
    username = server_request.get_username()

    # Check if the user has submitted any form data.
    if server_request.params():
        # If the user has submitted form data, create a new row in the database.
        page.add_text("Creating new row...")

        # Get the form data from the server request.
        form_data = server_request.params()
        form_data["author"] = username
        form_data["created_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        form_data["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # A UUID is a unique identifier that can be used to identify a row in the database.        
        form_data["id"] = str(uuid.uuid4())

        # Insert the new row into the database.
        server_request.store_dict(table_id="snippet", object_id=form_data["id"], value=form_data)

        with page.add_card() as card:
            card.add_header("Success!")
            card.add_text("Your new row has been created.")
            card.add_link("View Snippet", "/view_snippet?id=" + form_data["id"])

        return page

    with page.add_card() as card:
        card.add_header("Create Snippet")
        with card.add_form(action="/create_snippet", method="POST") as form:
            
            if username is not None and username != "": # Logged in users can write to this column
                form.add_formtext("Name", "Name")
            if username is not None and username != "": # Logged in users can write to this column
                form.add_formtext("Tables", "Tables")
            if username is not None and username != "": # Logged in users can write to this column
                form.add_formtextarea("Query", "Query")

            form.add_formsubmit("Create")
    
    return page
    
def update_snippet(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Update Snippet")

    username = server_request.get_username()

    snippet_id = server_request.params("id")

    data = server_request.retrieve_dict(table_id="snippet", object_id=snippet_id)

    with page.add_card() as card:
        card.add_header("Update Snippet")
        with card.add_form(action="/update_snippet") as form:
            form.add_formhidden("id", snippet_id)
    
            if username == data['author']: # Only the author can update this column
                form.add_formtext("Name", "Name", value=data["Name"] if "Name" in data else "")
            if username == data['author']: # Only the author can update this column
                form.add_formtext("Tables", "Tables", value=data["Tables"] if "Tables" in data else "")
            if username == data['author']: # Only the author can update this column
                form.add_formtextarea("Query", "Query", value=data["Query"] if "Query" in data else "")
    
            form.add_formsubmit("Update")
        
        return page
    
def delete_snippet(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Delete Snippet")

    snippet_id = server_request.params("id")

    data = server_request.retrieve_dict(table_id="snippet", object_id=snippet_id)

    username = server_request.get_username()
    # Only the author can delete this row
    if username is not None and username == data["author"]:
        if server_request.params("confirm") == "true":
            server_request.delete_dict(table_id="warranty_claim", object_id=warranty_claim_id)
            with page.add_card() as card:
                card.add_alert("Deleted", "Success", "green")
                card.add_link("Home", "/")
        else:
            with page.add_card() as card:
                card.add_header("Delete Snippet")
                with card.add_form(action="/delete_snippet") as form:
                    form.add_formhidden("id", snippet_id)
                    form.add_formhidden("confirm", "true")
                    form.add_formsubmit("Delete")
    else:
        page.add_alert("You do not have permission to delete this snippet.", "Error", "red")

    return page
    
def view_snippet(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Snippet")

    username = server_request.get_username()

    id = server_request.params("id")

    data = server_request.retrieve_dict(table_id="snippet", object_id=id)

    with page.add_card() as card:
        with card.add_rawtable() as table:
            with table.add_tablehead() as table_head:
                with table_head.add_tablerow() as table_row:
                    table_row.add_tablecellheader("Field Name")
                    table_row.add_tablecellheader("Field Value")
            with table.add_tablebody() as table_body:
                

                if True: # Anyone can read this column
                    with table_body.add_tablerow() as table_row:
                        table_row.add_tablecell("Name")
                        if "Name" in data:
                            table_row.add_tablecell(data["Name"])
                        else:
                            table_row.add_tablecell("")
                if True: # Anyone can read this column
                    with table_body.add_tablerow() as table_row:
                        table_row.add_tablecell("Tables")
                        if "Tables" in data:
                            table_row.add_tablecell(data["Tables"])
                        else:
                            table_row.add_tablecell("")
                if True: # Anyone can read this column
                    with table_body.add_tablerow() as table_row:
                        table_row.add_tablecell("Query")
                        if "Query" in data:
                            table_row.add_tablecell(data["Query"])
                        else:
                            table_row.add_tablecell("")
        with card.add_form(action="/delete_snippet") as form:
            form.add_formhidden("id", id)
            form.add_formsubmit("Delete")
        
        card.add_text("")

        with card.add_form(action="/update_snippet") as form:
            form.add_formhidden("id", id)
            form.add_formsubmit("Edit")

    return page   
    
def list_snippet(server_request: cob.Request) -> cob.Page:
    page = cob.Page("List of Snippets")
    
    username = server_request.get_username()

    snippets = server_request.list_objects(table_id="snippet")

    df = pd.DataFrame(snippets)

    action_buttons = [
        cob.Rowaction(label="View", url="/view_snippet?id={id}"),
        cob.Rowaction(label="Delete", url="/delete_snippet?id={id}"),
    ]

    page.add_pandastable(df, hide_fields=["id"], action_buttons=action_buttons)

    return page           
    
# APP CONFIGURATION
app = cob.App("Snippet", use_built_in_auth=True)
app.register_function(list_snippet)
app.register_function(create_snippet, require_login=True)
app.register_function(update_snippet, require_login=True, show_in_navbar=False, footer_category=None)
app.register_function(delete_snippet, require_login=True, show_in_navbar=False, footer_category=None)
app.register_function(view_snippet, show_in_navbar=False, footer_category=None)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
# Deploy to PyCob Hosting using `python3 -m pycob.deploy` or use your own hosting provider.
    