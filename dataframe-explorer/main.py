import pycob as cob
import pandas as pd
import plotly.express as px

app = cob.App("Data Frame Explorer")

# When we first ran the app we needed to load the data from the CSV file.
# df = pd.read_csv('vehicles.csv')
# We then saved the data to a cloud pickle file
# app.to_cloud_pickle(df, 'vehicles.pkl')

# Load the data
df = app.from_cloud_pickle('vehicles.pkl')

def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page()

    page.add_header('Data Frame Explorer')

    rows = server_request.params('rows')
    columns = server_request.params('columns')
    values = server_request.params('values')
    aggfunc = server_request.params('aggfunc')

    if rows == '':
        page.add_header("Sample Data", size=2)
        page.add_pandastable(df.head(5), action_buttons=[])

    with page.add_card() as card:
        card.add_header('Pivot Options')
        with card.add_form() as form:
            form.add_formselect('Rows', 'rows', df.columns, value="make" if rows == '' else rows)
            # form.add_formselect('Columns', 'columns', df.columns, value="model" if columns == '' else columns)
            form.add_formselect('Values', 'values', df.columns, 'comb08' if values == '' else values)
            form.add_formselect('Aggregation', 'aggfunc', ['mean', 'sum', 'count', 'min', 'max'], 'mean' if aggfunc == '' else aggfunc)
            form.add_formsubmit('Pivot!')

    if rows == '' or values == '':
        return page
    
    page.add_header("Pivot Table", size=2)

    page.add_code(f"pivot = df.pivot_table(\n\tindex=[{rows}], \n\tcolumns=[{columns}], \n\tvalues=[{values}], \n\taggfunc='{aggfunc}')\n.sort_values(ascending=False, by=values)\n.head(10)", header="Pivot Table")
    pivot = df.pivot_table(index=[rows], values=[values], aggfunc=aggfunc).sort_values(ascending=False, by=values).head(10)

    # Plotly Express bar chart of pivot
    page.add_code(f"px.bar(pivot.reset_index(), x={rows}, y={values}, color={values})", header="Plotly Express Bar Chart")
    page.add_plotlyfigure(px.bar(pivot.reset_index(), x=rows, y=values, color=values))

    # Pandas table of pivot
    page.add_code(f"page.add_pandastable(pivot.reset_index(), action_buttons=[])", header="Pandas Table")
    page.add_pandastable(pivot.reset_index(), action_buttons=[])

    return page


app.register_function(home, show_in_navbar=False)

server = app.run()

