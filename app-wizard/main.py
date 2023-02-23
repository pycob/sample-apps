# INITIALIZATION
import pycob as cob

def to_title(s: str) -> str:
    return s.title().replace("_", " ")

def to_snake(s: str) -> str:
    return s.lower().replace(" ", "_")

# PAGE FUNCTIONS    
def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Home")

    page.add_text("Use this tool to generate the code for a new app. It will generate a basic app with a table and fields. You can then customize the app to add more functionality.")
    with page.add_card() as card:
        card.add_header("Table Setup")
        with card.add_form(action="/add_field") as form:
            form.add_text("What is the 'thing' you want to store/track?")
            form.add_formtext("Table Name", "table_name")
            form.add_text("Who can create rows?")      
            form.add_formselect("Row Creation Authorization", "row_creation_auth", options=[{"value": "anyone", "label": "Anyone"}, {"value": "logged_in", "label": "Logged In Users"}, {"value": "admin", "label": "Admins Only"}])
            form.add_text("Who can update rows?")
            form.add_formselect("Row Update Authorization", "row_edit_auth", options=[{"value": "anyone", "label": "Anyone"}, {"value": "logged_in", "label": "Logged In Users"}, {"value": "author", "label": "Author (the person who created the row)"}, {"value": "admin", "label": "Admins Only"}])
            form.add_text("Who can delete rows?")
            form.add_formselect("Row Delete Authorization", "row_delete_auth", options=[{"value": "author", "label": "Author (the person who created the row)"}, {"value": "admin", "label": "Admins Only"}, {"value": "none", "label": "No One"}])
            form.add_formsubmit("Next")

    return page

