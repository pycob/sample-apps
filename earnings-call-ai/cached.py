import pycob as cob
import pandas as pd

app = cob.App("Earnings Call AI")

segment_summaries = app.from_cloud_pickle("segment_summaries2.pkl")

def summaries(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Summaries")

    user_question = "What does this company say about how it's dealing with inflation and/or the economy?"
    page.add_header("MDB")
    page.add_header(user_question, size=3)
    page.add_text("MongoDB (MDB) Q4 2023 Earnings Call Transcript")

    df = pd.DataFrame(segment_summaries)

    # Filter out "summary" that begins with "N/A"
    df = df[df["summary"].str.contains("N/A") == False]

    # Filter out "segment" that is just whitespace
    df = df[df["segment"].str.isspace() == False]

    page.add_pandastable(df)

    return page

app.register_function(summaries)

server = app.run()