# INITIALIZATION
import pandas as pd
import random
import pycob as cob
from elosports.elo import Elo

# GLOBAL VARIABLES
example_df = pd.DataFrame({'name': ['Alice', 'Bob', 'Charlie', 'Dave', 'Eve'],
                   'age': [25, 30, 35, 40, 45],
                   'gender': ['female', 'male', 'male', 'male', 'female']})

# Use of global variables works for this example, but is not recommended for production apps
eloLeague = Elo(k = 20)
players_df: pd.DataFrame
index_col: str
games = []

# PAGE FUNCTIONS
def input(server_request: cob.Request) -> cob.Page:
    page = cob.Page("DataFrame Comparison Game")
    page.add_header("Welcome to the DataFrame Comparison!")

    with page.add_card() as card:
        with card.add_form(action="/setup", method="POST") as form:
            form.add_text("Enter your data in JSON format")
            form.add_formtextarea("Data", "df_str", placeholder="", value=example_df.to_json(orient='records'))
            form.add_formtext("Index Column", "index_col", placeholder="Which column uniquely identifies the row?", value="name")
            
            form.add_text("Click on the button to start the playoffs")
            form.add_formsubmit("Start Playoffs")

    return page

def setup(server_request: cob.Request) -> cob.Page:
    page = cob.Page("DataFrame Comparison Game")

    # Get the dataframe from the form
    df_str = server_request.params('df_str')

    global index_col
    index_col = server_request.params('index_col')

    global players_df
    players_df = pd.read_json(df_str, orient='records')

    # Add the players to the Elo League
    global eloLeague
    for index, row in players_df.iterrows():
        if row[index_col] not in eloLeague.ratingDict:
            eloLeague.addPlayer(row[index_col])

    page.add_header("Data Saved")
    page.add_link("Start Playoffs", "/vs")

    return page


def row_to_df(row: pd.Series) -> pd.DataFrame:
    df = pd.DataFrame(row).reset_index()
    df.columns = ['column', 'value']
    return df

def vs(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Game")
    page.add_header("DataFrame Comparison")
    page.add_text("Select the winner of the following two rows")

    # Get the winner and loser from the query parameters
    winner = server_request.params('winner')
    loser = server_request.params('loser')

    # Update the Elo League
    if winner and loser:
        games.append({"winner": winner, "loser": loser})
        eloLeague.gameOver(winner=winner, loser=loser, winnerHome=False)

    global players_df
    global index_col

    # Randomly select 2 rows from the dataframe
    row1, row2 = random.sample(range(len(players_df)), 2)
    data1 = players_df.iloc[row1]
    data2 = players_df.iloc[row2]
    
    # Display the rows and a button to choose the winner
    with page.add_container(grid_columns=3) as container:
        with container.add_card() as card:
            card.add_header(str(data1[index_col]))
            card.add_pandastable(row_to_df(data1))
            card.add_link("Select as Winner", f"/vs?winner={data1[index_col]}&loser={data2[index_col]}")
        
        container.add_header("VS", classes="align-self-center text-center")

        with container.add_card() as card:
            card.add_header(str(data2[index_col]))
            card.add_pandastable(row_to_df(data2))
            card.add_link("Select as Winner", f"/vs?winner={data1[index_col]}&loser={data2[index_col]}")
    
    page.add_link("See Results", "/results")

    return page
        
def results(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Results")

    page.add_header("Rankings")
    rating_df = pd.DataFrame(pd.Series(eloLeague.ratingDict, name="Rating")).sort_values("Rating", ascending=False).reset_index()
    rating_df.columns = ['Player', 'Rating']

    page.add_pandastable(rating_df)

    page.add_header("Games")
    games_df = pd.DataFrame(games)
    page.add_pandastable(games_df)

    return page
    
# APP CONFIGURATION

app = cob.App("Compare and Rank", use_built_in_auth=False)

app.register_function(input, show_in_navbar=False)
app.register_function(setup, show_in_navbar=False, footer_category=None)
app.register_function(vs, show_in_navbar=False, footer_category=None)
app.register_function(results, show_in_navbar=True)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.