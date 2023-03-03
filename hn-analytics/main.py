# INITIALIZATION
import pycob as cob
import plotly.express as px

app = cob.App("HN Analytics", use_built_in_auth=False)

# DATA
# We are getting the data from a pickle file that was created in a notebook. It is basically just the result of running this query:
# %%bigquery hn_data --project pycob-prod
# SELECT *
# FROM (
#   SELECT * 
#   FROM `bigquery-public-data.hacker_news.full`
#   TABLESAMPLE SYSTEM (1 PERCENT)
# )
# WHERE score is not null and score > 0
# AND type = 'story'
# ORDER BY score desc
hn_data = app.from_cloud_pickle('hn_data.pkl')
hn_data['pacific_hour'] = hn_data['timestamp'].dt.tz_convert('America/Los_Angeles').dt.hour
hn_data['pacific_day_of_week'] = hn_data['timestamp'].dt.tz_convert('America/Los_Angeles').dt.day_of_week
hn_data['score'] = hn_data['score'].astype('int64')

# PAGE FUNCTIONS
def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page("HN Analytics")
    page.add_header("Hacker News Analytics")
    page.add_text("HN Analytics enables you to find the best time (<code>America/Los_Angeles</code>) to post on Hacker News.")
    page.add_link("See the source code for this app", "https://github.com/pycob/sample-apps/blob/main/hn-analytics/main.py")
    page.add_text("")
    
    title_filter = server_request.params('title_filter')

    if title_filter is None or title_filter == "":
        df = hn_data
    else:
        df = hn_data[hn_data['title'].str.contains(title_filter, case=False, na=False)]

    pivot = df.pivot_table(index=['pacific_hour'], columns=['pacific_day_of_week'], values=['score'], aggfunc='count')
    pivot.columns = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    fig1 = px.imshow(pivot, title="<b>Posts By Hour and Day of Week</b>", labels=dict(x="Day of Week", y="Hour of Day", color="Number of Posts"))
    
    pivot_by_day = df.pivot_table(index=['pacific_day_of_week'], values=['score'], aggfunc=['mean', 'median'])
    pivot_by_day.index = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    pivot_by_day.columns = ['mean', 'median']
    fig2 = px.bar(pivot_by_day, barmode='group', title="<b>Mean and Median HN Score By Day of Week</b>")

    fig3 = px.histogram(df, x="score", log_y=True, title="<b>Histogram of HN Scores on Log Scale<b>")

    probability_of_viral = df.pivot_table(index=['pacific_hour'], columns=['pacific_day_of_week'], values=['score'], aggfunc=lambda x: len(x[x > 20]) / len(x))
    probability_of_viral.columns = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    fig4 = px.imshow(probability_of_viral, title="<b>Probability that a Post Has a Score > 20</b>")

    with page.add_container(grid_columns=2) as container:
        container.add_plotlyfigure(fig1)
        container.add_plotlyfigure(fig2)

    with page.add_container(grid_columns=2) as container:
        container.add_plotlyfigure(fig3)
        container.add_plotlyfigure(fig4)

    with page.add_card() as card:
        with card.add_form() as form:
            form.add_formtext("Filter the Story Title", "title_filter", "text", value=title_filter)
            form.add_formsubmit("Filter")

    return page

    
# APP CONFIGURATION
app.register_function(home, show_in_navbar=False)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
