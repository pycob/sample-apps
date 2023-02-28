# INITIALIZATION
from __future__ import annotations
import pycob as cob
import pandas as pd
import sqlite3 as db
from dataclasses import dataclass, asdict
from typing import List
import json

# HELPER FUNCTIONS
app = cob.App("Data Catalog", use_built_in_auth=True)

# Change this to a connection to your database
conn = db.connect('northwind.db', check_same_thread=False)

# DATA MODEL
# Python @dataclass is a new feature in Python 3.7 that allows you to define a class with a bunch of attributes and their types.
# It just makes it easier to define a class with a bunch of attributes without having to define the __init__ method.
@dataclass
class Dataset:
    id: str
    name: str
    readable_name: str
    description: str
    tables: list[Table]

    def to_dataframe(self):
        records = []

        for table in self.tables:
            row = {}
            row['dataset_id'] = self.id
            row['dataset_name'] = self.name
            row['dataset_description'] = self.description
            row['table_id'] = table.name
            row['table_description'] = table.description
            row['table_last_updated'] = table.last_updated
            row['table_type'] = table.type
            
            records.append(row)
        
        return pd.DataFrame(records)

@dataclass
class Table:
    name: str
    readable_name: str
    description: str
    last_updated: str
    type: str
    columns: list[Column]

    def to_dataframe(self):
        records = []

        for column in self.columns:
            row = {}
            row['column_name'] = column.name
            row['column_description'] = column.description
            row['column_data_type'] = column.data_type
            row['column_nullable'] = column.nullable
            row['column_min'] = column.min
            row['column_max'] = column.max
            row['column_mean'] = column.mean
            row['column_num_distinct'] = column.num_distinct
            row['column_num_null'] = column.num_null
            row['column_num_rows'] = column.num_rows
            
            records.append(row)
        
        return pd.DataFrame(records)

@dataclass
class Column:
    name: str
    readable_name: str
    description: str
    data_type: str
    nullable: bool
    min: float
    max: float
    mean: float
    num_distinct: int
    num_null: int
    num_rows: int

# PyCob has a built-in cloud pickle feature that allows you to save and load objects to the cloud.
try:
    print("Loading from cloud pickle")
    dset = app.from_cloud_pickle("northwind.pkl")
except Exception as e:
    print(f"Error getting cloud pickle {e}")
    dset = None

def update_dataset(params: dict):
    global dset

    # Parameters are of the form
    # /update?dataset_name=124124&table_name=Categories&table_type=Dimension&description=124124&column_CategoryID_readable_name=CategoryID&column_CategoryID_description=test1&column_CategoryName_readable_name=CategoryName&column_CategoryName_description=test2&column_Description_readable_name=Description&column_Description_description=test3&column_Picture_readable_name=Picture&column_Picture_description=test4

    dataset_name = params.get("dataset_name")
    table_name = params.get("table_name")
    table_type = params.get("table_type")
    description = params.get("description")


    # Get the columns
    columns = []
    for key in params.keys():
        if key.startswith("column_"):
            column_name = key.split("_")[1]
            column_description = params.get(key)
            column = Column(name=column_name, readable_name=column_name, description=column_description, data_type="", nullable=False, min=0, max=0, mean=0, num_distinct=0, num_null=0, num_rows=0)
            columns.append(column)


    app.to_cloud_pickle(dset, "northwind.pkl")

    print(f"Updated dataset {dset}")


