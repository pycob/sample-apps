# INITIALIZATION
from __future__ import annotations
import pycob as cob
import pandas as pd
import sqlite3 as db
from dataclasses import dataclass, asdict
from typing import List
from datetime import datetime
import json

# HELPER FUNCTIONS
app = cob.App("Data Catalog", use_built_in_auth=True)

# Change this to a connection to your database
conn = db.connect('northwind.db', check_same_thread=False)

# DATA MODEL
# Python @dataclass is a new feature in Python 3.7 that allows you to define a class with a bunch of attributes and their types.
# It just makes it easier to define a class with a bunch of attributes without having to define the __init__ method.
@dataclass
class Datasets:
    datasets: list[Dataset]

    def to_dataframe(self) -> pd.DataFrame:
        records = []

        for dataset in self.datasets:
            records.extend(dataset.to_dataframe().to_dict('records'))
        
        return pd.DataFrame(records)

    def get_dataset_index(self, dataset_name: str) -> int:
        for i in range(len(self.datasets)):
            if self.datasets[i].name == dataset_name:
                return i

        return -1

@dataclass
class Dataset:
    name: str
    readable_name: str
    description: str
    tables: list[Table]

    def to_dataframe(self) -> pd.DataFrame:
        records = []

        for table in self.tables:
            row = {}
            row['dataset_name'] = self.name
            row['dataset_readable_name'] = self.readable_name
            row['dataset_description'] = self.description
            row['table_name'] = table.name
            row['table_readable_name'] = table.readable_name
            row['table_description'] = table.description
            row['row_count'] = table.row_count
            row['table_last_updated'] = table.last_updated.strftime("%Y-%m-%d %H:%M")
            row['table_type'] = table.type
            
            records.append(row)
        
        return pd.DataFrame(records)

    def get_table_index(self, table_name: str) -> int:
        for i in range(len(self.tables)):
            if self.tables[i].name == table_name:
                return i

        return -1

@dataclass
class Table:
    name: str
    readable_name: str
    description: str
    last_updated: datetime
    type: str
    columns: list[Column]
    sample: pd.DataFrame
    row_count: int

    def to_dataframe(self) -> pd.DataFrame:
        records = []

        for column in self.columns:
            row = {}
            row['column_name'] = column.name
            row['column_readable_name'] = column.readable_name
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
dsets: Datasets
try:
    print("Loading from cloud pickle")
    dsets = app.from_cloud_pickle("northwind.pkl")
except Exception as e:
    print(f"Error getting cloud pickle {e}")
    dsets = None

def to_readable_name(name: str) -> str:
    import re

    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

    return name.replace("_", " ").title()

def update_dataset(params: dict) -> None:
    global dsets

    # Parameters are of the form
    # /update?dataset_name=northwind&table_name=Categories&dataset_readable_name=Northwind&table_readable_name=Categories&table_type=Dimension&table_description=Description&column_CategoryID_readable_name=Category+ID&column_CategoryID_description=test+1&column_CategoryName_readable_name=Category+Name&column_CategoryName_description=test+2&column_Description_readable_name=Description&column_Description_description=test+3&column_Picture_readable_name=Picture&column_Picture_description=test+4

    dataset_name = params.get("dataset_name")
    dataset_readable_name = params.get("dataset_readable_name")
    table_name = params.get("table_name")
    table_readable_name = params.get("table_readable_name")
    table_type = params.get("table_type")
    table_description = params.get("table_description")

    dataset_index = dsets.get_dataset_index(dataset_name)

    if dataset_index == -1:
        return None
    
    dset = dsets.datasets[dataset_index]

    table_index = dset.get_table_index(table_name)

    if table_index == -1:
        return None
    
    table = dset.tables[table_index]

    # Update the table
    table.readable_name = table_readable_name
    table.description = table_description
    table.type = table_type

    # Update the dataset
    dset.readable_name = dataset_readable_name

    # Update the columns

    for column in table.columns:
        column.readable_name = params.get(f"column_{column.name}_readable_name")
        column.description = params.get(f"column_{column.name}_description")                    

    app.to_cloud_pickle(dsets, "northwind.pkl")


