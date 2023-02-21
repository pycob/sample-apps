# INITIALIZATION
import pycob as cob
import pandas as pd
import re

def construct_ai_prompt(string1, output1, string2, output2, string3, output3):
    # The prompt will be of the form:
    # Write a single Python regular expression pattern that will extract the following substrings from strings:
    # "hello" from "https://yo.hello.com"
    # "hi" from "https://xyz.hi.com"
    # Use the most general pattern possible and return the result as runnable Python code.

    prompt = "Write a single Python regular expression pattern that will extract the following substrings from strings:\n"

    if string1 != "":
        prompt += f'"{output1}" from "{string1}"\n'
    if string2 != "":
        prompt += f'"{output2}" from "{string2}"\n'
    if string3 != "":
        prompt += f'"{output3}" from "{string3}"\n'

    prompt += "Use the most general pattern possible and return the result as runnable Python code."

    return prompt

def extract_pattern_from_ai_response(response):
    lines = response.split("\n")

    for line in lines:
        if "pattern = " in line:
            return line.split("pattern = ")[1]
        
    return "No pattern found"


# PAGE FUNCTIONS
def gen_regex(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Gen Regex")
    page.add_header("Python Regex from AI")

    string1 = server_request.params("string1")
    output1 = server_request.params("output1")

    string2 = server_request.params("string2")
    output2 = server_request.params("output2")

    string3 = server_request.params("string3")
    output3 = server_request.params("output3")

    if string1 != "":
        prompt = construct_ai_prompt(string1, output1, string2, output2, string3, output3)
        
        response = server_request.app.generate_text_from_ai(prompt)
        
        pattern_str = extract_pattern_from_ai_response(response)
        
        if pattern_str == "No pattern found":
            page.add_text("No pattern found. Please try again.")
            
        pattern = eval(pattern_str)
        
        page.add_code(pattern_str, header="Pattern", prefix="")
        
        sample_usage = f"""
    import re
    pattern = {pattern_str}
    re.compile(pattern).match("{string1}").group(1)
    """
        
        page.add_code(sample_usage, header="Sample Usage", prefix="")

        actual_output = []

        for string in [string1, string2, string3]:
            if string == "":
                actual_output.append("")
            else:
                try:
                    actual_output.append(re.compile(pattern).match(string).group(1))
                except:
                    actual_output.append("Error: No match found.")
        
        data = {
            "input": [string1, string2, string3],
            "desired_output": [output1, output2, output3],
            "actual_output": actual_output
        }
        
        df = pd.DataFrame(data)
        
        page.add_header("Did the AI Get it Right?")
        page.add_pandastable(df)


    return page
    
def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Home")
    
    with page.add_card() as card:
        card.add_header("AI Regex Generator")
        card.add_text("Provide 3 examples of strings and the desired output, <br> and the AI will generate a Python regex pattern for you.")
        
        with card.add_form(action="/gen_regex", method="POST") as form:
            form.add_formtext(label="Input String 1", name="string1", placeholder="http://user1.pycob.app")
            form.add_formtext(label="Desired Output 1", name="output1", placeholder="user1")

            form.add_formtext(label="Input String 2", name="string2", placeholder="http://user2.pycob.app")
            form.add_formtext(label="Desired Output 2", name="output2", placeholder="user2")

            form.add_formtext(label="Input String 3", name="string3", placeholder="http://user3.pycob.app")
            form.add_formtext(label="Desired Output31", name="output3", placeholder="user3")

            form.add_formsubmit()


    return page
        
# APP CONFIGURATION
app = cob.App("AI Regex Generator", use_built_in_auth=False)

app.register_function(home)
app.register_function(gen_regex)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
