# To use pycob, make sure to run `pip install pycob` in your terminal.
import pycob as cob
import pandas as pd
import datetime
import uuid
import sqlite3 as db

# List of admin usernames.
# TODO: Change this to the list of usernames of your admins.
admin_users = ["admin"]

# HELPER FUNCTIONS
conn = db.connect('northwind.db', check_same_thread=False)

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
        form_data["last_run"] = ""
        form_data["rows_returned"] = 0

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
                form.add_formtext("Query Name", "Name", placeholder="Descriptive Name for this Query")
            if username is not None and username != "": # Logged in users can write to this column
                form.add_formtext("Tables Used", "Tables", placeholder="Table1, Table2")
            if username is not None and username != "": # Logged in users can write to this column
                form.add_formtextarea("Query", "Query", placeholder="SELECT *\nFROM Table1\nWHERE ...")

            form.add_formsubmit("Create")
    
    return page
    
def update_snippet(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Update Snippet")

    username = server_request.get_username()

    snippet_id = server_request.params("id")

    data = server_request.retrieve_dict(table_id="snippet", object_id=snippet_id)

    form_data = server_request.params()
    if "Query" in form_data:
        data["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data["author"] = username
        data["Query"] = form_data["Query"]
        data["Name"] = form_data["Name"]
        data["Tables"] = form_data["Tables"]        
        server_request.store_dict(table_id="snippet", object_id=snippet_id, value=data)
        with page.add_card() as card:
            card.add_header("Success!")
            card.add_text("Your row has been updated.")
            card.add_link("View Snippet", "/view_snippet?id=" + snippet_id)
        return page


    with page.add_card() as card:
        card.add_header("Update Snippet")
        with card.add_form(action="/update_snippet", method="POST") as form:
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
            server_request.delete_dict(table_id="snippet", object_id=snippet_id)
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

    username = server_request.get_username()

    id = server_request.params("id")

    data = server_request.retrieve_dict(table_id="snippet", object_id=id)

    page = cob.Page("Snippet" if "Name" not in data else data["Name"])

    with page.add_container(grid_columns=6) as container:
        container.add_header("Snippet" if "Name" not in data else data["Name"], classes="col-span-3")

        with container.add_container(grid_columns=2) as actions:
            with actions.add_container() as delete:
                with delete.add_form(action="/delete_snippet") as form:
                    form.add_formhidden("id", id)
                    form.add_formsubmit("Delete")
            
            with actions.add_container() as edit:
                with edit.add_form(action="/update_snippet") as form:
                    form.add_formhidden("id", id)
                    form.add_formsubmit("Edit")

    with page.add_card() as card:
        # Put the data into a dataframe, excluding the query
        df = pd.DataFrame(pd.Series(data, name="Fields")).reset_index().query("index != 'Query'")
        card.add_pandastable(df)

    page.add_codeeditor(data["Query"], "sql")

    page.add_html("""
    <button class="mt-5 text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm w-full sm:w-auto px-5 py-2.5 text-center dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800" onclick="runCode()">Run SQL</button>
    <script>
        function runCode() {
            var code = editor.getValue();

            document.getElementById("sql_val").value = code

            document.getElementById("code_runner_form").submit()
        }
    </script>
    """+
    f"""
    <form id="code_runner_form" class="hidden" target="code_runner" action="/run_snippet" method="POST">
        <input id="sql_val" name="code" type="hidden" value="blank" />
        <input id="id" name="id" type="hidden" value="{id}" />
        <input type="submit">
    </form>
    """)

    try:
        df = server_request.app.from_cloud_pickle(f"{id}.pkl")
        page.add_header("Cached Results")
        page.add_datagrid(df)
    except:
        page.add_text("No cached results found. Run the SQL to see the results.")

    return page   

def run_snippet(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Snippet")

    code = server_request.params("code")
    id = server_request.params("id")

    page.add_codeeditor(code, language="sql")

    df = pd.read_sql_query(code, conn)

    server_request.app.to_cloud_pickle(df, f"{id}.pkl")

    page.add_datagrid(df)

    data = server_request.retrieve_dict(table_id="snippet", object_id=id)

    data["last_run"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["rows_returned"] = len(df)

    server_request.store_dict(table_id="snippet", object_id=id, value=data)

    return page

def all_snippets(server_request: cob.Request) -> cob.Page:
    page = cob.Page("All Snippets")
    page.add_header("All Snippets")
    
    username = server_request.get_username()

    snippets = server_request.list_objects(table_id="snippet")

    df = pd.DataFrame(snippets)

    action_buttons = [
        cob.Rowaction(label="View", url="/view_snippet?id={id}", open_in_new_window=False),
    ]

    page.add_pandastable(df, hide_fields=["id", "Query"], action_buttons=action_buttons)

    return page           
    
# APP CONFIGURATION
app = cob.App("SQL Snippets", use_built_in_auth=True)
app.register_function(all_snippets)
app.register_function(create_snippet, require_login=True)
app.register_function(update_snippet, require_login=True, show_in_navbar=False, footer_category=None)
app.register_function(delete_snippet, require_login=True, show_in_navbar=False, footer_category=None)
app.register_function(view_snippet, show_in_navbar=False, footer_category=None)
app.register_function(run_snippet, show_in_navbar=False, footer_category=None)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
# Deploy to PyCob Hosting using `python3 -m pycob.deploy` or use your own hosting provider.
    