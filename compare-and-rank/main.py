# INITIALIZATION
import pandas as pd
import random
import pycob as cob

# GLOBAL VARIABLES
df = pd.DataFrame({'name': ['Alice', 'Bob', 'Charlie', 'Dave', 'Eve'],
                   'age': [25, 30, 35, 40, 45],
                   'gender': ['female', 'male', 'male', 'male', 'female']})

# PAGE FUNCTIONS
def index(server_request: cob.Request) -> cob.Page:
    page = cob.Page("DataFrame Comparison Game")
    page.add_header("Welcome to the DataFrame Comparison Game!")
    page.add_text("Click on the button to start the game")
    page.add_link("Start Game", "/game")
    return page

def game(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Game")
    page.add_header("DataFrame Comparison Game")
    
    # Randomly select 2 rows from the dataframe
    row1, row2 = random.sample(range(len(df)), 2)
    data1 = df.iloc[row1]
    data2 = df.iloc[row2]
    
    # Display the rows and a button to choose the winner
    with page.add_container(classes="row"):
        with page.add_container(classes="col-md-6") as container:
            container.add_header("Row 1")
            container.add_text(str(data1))
            container.add_link("Select as Winner", f"/winner?winner={row1}")
        with page.add_container(classes="col-md-6") as container:
            container.add_header("Row 2")
            container.add_text(str(data2))
            container.add_link("Select as Winner", f"/winner?winner={row2}")
    
    return page
    
def winner(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Winner")
    page.add_header("DataFrame Comparison Game")
    
    winner = int(server_request.params('winner'))
    
    # Record the winner in a separate dataframe
    if 'winners' not in server_request.session:
        server_request.session['winners'] = pd.DataFrame(columns=['name', 'age', 'gender', 'winner'])
    winners_df = server_request.session['winners']
    winners_df = winners_df.append(df.iloc[winner].append(pd.Series({'winner': winner})), ignore_index=True)
    server_request.session['winners'] = winners_df
    
    page.add_text(f"You selected {df.iloc[winner]['name']} as the winner!")
    page.add_button("Play Again", "/game")
    page.add_button("View Results", "/results")
    
    return page
    
def results(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Results")
    page.add_header("DataFrame Comparison Game")
    
    # Display the winners dataframe
    if 'winners' in server_request.session:
        winners_df = server_request.session['winners']
        with page.add_container(classes="row"):
            with page.add_container(classes="col-md-8 offset-md-2") as container:
                container.add_header("Winners")
                container.add_dataframe(winners_df)
    else:
        page.add_text("No winners yet!")
    
    page.add_button("Play Again", "/game")
    page.add_button("Home", "/")
    
    return page
    
# APP CONFIGURATION

app = cob.App("DataFrame Comparison Game", use_built_in_auth=False)

app.add_page('/', 'index', index, show_in_navbar=True, footer_category=None)
app.add_page('/game', 'game', game, show_in_navbar=False, footer_category=None)
app.add_page('/winner', 'winner', winner, show_in_navbar=False, footer_category=None)
app.add_page('/results', 'results', results, show_in_navbar=True, footer_category=None)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.