# INITIALIZATION
import pycob as cob



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
            form.add_formselect("Field Data Type", "field_type_{}".format(i), options=options)
            form.add_formselect("Column Write Authorization", "column_write_auth_{}".format(i), options=[{"value": "anyone", "label": "Anyone"}, {"value": "logged_in", "label": "Logged In Users"}, {"value": "author", "label": "Author (the person who created the row)"}, {"value": "admin", "label": "Admins Only"}])
            form.add_formselect("Column Read Authorization", "column_read_auth_{}".format(i), options=[{"value": "anyone", "label": "Anyone"}, {"value": "logged_in", "label": "Logged In Users"}, {"value": "author", "label": "Author (the person who created the row)"}, {"value": "admin", "label": "Admins Only"}])
            form.add_formsubmit("Add") 

    if i > 1:
        page.add_header("Generated Code")
        page.add_text("Use this as a starting point for your app.")
        page.add_codeeditor(generate_code(server_request.params()))        

    return page

def generate_preamble(params: dict) -> str:
    return f"""import pycob as cob

# PAGE FUNCTIONS
    """

def generate_create_row(params: dict) -> str:
    table_name = params["table_name"]
    row_creation_auth = params["row_creation_auth"]
    row_edit_auth = params["row_edit_auth"]
    row_delete_auth = params["row_delete_auth"]

    code = f"""
def create_{table_name}(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Create {table_name}")

    with page.add_card() as card:
        card.add_header("Create {table_name.title()}")
        # This form will be submitted to the get_{table_name} function, which will handle the creation of the row.
        with card.add_form(action="/get_{table_name}") as form:
            form.add_formhidden("modification_type", "create")
            """

    i = 1

    while f"field_name_{i}" in params and params[f"field_name_{i}"] is not None and params[f"field_name_{i}"] != "":
        field_name = params[f"field_name_{i}"]
        field_type = params[f"field_type_{i}"]
        column_write_auth = params[f"column_write_auth_{i}"]
        column_read_auth = params[f"column_read_auth_{i}"]

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
    """

    return code

def generate_update_row(params: dict) -> str:
    table_name = params["table_name"]
    row_creation_auth = params["row_creation_auth"]
    row_edit_auth = params["row_edit_auth"]
    row_delete_auth = params["row_delete_auth"]

    code = f"""
def update_{table_name}(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Update {table_name}")

    {table_name}_id = server_request.params("id")

    with page.add_card() as card:
        card.add_header("Update {table_name.title()}")
        # This form will be submitted to the get_{table_name} function, which will handle the row update
        with card.add_form(action="/get_{table_name}") as form:
            form.add_formhidden("modification_type", "update")
            form.add_formhidden("id", {table_name}_id)
    """

    i = 1

    while f"field_name_{i}" in params and params[f"field_name_{i}"] is not None and params[f"field_name_{i}"] != "":
        field_name = params[f"field_name_{i}"]
        field_type = params[f"field_type_{i}"]
        column_write_auth = params[f"column_write_auth_{i}"]
        column_read_auth = params[f"column_read_auth_{i}"]

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
    
            form.add_formsubmit("Update")
    """

    return code

def generate_delete_row(params: dict) -> str:
    table_name = params["table_name"]
    row_creation_auth = params["row_creation_auth"]
    row_edit_auth = params["row_edit_auth"]
    row_delete_auth = params["row_delete_auth"]

    code = f"""
def delete_{table_name}(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Delete {table_name}")

    {table_name}_id = server_request.params("id")

    with page.add_card() as card:
        card.add_header("Delete {table_name.title()}")
        with card.add_form(action="/delete_{table_name}") as form:
            form.add_formhidden("modification_type", "delete")
            form.add_formhidden("id", {table_name}_id)
    """

    return code


def generate_get_row(params: dict) -> str:
    table_name = params["table_name"]
    row_creation_auth = params["row_creation_auth"]
    row_edit_auth = params["row_edit_auth"]
    row_delete_auth = params["row_delete_auth"]

    code = f"""
def get_{table_name}(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Get {table_name}")

    {table_name}_id = server_request.params("id")

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
    page = cob.Page("Get {table_name}s")


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
app = cob.App("{table_name}", use_built_in_auth=True)
app.register_function(create_{table_name}{", require_login=True" if row_creation_auth != "anyone" else ""})
app.register_function(update_{table_name}{", require_login=True" if row_edit_auth != "anyone" else ""})
app.register_function(delete_{table_name}, require_login=True)
app.register_function(get_{table_name})

server = app.run()
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
