# INITIALIZATION
import pycob as cob
import plotly.express as px

app = cob.App("PyPi Analytics", use_built_in_auth=False)
pypi_projects_by_month = app.from_cloud_pickle('pypi_projects_by_month.pkl')
pypi_projects_by_month = app.from_cloud_pickle('pypi_projects_by_month.pkl')

# PAGE FUNCTIONS
def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page("PyPi Analytics")
    page.add_header("PyPi Analytics")
    page.add_text("PyPi analytics enables Python engineers to identify usage trends with Python packages as an input for picking the right package")
    page.add_link("See the source code for this app", "https://github.com/pycob/sample-apps/blob/main/pypi-analytics/main.py")
    page.add_text("")
    
    top_projects = pypi_projects_by_month.groupby('pypi_project').sum().sort_values('avg_downloads_per_day', ascending=False).reset_index().head(50)

    action_buttons = [
        cob.Rowaction(label="Analytics", url="/project_detail?project_name={pypi_project}", open_in_new_window=True),
        cob.Rowaction(label="Project", url="https://pypi.org/project/{pypi_project}", open_in_new_window=True),
    ]
    
    with page.add_card() as card:
        card.add_header("Analyze a Project")
        with card.add_form(action="/project_detail") as form:
            form.add_formtext(name="project_name", label="Project Name", placeholder="Enter a project name")
            form.add_formsubmit("Analyze")

    page.add_text("")

    page.add_header("Top 50 Projects by Downloads", size=4)
    page.add_pandastable(top_projects, action_buttons=action_buttons)
    
    return page

def project_detail(server_request: cob.Request) -> cob.Page:
    page = cob.Page("PyPi Analytics")
    
    project_name = server_request.params('project_name')
    compare_to = server_request.params('compare_to')
    subtitle = server_request.params('subtitle')

    page.add_header(f"PyPi Analytics for <code>{project_name}</code>")

    if not subtitle:
        with page.add_form(action="/project_detail") as form:
            form.add_formhidden(name="project_name", value=project_name)
            form.add_formhidden(name="compare_to", value=compare_to)
            form.add_formtext(name="subtitle", label="Subtitle", placeholder="Enter a subtitle")
            form.add_formsubmit("Update Subtitle")
    else:
        page.add_header(f"{subtitle}", size=4)
    
    if compare_to:
        project_detail = pypi_projects_by_month[pypi_projects_by_month['pypi_project'].isin([project_name, compare_to])]
    else:
        project_detail = pypi_projects_by_month[pypi_projects_by_month['pypi_project'] == project_name]
    
    fig = px.line(project_detail.sort_values(["month", "pypi_project"]), x="month", y="avg_downloads_per_day", line_group="pypi_project", color="pypi_project")

    page.add_plotlyfigure(fig)
    
    if not compare_to:
        with page.add_card() as card:
            with card.add_form(action="/project_detail") as form:
                form.add_formhidden(name="project_name", value=project_name)
                form.add_formtext(label="Compare To", name="compare_to", placeholder="Enter a project name")
                form.add_formsubmit("Analyze")

    return page    
    
# APP CONFIGURATION

app.register_function(home, show_in_navbar=False)
app.register_function(project_detail, show_in_navbar=False)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