# PAGE FUNCTIONS
def tables(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Tables")
    page.add_header("Tables")

    if dsets is None:
        page.add_alert("Refresh required", "Error", "red")
        return page

    action_buttons = [
        cob.Rowaction(label="View", url="/table_detail?dataset_name={dataset_name}&table_name={table_name}", open_in_new_window=False),
    ]

    
    page.add_datagrid(dsets.to_dataframe(), action_buttons=action_buttons)
    
    return page
    
def table_detail(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Table Detail")
    dataset_name = server_request.params("dataset_name")
    table_name = server_request.params("table_name")
    
    if dsets is None:
        page.add_alert("Refresh required", "Error", "red")
        return page
    
    page.add_header(f'Table Detail: {dataset_name} - {table_name}')

    with page.add_form(action="/edit") as form:
        form.add_formhidden("dataset_name", dataset_name)
        form.add_formhidden("table_name", table_name)
        form.add_formsubmit("Edit")

    dataset_index = dsets.get_dataset_index(dataset_name)

    if dataset_index is None or dataset_index < 0:
        page.add_alert("Dataset not found", "Error", "red")
        return page

    dset = dsets.datasets[dataset_index]

    table_index = dset.get_table_index(table_name)

    if table_index is None or table_index < 0:
        page.add_alert("Table not found", "Error", "red")
        return page

    table_df = dset.to_dataframe().iloc[table_index,:].reset_index()
    table = dset.tables[table_index]

    table_df.columns = ["Field", "Value"]
    # Make the field names more readable
    table_df['Field'] = table_df['Field'].map(lambda x: x.replace("_", " ").title())

    page.add_pandastable(table_df)

    page.add_header("Columns", size=2)
    page.add_pandastable(table.to_dataframe())

    page.add_header("Sample Data", size=2)
    page.add_pandastable(table.sample)

    page.add_link("Edit Table Metadata", f"/edit?dataset_name={dset.name}&table_name={table_name}")
    
    return page

def edit(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Edit")

    dataset_name = server_request.params("dataset_name")
    table_name = server_request.params("table_name")    

    dataset_index = dsets.get_dataset_index(dataset_name)

    if dataset_index is None or dataset_index < 0:
        page.add_alert("Dataset not found", "Error", "red")
        return page

    dset = dsets.datasets[dataset_index]

    table_index = dset.get_table_index(table_name)

    if table_index is None or table_index < 0:
        page.add_alert("Table not found", "Error", "red")
        return page

    table = dset.tables[table_index]

    with page.add_card() as card:
        card.add_header(f"Edit")
        card.add_header(f"{dset.readable_name} - {table.readable_name}", size=2)

        with card.add_form(action="/update") as form:
            form.add_formhidden("dataset_name", value=dataset_name)
            form.add_formhidden("table_name", value=table_name)
            form.add_formtext("Dataset Readable Name", "dataset_readable_name", value=dset.readable_name)
            form.add_formtext("Table Readable Name", "table_readable_name", value=table.readable_name)

            table = dset.tables[table_index]

            form.add_formselect("Table Type", "table_type", options=["Fact", "Dimension"], value=table.type)
            form.add_formtextarea("Table Description", "table_description", placeholder="Table Description", value=table.description)

            for column in table.columns:
                form.add_text(f"Column <code>{column.name}</code>")
                with form.add_container(grid_columns=2) as container:
                    container.add_formtext(f"Readable Name", f"column_{column.name}_readable_name", value=column.readable_name)
                    container.add_formtextarea(f"Description", f"column_{column.name}_description", value=column.description, placeholder="Column Description")


            form.add_formsubmit("Save")

    return page

# TODO: You can customize this to your needs
# This is a sample for SQLite and will need to be updated for your database
# The rest of the app can stay the same. The only thing that this function needs to do
# is update the global dsets variable, which is a Datasets object
#
# As an alternative, you can also create the dsets object in a Jupyter Notebook
# and use app.to_cloud_pickle() to save it to PyCob Cloud.
# The app uses app.from_cloud_pickle() to load the dsets object from PyCob Cloud.
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
    # Since we're using SQLite, there's no concept of a dataset so we'll create a placeholder one called "northwind"
    global dsets
    dsets = Datasets(datasets=[])

    dset = Dataset(name='northwind', readable_name=to_readable_name("northwind"), description='A sample dataset containing customer and order information', tables=[])
    
    # Get tables
    tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table'", conn)
    # page.add_pandastable(tables)

    for table_name in tables['name']:
        # Get table metadata
        
        # Get columns
        columns = pd.read_sql_query(f"PRAGMA table_info('{table_name}')", conn)
        
        # Remove the "Picture" or "Photo" column from the sample data
        columns = columns[columns['name'] != 'Picture']
        columns = columns[columns['name'] != 'Photo']

        page.add_pandastable(columns)
        
        sample = pd.read_sql_query(f"SELECT * FROM \"{table_name}\" LIMIT 10", conn)

        # Remove the "Picture" column from the sample data if it exists
        if 'Picture' in sample.columns:
            sample = sample.drop(columns=['Picture'])
        if 'Photo' in sample.columns:
            sample = sample.drop(columns=['Photo'])

        row_count = pd.read_sql_query(f"SELECT COUNT(*) as cnt FROM \"{table_name}\"", conn)['cnt'][0]

        table = Table(name=table_name, readable_name=to_readable_name(table_name), description='', last_updated=datetime.now(), type='', columns=[], sample=sample, row_count=row_count)

        # Get column metadata
        for label, col in columns.iterrows():
            # Get min, max, mean, num_distinct, num_null, num_rows
            stats_df = pd.read_sql_query(f"SELECT MIN({col['name']}) as min, MAX({col['name']}) as max, AVG({col['name']}) as mean, COUNT(DISTINCT {col['name']}) as num_distinct, COUNT({col['name']}) as num_rows, COUNT({col['name']} IS NULL) as num_null, COUNT(*) as num_rows FROM \"{table_name}\"", conn)

            try:
                stats = stats_df.iloc[0].to_dict()

                column = Column(name=col['name'], readable_name=to_readable_name(col['name']), description='', data_type=col['type'], nullable='Nullable' if col['notnull']==0 else 'Not Nullable', min=stats['min'], max=stats['max'], mean=stats['mean'], num_distinct=stats['num_distinct'], num_null=stats['num_null'], num_rows=stats['num_rows'])
            except:
                column = Column(name=col['name'], readable_name=to_readable_name(col['name']), description='', data_type=col['type'], nullable='Nullable' if col['notnull']==0 else 'Not Nullable', min=None, max=None, mean=None, num_distinct=None, num_null=None, num_rows=None)

            table.columns.append(column)
        
        dset.tables.append(table)

    dsets.datasets.append(dset)

    server_request.app.to_cloud_pickle(dsets, 'northwind.pkl')
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