# PAGE FUNCTIONS
def tables(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Tables")
    page.add_header("Tables")

    if dset is None:
        page.add_alert("Refresh required", "Error", "red")
        return page

    action_buttons = [
        cob.Rowaction(label="Edit", url="/edit?dataset_name={dataset_id}&table_name={table_id}", open_in_new_window=True),
        cob.Rowaction(label="View", url="/table_detail?dataset_name={dataset_id}&table_name={table_id}", open_in_new_window=True),
    ]

    
    page.add_pandastable(dset.to_dataframe(), action_buttons=action_buttons)
    
    return page
    
def table_detail(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Table Detail")
    table_name = server_request.params("table_name")
    
    if dset is None:
        page.add_alert("Refresh required", "Error", "red")
        return page

    table = list(filter(lambda x: x.name == table_name, dset.tables))
                
    page.add_header(f'Table Detail: {table_name}')

    if table is not None and len(table) > 0:
        table = table[0]

        page.add_header(f"Description: {table.description}", size=2)
        page.add_header(f"Last Updated: {table.last_updated}", size=2)
        page.add_header(f"Type: {table.type}", size=2)

    page.add_pandastable(table.to_dataframe(), action_buttons=[])

    page.add_link("Edit", f"/edit?dataset_name={dset.name}&table_name={table_name}")
    
    return page

def edit(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Edit")

    dataset_name = server_request.params("dataset_name")
    table_name = server_request.params("table_name")    

    if dset is None:
        page.add_alert("Refresh required", "Error", "red")
        return page

    with page.add_card() as card:
        card.add_header(f"Edit")
        card.add_header(f"{table_name}", size=2)

        with card.add_form(action="/update") as form:            
            form.add_formtext("Dataset Name", "dataset_name", value=dataset_name)
            form.add_formtext("Table Name", "table_name", value=table_name)

            table = list(filter(lambda x: x.name == table_name, dset.tables))
            if table is not None and len(table) > 0:
                form.add_formselect("Table Type", "table_type", options=["Fact", "Dimension"], value=table[0].type)
                form.add_formtextarea("Description", "description", placeholder="Table Description", value=table[0].description)

                for column in table[0].columns:
                    form.add_text(f"Column <code>{column.name}</code>")
                    with form.add_container(grid_columns=2) as container:
                        container.add_formtext(f"Readable Name", f"column_{column.name}_readable_name", value=column.readable_name)
                        container.add_formtextarea(f"Description", f"column_{column.name}_description", value=column.description, placeholder="Column Description")
            else:
                form.add_text("No columns found")


            form.add_formsubmit("Save")

    return page

def refresh(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Refresh")
    page.add_header("Refresh")

    refresh = server_request.params("refresh")

    if refresh != "true":
        with page.add_card() as card:
            card.add_header("Are You Sure?")
            card.add_text("Refresh the dataset from the source")
            card.add_alert("This will overwrite any changes you've made to the metadata", "Warning", "yellow")
            with card.add_form() as form:
                form.add_formhidden("refresh", "true")
                form.add_formsubmit("Refresh")
        
        return page
    
    # Get datasets
    # Since we're using SQLite, there's no concept of a dataset so we'll create a blank one
    global dset
    dset = Dataset(id='', name='Northwind', readable_name="Northwind", description='A sample dataset containing customer and order information', tables=[])
    
    # Get tables
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
    # page.add_pandastable(tables, action_buttons=[])

    # page.add_pandastable(columns, action_buttons=[])

    for table_name in tables['name']:
        # Get table metadata
        table = Table(name=table_name, readable_name=table_name, description='', last_updated='', type='', columns=[])
        
        # Get columns
        columns = pd.read_sql_query(f"PRAGMA table_info('{table_name}')", conn)
        
        # Get column metadata
        for label, col in columns.iterrows():
            column = Column(name=col['name'], readable_name=col['name'], description='', data_type='type', nullable='', min=None, max=None, mean=None, num_distinct=None, num_null=None, num_rows=None)
            table.columns.append(column)
        
        dset.tables.append(table)
        
    server_request.app.to_cloud_pickle(dset, 'northwind.pkl')
    page.add_link("Refreshed. See tables", "/tables")
    
    return page

def update(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Update")
    page.add_header("Update")

    update_dataset(server_request.params())

    page.add_link("Updated. See tables", "/tables")

    return page

# APP CONFIGURATION

app.register_function(tables, show_in_navbar=False, footer_category=None)
app.register_function(refresh, show_in_navbar=True, footer_category=None)
app.register_function(edit, show_in_navbar=False, footer_category=None, require_login=True)
app.register_function(table_detail, show_in_navbar=False, footer_category=None)
app.register_function(update, show_in_navbar=False, footer_category=None, require_login=True)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
