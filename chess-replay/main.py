import pycob as cob
import chess
import chess.pgn
import io

from dataclasses import dataclass


def get_frames(game: chess.pgn.Game) -> list:
    """Get frames from a game"""

    current_game = game

    frames = []

    while True:
        current_board = current_game.board()

        last_move = current_game.move

        svg = chess.svg.board(
                current_board,
                lastmove=last_move,
                fill={},
                arrows=[],
                squares=None,
                size=350,
        )

        frames.append(svg)

        captures = {}
        for capture in current_board.generate_legal_captures():
            print(capture)
            if capture.from_square in captures:
                captures[capture.from_square].append(capture.to_square)
            else:
                captures[capture.from_square] = [capture.to_square]
        #    arrows.append(chess.svg.Arrow(capture.from_square, capture.to_square, color="#ff0011cc"))

        for capture_from in captures:
            arrows = []

            for capture_to in captures[capture_from]:
                arrows.append(chess.svg.Arrow(capture_from, capture_to, color="#ff0011cc"))

            svg = chess.svg.board(
                current_board,
                fill={},
                arrows=arrows,
                squares=None,
                size=350,
            )
            # display.SVG(svg)
            # frames.append(Frame(svg, "Title", "Subtitle"))
            frames.append(svg)

        if current_game.is_end():
            break

        current_game = current_game.next()

    return frames

def home(server_request: cob.Request) -> cob.Page:
    """Home page"""
    page = cob.Page("Chess Replay")
    page.add_text("This is a chess replay app. It allows you to replay chess games from the PGN file format.")

    pgn_param = server_request.params("pgn")
    size = server_request.params("size")

    scholars_mate = """
1. e4 e5
2. Qh5 Nc6
3. Bc4 Nf6
4. Qxf7    
    """

    with page.add_card() as card:
        card.add_header("Game Data")
        card.add_link("Portable Game Notation", "https://en.wikipedia.org/wiki/Portable_Game_Notation")
        with card.add_form(action="/") as form:
            form.add_formtextarea("PGN", "pgn", value=scholars_mate if pgn_param is None or pgn_param=="" else pgn_param)
            form.add_formselect("Size", "size", ["Small", "Full Screen"], value="Small")
            form.add_formsubmit("Playback")
        
    if pgn_param is None or pgn_param == "":
        pgn_param = scholars_mate
    
    pgn = io.StringIO(pgn_param)
    game = chess.pgn.read_game(pgn)

    frames = get_frames(game)

    js = f"""
    <div class="flex">
        <div id="svg-container" class="mx-auto {'h-screen' if size == 'Full Screen' else ''}"></div>
    </div>
    """

    js += """
    <script>
    function displaySVGs(svgArray) {
    let index = 0;
    const intervalId = setInterval(() => {
        const svgString = svgArray[index];
        // Display the SVG string however you want,
        // for example by setting it as the innerHTML
        // of a div element with id "svg-container":
        element = document.getElementById("svg-container");
        element.innerHTML = svgString.replace('width="350"', 'width="100%"').replace('height="350"', 'height="100%"');
        element.scrollIntoView();
        index++;
        if (index === svgArray.length) {
        clearInterval(intervalId);
        }
    }, 1000);
    }
    """

    js += f"""
    // Example usage:
    const svgArray = {frames};
    displaySVGs(svgArray);
    </script>
    """

    page.add_html(js)

    return page

app = cob.App("Replay Chess Games")

app.register_function(home, show_in_navbar=False)

server = app.run()