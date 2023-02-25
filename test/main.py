import pycob as cob
import plotly.express as px

def data_frames(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Data Frames in PyCob")

    page.add_header("Data Frames in PyCob")

    page.add_text("This page demonstrates how to use data frames in PyCob.")

    page.add_text("Let's start with a data frame from the plotly library:")

    page.add_code("""import plotly.express as px

df = px.data.gapminder().query("country=='Canada'")""")

    df = px.data.gapminder().query("country=='Canada'")

    page.add_text("Now we can add the data frame to the page as a native table:")
    page.add_code("""page.add_pandastable(df, action_buttons=[])""")

    page.add_pandastable(df, action_buttons=[])

    page.add_text("Or we can add the data frame to the page as a datagrid:")
    page.add_code("""page.add_datagrid(df, action_buttons=[])""")
    page.add_datagrid(df, action_buttons=[])


    page.add_text("Or we can add the data frame to the page as a plotly figure:")
    page.add_code("""fig = px.line(df, x="year", y="lifeExp", title='Life expectancy in Canada')
page.add_plotlyfigure(fig)""")

    fig1 = px.line(df, x="year", y="lifeExp", title='Life expectancy in Canada')
    page.add_plotlyfigure(fig1)

    page.add_text("This is an example of a bar chart:")
    page.add_code("""fig = px.bar(df, x='year', y='pop')
page.add_plotlyfigure(fig)""")

    fig2 = px.bar(df, x='year', y='pop')
    page.add_plotlyfigure(fig2)

    return page

app = cob.App("Data Frames", use_built_in_auth=True)

app.register_function(data_frames, show_in_navbar=False)

server = app.run()