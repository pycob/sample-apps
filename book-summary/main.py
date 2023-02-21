# INITIALIZATION: Do not delete this comment
import pycob as cob



# PAGE FUNCTIONS: Do not delete this comment
def book(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Book")
    page.add_header("Summary")
    
    book_id = server_request.params('book_id')
    
    if book_id != "":
        book_data = server_request.retrieve_dict('book_data', object_id=book_id)
    
        card = page.add_card()
    
        card.add_header(book_data['title'], classes="mx-auto")
        card.add_header(book_data['subtitle'], size=3, classes="mx-auto")
        card.add_image(book_data['cover_url'], "Cover Image", classes="mx-auto")
        card.add_header(f"By: {book_data['author']}", size=2, classes="mx-auto")
        
        with card.add_container(classes="whitespace-pre-wrap") as container:
            container.add_html(book_data['ai_summary'])
    
    return page
    
def home(server_request: cob.Request) -> cob.Page:
    page = cob.Page("Home")
    page.add_header("AI-Generated Book Summaries")
    page.add_text("10-Bullet Point Summaries of Books")
    
    book_index = server_request.retrieve_dict('book_index', object_id='book_index')
    
    container = page.add_container(grid_columns=4)
    
    if book_index and 'book_index_list' in book_index:
        for book_summary_data in book_index['book_index_list']:
            with container.add_card() as card:
                card.add_header(book_summary_data['title'], size=4, classes="mx-auto text-center")
                card.add_image(book_summary_data['cover_url'], "Cover Image", classes="mx-auto")
                card.add_header(book_summary_data['author'], size=3, classes="mx-auto text-center")
                card.add_link("AI Summary", '/book?book_id=' + book_summary_data['work_id'])
    
    page.add_link("Add a new book", '/new_book')
    return page
    
def new_book(server_request: cob.Request) -> cob.Page:
    page = cob.Page("New Book")
    from urllib.request import urlopen
    import json
    
    page.add_header("Book Details")
    page.add_text("Paste in the link from Open Library")
    
    with page.add_card() as card:
        with card.add_form(action="https://openlibrary.org/search") as form:
            form.add_formtext("Search", "q", "The Cold Start Problem")
            form.add_formhidden(name='mode', value='everything')
            form.add_formsubmit('Search OpenLibrary')
    
    with page.add_card() as card:
        with card.add_form(action="?", method="POST") as form:
            form.add_formtext("Open Library URL", "openlibrary_url", "https://openlibrary.org/works/OL17078706W/Zero_to_One?edition=key%3A/books/OL27546580M")
            form.add_formsubmit()
    
    openlibrary_url = server_request.params('openlibrary_url')
    
    if openlibrary_url and openlibrary_url != "":
        # From URL of this format: https://openlibrary.org/works/OL17078706W/Zero_to_One?edition=key%3A/books/OL27546580M
        # Parse the work ID
        work_id = openlibrary_url.split('/')[4]
        # Get the JSON data from the Open Library API
        url = f"https://openlibrary.org/works/{work_id}.json"
        response = urlopen(url)
        data_json = json.loads(response.read())
    
        title = ''
        subtitle = ''
        cover_url = ''
        author = ''
        
        with page.add_card() as card:
            card.add_link("JSON URL", url)
    
            if 'title' in data_json:
                title = data_json['title']
                card.add_header(f"{title}")
            
            if 'subtitle' in data_json:
                subtitle = data_json['subtitle']
                card.add_text(f"{subtitle}")
    
            if 'covers' in data_json:
                covers = data_json['covers']
                cover_id = covers[0]
                cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
                card.add_image(cover_url, "Cover Image")
    
            if 'authors' in data_json:
                authors = data_json['authors']
                authors_data = authors[0]
                if 'author' in authors_data:
                    author_data = authors_data['author']
                    
                    if 'key' in author_data:
                        author_key = author_data['key']
    
                        author_url = f"https://openlibrary.org{author_key}.json"
                        response = urlopen(author_url)
                        author_json = json.loads(response.read())
    
                        if 'name' in author_json:
                            author = author_json['name']
                            card.add_text(f"Author: {author}")
    
            # You are a book summarizer. Summarize the book: "Zero to One" by Peter Thiel in 10 bullet points where each bullet point captures one of the major ideas presented in the book. Each bullet point should be no more than 280 characters.
    
            ai_summary = app.generate_text_from_ai(f'''You are a book summarizer. Summarize the book: "{title}" by {author} in 10 bullet points where each bullet point captures one of the major ideas presented in the book. Each bullet point should be no more than 280 characters.''')
    
            card.add_text(f"AI Summary: {ai_summary}")
    
            book_data = {
                'title': title,
                'author': author,
                'subtitle': subtitle,
                'cover_url': cover_url,
                'work_id': work_id,
                'ai_summary': ai_summary,
            }
    
            server_request.store_dict('book_data', object_id=work_id, value=book_data)
    
    return page
    
# APP CONFIGURATION

app = cob.App("Book Summary", use_built_in_auth=False)

app.add_page('/book', 'book', book, show_in_navbar=True, footer_category=None)
app.add_page('/', 'home', home, show_in_navbar=True, footer_category=None)
app.add_page('/new_book', 'new_book', new_book, show_in_navbar=True, footer_category=None)

server = app.run()
# Run this using `python3 main.py` or `python main.py` depending on your system.
