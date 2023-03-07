import pycob as cob
import pandas as pd
import plotly.express as px
import snowflake.connector

def get_secret(app: cob.App, secret_name: str) -> str:
    secrets = app.retrieve_dict(table_id="secrets", object_id="secrets")
    if secrets is None:
        raise ValueError("Secrets not found")
    
    if secret_name in secrets:
        return secrets[secret_name]
    else:
        raise ValueError(f"Secret {secret_name} not found")

def get_data(app: cob.App, tickers: list) -> pd.DataFrame:
    """Get the data for the tickers"""
    # Get the data
    conn = snowflake.connector.connect(
        user=get_secret(app, "SNOWFLAKE_USER"),
        password=get_secret(app, "SNOWFLAKE_PASSWORD"),
        account=get_secret(app, "SNOWFLAKE_ACCOUNT"),
        )
    cs = conn.cursor()

    cur = cs.execute("""
    SELECT "ticker", "date", "closeadj"
    FROM QUANDL.TYPED.SEP
    WHERE "ticker" in ('AAPL', 'MSFT', 'AMZN', 'GOOG', 'FB')
    ORDER BY "date"
    """)    

    data = cur.fetch_pandas_all()

    # Calculate the returns
    data["return"] = data.groupby("ticker")["closeadj"].pct_change()

    return data

# Page Functions
def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Portfolio Volatility")

    tickers_and_weights = {
        "AAPL": 0.2,
        "MSFT": 0.2,
        "AMZN": 0.2,
        "GOOG": 0.2,
        "FB": 0.2,        
    }

    # Get the data
    data = get_data(server_request.app, tickers_and_weights.keys())

    data['weighted_return'] = data['return'] * data['ticker'].map(tickers_and_weights)

    page.add_pandastable(data.head())

    # Calculate the portfolio volatility
    portfolio_volatility = data.groupby("date")["weighted_return"].std().mean() * 252 ** 0.5

    page.add_text(f"Portfolio Volatility: {portfolio_volatility}")

    # Plotly Histogram of the returns
    fig = px.histogram(data, x="return", nbins=100, title="Returns")
    page.add_plotlyfigure(fig)

    # Compute portfolio Value at Risk
    portfolio_var = data.groupby("date")["weighted_return"].quantile(0.025).mean() * 252 ** 0.5

    page.add_text(f"Portfolio Value at Risk: {portfolio_var}")

    # Compute portfolio Expected Shortfall
    portfolio_es = data.groupby("date")["weighted_return"].apply(lambda x: x[x < x.quantile(0.025)].mean()).mean() * 252 ** 0.5

    page.add_text(f"Portfolio Expected Shortfall: {portfolio_es}")

    # First Date
    first_date = data["date"].min()

    # Last Date
    last_date = data["date"].max()

    # Ticker volatility
    ticker_volatility = data.groupby("ticker")["return"].std() * 252 ** 0.5

    # Compute the total returns using the first date and last date and closeadj
    total_returns = data[data["date"] == last_date].set_index("ticker")["closeadj"] / data[data["date"] == first_date].set_index("ticker")["closeadj"] - 1

    # Join ticker_volatility and total_returns
    return_vs_volatility = total_returns.to_frame("total_return").join(ticker_volatility.to_frame("volatility"))

    page.add_pandastable(return_vs_volatility.reset_index())

    # Plotly Scatter of the returns vs volatility
    fig = px.scatter(return_vs_volatility.reset_index(), x="volatility", y="total_return", title="Returns vs Volatility", hover_name="ticker")
    page.add_plotlyfigure(fig)

    # Compute the correlation matrix
    correlation_matrix = data.pivot(index="date", columns="ticker", values="return").corr()

    page.add_pandastable(correlation_matrix.reset_index())

    return page

app = cob.App("Portfolio Volatility")

# Add the pages
app.register_function(home)

# Run the app
server = app.run()