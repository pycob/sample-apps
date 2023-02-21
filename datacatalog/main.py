# INITIALIZATION: Do not delete this comment
import pycob as cob



# PAGE FUNCTIONS: Do not delete this comment
def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Home")
    page.add_header("Data Catalog")
    
    tables = server_request.app.from_cloud_pickle('tables.pkl')
    
    action_buttons = [
        cob.Rowaction(label="Table Detail", url="/table_detail?table_name={table_name}", open_in_new_window=True),
    ]
    
    page.add_datagrid(tables, action_buttons=action_buttons)
    
    return page
    
def table_detail(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Table Detail")
    table_name = server_request.params("table_name")
    
    page.add_header(f'Table Detail: {table_name}')
    
    columns = server_request.app.from_cloud_pickle('columns.pkl')
    
    filtered_columns = columns[columns['table_name'] == table_name]
    
    page.add_datagrid(filtered_columns, action_buttons=[])
    
    return page
    
# APP CONFIGURATION: Do not delete this comment. 
# Temporary Restriction: Do not edit the code below this comment.
app = cob.App("Data Catalog", use_built_in_auth=False)

app.add_page('/', 'home', home, show_in_navbar=True, footer_category=None)
app.add_page('/table_detail', 'table_detail', table_detail, show_in_navbar=True, footer_category=None)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