def add_field(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Add Field")

    table_name = server_request.params("table_name")

    # page.add_header(f"Fields for Table {table_name}")        

    # i = 1
    # while server_request.params(f"field_name_{i}") is not None and server_request.params(f"field_name_{i}") != "":
    #     field_name = server_request.params(f"field_name_{i}")
    #     field_type = server_request.params(f"field_type_{i}")
    #     page.add_text(f"{field_name} ({field_type})")
    #     i += 1

    with page.add_card() as card:
        card.add_header("Add Field")
        with card.add_form(action="/add_field") as form:
            form.add_formhidden("table_name", table_name)

            row_creation_auth = server_request.params("row_creation_auth")
            row_edit_auth = server_request.params("row_edit_auth")
            row_delete_auth = server_request.params("row_delete_auth")
            form.add_formhidden("row_creation_auth", row_creation_auth)
            form.add_formhidden("row_edit_auth", row_edit_auth)
            form.add_formhidden("row_delete_auth", row_delete_auth)

            i = 1
            while server_request.params(f"field_name_{i}") is not None and server_request.params(f"field_name_{i}") != "":
                field_name = server_request.params(f"field_name_{i}")
                field_type = server_request.params(f"field_type_{i}")
                column_write_auth = server_request.params(f"column_write_auth_{i}")
                column_read_auth = server_request.params(f"column_read_auth_{i}")
                form.add_formhidden(f"field_name_{i}", field_name)
                form.add_formhidden(f"field_type_{i}", field_type)
                form.add_formhidden(f"column_write_auth_{i}", column_write_auth)
                form.add_formhidden(f"column_read_auth_{i}", column_read_auth)
                i += 1

            form.add_formtext("Field Name", "field_name_{}".format(i))
            options = [{"value": "short_text", "label": "Short Text"}, {"value": "email", "label": "Email"}, {"value": "long_text", "label": "Long Text"}, {"value": "dropdown", "label": "Dropdown"}]
            form.add_formselect("Field Data Type", "field_type_{}".format(i), options=options, value="short_text")
            form.add_formselect("Column Write Authorization", "column_write_auth_{}".format(i), options=[{"value": "anyone", "label": "Anyone"}, {"value": "logged_in", "label": "Logged In Users"}, {"value": "author", "label": "Author (the person who created the row)"}, {"value": "admin", "label": "Admins Only"}], value="author")
            form.add_formselect("Column Read Authorization", "column_read_auth_{}".format(i), options=[{"value": "anyone", "label": "Anyone"}, {"value": "logged_in", "label": "Logged In Users"}, {"value": "author", "label": "Author (the person who created the row)"}, {"value": "admin", "label": "Admins Only"}], value="author")
            form.add_formsubmit("Add") 

    if i > 1:
        page.add_header("Generated Code")
        page.add_text("Use this as a starting point for your app.")

        code = generate_code(server_request.params())
        page.add_codeeditor(code)
        # Write code to output.py
        with open("output.py", "w") as f:
            f.write(code)
        f.close()

    return page

def generate_preamble(params: dict) -> str:
    code = f"""# To use pycob, make sure to run `pip install pycob` in your terminal.
import pycob as cob
import pandas as pd
import datetime
import uuid

# List of admin usernames.
# TODO: Change this to the list of usernames of your admins.
admin_users = ["admin"]

# HELPER FUNCTIONS
"""
    

    code += f"""
# PAGE FUNCTIONS
# Each page function takes in a server_request object and returns a page object.
# The server_request object contains information about the request that was made to the server, including query parameters, form data, and the username of the user who is logged in.
# The page object contains information about the page that will be displayed to the user.
    """

    return code

def generate_create_row(params: dict) -> str:
    table_name = params["table_name"]
    row_creation_auth = params["row_creation_auth"]
    row_edit_auth = params["row_edit_auth"]
    row_delete_auth = params["row_delete_auth"]

    code = f"""
def create_{table_name}(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Create {to_title(table_name)}")

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
        server_request.store_dict(table_id="{to_snake(table_name)}", object_id=form_data["id"], value=form_data)

        with page.add_card() as card:
            card.add_header("Success!")
            card.add_text("Your new row has been created.")
            card.add_link("View {to_title(table_name)}", "/view_{table_name}?id=" + form_data["id"])

        return page

    with page.add_card() as card:
        card.add_header("Create {to_title(table_name)}")
        with card.add_form(action="/create_{table_name}", method="POST") as form:
            """

    i = 1

    while f"field_name_{i}" in params and params[f"field_name_{i}"] is not None and params[f"field_name_{i}"] != "":
        field_name = params[f"field_name_{i}"]
        field_type = params[f"field_type_{i}"]
        column_write_auth = params[f"column_write_auth_{i}"]
        column_read_auth = params[f"column_read_auth_{i}"]

        if column_write_auth == "anyone":
            code += f"""
            if True: # Anyone can write to this column"""
        elif column_write_auth == "logged_in" or column_write_auth == "author":
            code += f"""
            if username is not None and username != "": # Logged in users can write to this column"""
        elif column_write_auth == "admin":
            code += f"""
            if username in admin_users: # Admins can write to this column"""

        if field_type == "short_text":
            code += f"""
                form.add_formtext("{field_name.title()}", "{field_name}")"""
        elif field_type == "email":
            code += f"""
                form.add_formemail("{field_name.title()}", "{field_name}")"""
        elif field_type == "long_text":
            code += f"""
                form.add_formtextarea("{field_name.title()}", "{field_name}")"""
        elif field_type == "dropdown":
            code += f"""
                form.add_formselect("{field_name.title()}", "{field_name}", options=[{{"value": "option_1", "label": "Option 1"}}, {{"value": "option_2", "label": "Option 2"}}])"""

        i += 1

    code += f"""

            form.add_formsubmit("Create")
    
    return page
    """

    return code

def generate_update_row(params: dict) -> str:
    table_name = params["table_name"]
    row_creation_auth = params["row_creation_auth"]
    row_edit_auth = params["row_edit_auth"]
    row_delete_auth = params["row_delete_auth"]

    code = f"""
def update_{table_name}(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Update {to_title(table_name)}")

    username = server_request.get_username()

    {table_name}_id = server_request.params("id")

    data = server_request.retrieve_dict(table_id="{table_name}", object_id={table_name}_id)

    with page.add_card() as card:
        card.add_header("Update {to_title(table_name)}")
        with card.add_form(action="/update_{table_name}") as form:
            form.add_formhidden("id", {table_name}_id)
    """

    i = 1

    while f"field_name_{i}" in params and params[f"field_name_{i}"] is not None and params[f"field_name_{i}"] != "":
        field_name = params[f"field_name_{i}"]
        field_type = params[f"field_type_{i}"]
        column_write_auth = params[f"column_write_auth_{i}"]
        column_read_auth = params[f"column_read_auth_{i}"]

        if column_write_auth == "anyone":
            code += f"""
            if True: # Anyone can write to this column"""
        elif column_write_auth == "logged_in":
            code += f"""
            if username is not None and username != "": # Logged in users can update this column"""
        elif column_write_auth == "author":
            code += f"""
            if username == data['author']: # Only the author can update this column"""
        elif column_write_auth == "admin":
            code += f"""
            if username in admin_users: # Admins can update this column"""

        if field_type == "short_text":
            code += f"""
                form.add_formtext("{field_name.title()}", "{field_name}", value=data["{field_name}"] if "{field_name}" in data else "")"""
        elif field_type == "email":
            code += f"""
                form.add_formtext("{field_name.title()}", "{field_name}", value=data["{field_name}"] if "{field_name}" in data else "")"""
        elif field_type == "long_text":
            code += f"""
                form.add_formtextarea("{field_name.title()}", "{field_name}", value=data["{field_name}"] if "{field_name}" in data else "")"""
        elif field_type == "dropdown":
            code += f"""
                form.add_formselect("{field_name.title()}", "{field_name}", options=[{{"value": "option_1", "label": "Option 1"}}, {{"value": "option_2", "label": "Option 2"}}], value=data["{field_name}"] if "{field_name}" in data else "")"""

        i += 1

    code += f"""
    
            form.add_formsubmit("Update")
        
        return page
    """

    return code

def generate_delete_row(params: dict) -> str:
    table_name = params["table_name"]
    row_creation_auth = params["row_creation_auth"]
    row_edit_auth = params["row_edit_auth"]
    row_delete_auth = params["row_delete_auth"]

    code = f"""
def delete_{table_name}(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Delete {to_title(table_name)}")

    {table_name}_id = server_request.params("id")

    data = server_request.retrieve_dict(table_id="{table_name}", object_id={table_name}_id)

    username = server_request.get_username()
    """

    if row_delete_auth == "author":
        code += f"""# Only the author can delete this row
    if username is not None and username == data["author"]:"""
    elif row_delete_auth == "admin":
        code += f""" # Admins can delete this row
    if username is not None and username in admin_users:"""
    else:
        code += f""" # Nobody can delete this row
    if False:"""

    code += f"""
        if server_request.params("confirm") == "true":
            server_request.delete_dict(table_id="warranty_claim", object_id=warranty_claim_id)
            with page.add_card() as card:
                card.add_alert("Deleted", "Success", "green")
                card.add_link("Home", "/")
        else:
            with page.add_card() as card:
                card.add_header("Delete {to_title(table_name)}")
                with card.add_form(action="/delete_{table_name}") as form:
                    form.add_formhidden("id", {table_name}_id)
                    form.add_formhidden("confirm", "true")
                    form.add_formsubmit("Delete")
    else:
        page.add_alert("You do not have permission to delete this {table_name}.", "Error", "red")

    return page
    """

    return code


def generate_get_row(params: dict) -> str:
    table_name = params["table_name"]
    row_creation_auth = params["row_creation_auth"]
    row_edit_auth = params["row_edit_auth"]
    row_delete_auth = params["row_delete_auth"]

    code = f"""
def view_{table_name}(server_request: cob.Request) -> cob.Page:
    page = cob.Page("{to_title(table_name)}")

    username = server_request.get_username()

    id = server_request.params("id")

    data = server_request.retrieve_dict(table_id="{to_snake(table_name)}", object_id=id)

    with page.add_card() as card:
        with card.add_rawtable() as table:
            with table.add_tablehead() as table_head:
                with table_head.add_tablerow() as table_row:
                    table_row.add_tablecellheader("Field Name")
                    table_row.add_tablecellheader("Field Value")
            with table.add_tablebody() as table_body:
                
"""

    i = 1

    while f"field_name_{i}" in params and params[f"field_name_{i}"] is not None and params[f"field_name_{i}"] != "":
        field_name = params[f"field_name_{i}"]
        field_type = params[f"field_type_{i}"]
        column_write_auth = params[f"column_write_auth_{i}"]
        column_read_auth = params[f"column_read_auth_{i}"]

        if column_read_auth == "anyone":
            code += f"""
                if True: # Anyone can read this column"""
        elif column_read_auth == "logged_in":
            code += f"""
                if username is not None and username != "": # Logged in users can read this column"""
        elif column_read_auth == "author":
            code += f"""
                if username == data["author"]: # Only the author can read this column"""
        elif column_read_auth == "admin":
            code += f"""
                if username in admin_users: # Admins can read this column"""

        code += f"""
                    with table_body.add_tablerow() as table_row:
                        table_row.add_tablecell("{field_name.title()}")
                        if "{field_name}" in data:
                            table_row.add_tablecell(data["{field_name}"])
                        else:
                            table_row.add_tablecell("")"""

        i += 1

    code += f"""
        with card.add_form(action="/delete_{table_name}") as form:
            form.add_formhidden("id", id)
            form.add_formsubmit("Delete")
        
        card.add_text("")

        with card.add_form(action="/update_{table_name}") as form:
            form.add_formhidden("id", id)
            form.add_formsubmit("Edit")

    return page   
    """

    return code

def generate_get_table(params: dict) -> str:
    table_name = params["table_name"]
    row_creation_auth = params["row_creation_auth"]
    row_edit_auth = params["row_edit_auth"]
    row_delete_auth = params["row_delete_auth"]

    code = f"""
def list_{table_name}(server_request: cob.Request) -> cob.Page:
    page = cob.Page("List of {to_title(table_name)}s")
    
    username = server_request.get_username()

    {to_snake(table_name)}s = server_request.list_objects(table_id="{to_snake(table_name)}")

    df = pd.DataFrame({to_snake(table_name)}s)

    action_buttons = [
        cob.Rowaction(label="View", url="/view_{table_name}?id={{id}}"),
        cob.Rowaction(label="Delete", url="/delete_{table_name}?id={{id}}"),
    ]

    page.add_pandastable(df, hide_fields=["id"], action_buttons=action_buttons)

    return page           
    """

    return code

def generate_app_setup(params: dict) -> str:
    table_name = params["table_name"]
    row_creation_auth = params["row_creation_auth"]
    row_edit_auth = params["row_edit_auth"]
    row_delete_auth = params["row_delete_auth"]

    code = f"""
# APP CONFIGURATION
app = cob.App("{to_title(table_name)}", use_built_in_auth=True)
app.register_function(create_{table_name}{", require_login=True" if row_creation_auth != "anyone" else ""})
app.register_function(list_{table_name})
app.register_function(update_{table_name}{", require_login=True" if row_edit_auth != "anyone" else ""}, show_in_navbar=False, footer_category=None)
app.register_function(delete_{table_name}, require_login=True, show_in_navbar=False, footer_category=None)
app.register_function(view_{table_name}, show_in_navbar=False, footer_category=None)

server = app.run(port=5050)
# Run this using `python3 main.py` or `python main.py` depending on your system.
# Deploy to PyCob Hosting using `python3 -m pycob.deploy` or use your own hosting provider.
    """

    return code

def generate_code(params: dict) -> str:
    return generate_preamble(params) + generate_create_row(params) + generate_update_row(params) + generate_delete_row(params) + generate_get_row(params) + generate_get_table(params) + generate_app_setup(params)

# APP CONFIGURATION

app = cob.App("App Wizard", use_built_in_auth=False)

app.register_function(home)
app.register_function(add_field)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
