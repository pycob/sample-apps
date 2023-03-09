import pycob as cob
import pandas as pd
import plotly.express as px
import snowflake.connector

app = cob.App("Portfolio Volatility")

initial_tickers_and_weights = {
    "AAPL": 0.2,
    "MSFT": 0.2,
    "AMZN": 0.2,
    "GOOG": 0.2,
    "FB": 0.2,
}

def get_data(app: cob.App, tickers: list) -> pd.DataFrame:
    """Get the data for the tickers"""
    # Get the data
    conn = snowflake.connector.connect(
        user=app.retrieve_secret("SNOWFLAKE_USER"),
        password=app.retrieve_secret("SNOWFLAKE_PASSWORD"),
        account=app.retrieve_secret("SNOWFLAKE_ACCOUNT"),
        )
    cs = conn.cursor()

    # Load data for tickers
    cur = cs.execute(f"""
    SELECT "ticker", "date", "closeadj"
    FROM QUANDL.TYPED.SEP
    WHERE "ticker" in ({', '.join([f"'{ticker}'" for ticker in tickers])})
    ORDER BY "date"
    """)

    data = cur.fetch_pandas_all()

    return data

def update_tickers_and_weights(before: dict, ticker: str, weight: float) -> dict:
    after = before.copy()
    after[ticker] = weight

    # Normalize the weights
    total_weight = sum(after.values())

    for ticker in after:
        after[ticker] = after[ticker] / total_weight

    return after

def compute_daily_returns(data: pd.DataFrame) -> pd.DataFrame:
    data["return"] = data.groupby("ticker")["closeadj"].pct_change()

    return data

def compute_portfolio_returns(data: pd.DataFrame, tickers_and_weights: dict) -> pd.DataFrame:
    data['weighted_return'] = data['return'] * data['ticker'].map(tickers_and_weights)

    portfolio_return = data.groupby("date")["weighted_return"].sum()

    return portfolio_return

def get_return_vs_volatility(data: pd.DataFrame) -> pd.DataFrame:
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

    return return_vs_volatility

# Page Functions
def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Portfolio Volatility")

    ticker = server_request.params("ticker")
    weight = server_request.params("weight")

    if ticker != "" and weight != "":
        # Update the tickers and weights
        tickers_and_weights = update_tickers_and_weights(initial_tickers_and_weights, ticker, float(weight))
    else:
        tickers_and_weights = initial_tickers_and_weights

    # Get the data
    data = get_data(server_request.app, tickers_and_weights.keys())
    data = compute_daily_returns(data)
    portfolio_return = compute_portfolio_returns(data, tickers_and_weights)

    # Calculate the portfolio volatility
    portfolio_volatility = portfolio_return.std() * 252 ** 0.5

    # Compute the portfolio cumulative return
    portfolio_cumulative_return = (1+portfolio_return).cumprod()-1

    # Compute portfolio Value at Risk
    tail_cutoff = data.groupby("date")["weighted_return"].sum().quantile(0.025)
    portfolio_var = tail_cutoff * 252 ** 0.5

    # Compute portfolio Expected Shortfall
    portfolio_es = portfolio_return[portfolio_return < tail_cutoff].mean() * 252 ** 0.5

    # Plotly Histogram of the returns
    fig1 = px.histogram(portfolio_return, x="weighted_return", nbins=100, title="<b>Daily Portfolio Return Distribution<b>")
    fig1.layout.xaxis.tickformat = ',.0%'
    
    # Plotly Cumulative Return
    fig2 = px.line(pd.DataFrame(portfolio_cumulative_return), x=portfolio_cumulative_return.index, y="weighted_return", title="<b>Portfolio Cumulative Return</b>")
    fig2.layout.yaxis.tickformat = ',.0%'

    # Plotly Scatter of the returns vs volatility
    return_vs_volatility = get_return_vs_volatility(data)
    fig3 = px.scatter(return_vs_volatility.reset_index(), x="volatility", y="total_return", title="<b>Returns vs Volatility</b>", text="ticker")
    fig3.update_traces(textposition="bottom right")

    # Compute the correlation matrix
    correlation_matrix = data.pivot(index="date", columns="ticker", values="return").corr()

    # Plotly Heatmap of the correlation matrix
    fig4 = px.imshow(correlation_matrix, title="<b>Correlation Matrix</b>")

    with page.add_container(grid_columns=3) as risk_stats:
        with risk_stats.add_card() as card:
            card.add_header(f"{portfolio_volatility:.2%}")
            card.add_text("Portfolio Volatility")
        
        with risk_stats.add_card() as card:
            card.add_header(f"{portfolio_var:.2%}")
            card.add_text("Portfolio Value at Risk")

        with risk_stats.add_card() as card:
            card.add_header(f"{portfolio_es:.2%}")
            card.add_text("Portfolio Expected Shortfall")

    with page.add_container(grid_columns=2) as plots1:
        plots1.add_plotlyfigure(fig1)
        plots1.add_plotlyfigure(fig2)
    
    with page.add_container(grid_columns=2) as plots2:
        plots2.add_plotlyfigure(fig3)
        plots2.add_plotlyfigure(fig4)

    with page.add_card() as card:
        card.add_header("Add Ticker")
        card.add_text("The rest of the portfolio will be rebalanced to maintain the relative weights.")
        with card.add_form() as form:
            form.add_formtext("Ticker", "ticker", "AAPL")
            form.add_formtext("Weight", "weight", "0.2")
            form.add_formsubmit("Add Ticker")

    return page


# Add the pages
app.register_function(home)

# Run the app
server = app.run()