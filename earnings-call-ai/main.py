import pycob as cob
import pandas as pd
import openai

app = cob.App("Earnings Call AI")

openai.api_key = app.retrieve_secret("OPENAI_API_KEY") # Use your own OpenAI API key here

# TODO: This is a placeholder for you to add your own Earnings Call Transcript API
def get_transcript(ticker: str) -> str:
    with open(f"./transcripts/{ticker}.txt", "r") as transcript_file:
        transcript = transcript_file.read()

    return transcript

def send_to_chatgpt(message_log) -> str:
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=message_log, max_tokens=500, stop=None, temperature=0.7)

    # Find the first response from the chatbot that has text in it (some responses may not have text)
    for choice in response.choices:
        if "text" in choice:
            return choice.text

    # If no response with text is found, return the first response's content (which may be empty)
    return response.choices[0].message.content

def count_tokens(s: str) -> int:
    return len(s) / 4.0

# OpenAI has a token limit so we need to break up the transcript into segments
def break_up_transcript(ticker: str, max_tokens: int = 1500) -> list:
    split_transcript = []

    current_group_token_count = 0
    current_group_str = ""

    for line in get_transcript(ticker).splitlines():
        line_tokens = count_tokens(line)

        if current_group_token_count + line_tokens < max_tokens:
            current_group_str += line
            current_group_token_count += line_tokens
        else:
            split_transcript.append(current_group_str)
            current_group_str = line
            current_group_token_count = line_tokens

    return split_transcript

def summarize_segment(segment: str, user_question: str) -> str:
    message_log = [
        {"role": "system", "content": f""""
        You are an Earnings call transcript summarizer. The user will give you sections of an earnings call transcript and you will evaluate each section to see if it has anything to say about the following question:
        {user_question}
        If the section does not contain any relevant information, you may respond with "N/A"
        """}]

    message_log.append({"role": "user", "content": segment})

    return send_to_chatgpt(message_log)


def question(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Question")

    with page.add_card() as card:
        with card.add_form(action="/summarize") as form:
            form.add_formtext("Question", "question", placeholder="What is this company doing to reduce costs?", value="What is this company doing to reduce costs?")
            form.add_formselect("Ticker", "ticker", options=["MDB", "SNOW", "KR"], value="MDB")
            form.add_formsubmit("Submit")

    return page

def summarize(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Summaries")

    question = server_request.params("question")
    ticker = server_request.params("ticker")

    if question == "" or ticker == "":
        page.add_alert("Please enter a question and select a ticker", "red")
        return page

    page.add_header(ticker)
    page.add_header(question, size=3)
    page.add_text(f"{ticker} Earnings Call Transcript")

    segment_summaries = []

    for segment in break_up_transcript(ticker):
        segment_summaries.append({
            "segment": segment,
            "summary": summarize_segment(segment, question),
        })

    df = pd.DataFrame(segment_summaries)

    # Filter out "summary" that begins with "N/A" or "segment" that is just whitespace
    df = df[ (df["summary"].str.contains("N/A") == False) & (df["segment"].str.isspace() == False)]

    page.add_pandastable(df)

    return page

app.register_function(question)
app.register_function(summarize)

server = app.run()