import pycob as cob
import chess
import chess.pgn
import io

from dataclasses import dataclass


def get_frames(game: chess.pgn.Game) -> list:
    """Get frames from a game"""

    current_game = game

    frames = []

    for i in range(0, 7):
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

        current_game = current_game.next()

    return frames

def home(server_request: cob.Request) -> cob.Page:
    """Home page"""
    page = cob.Page("Chess Replay")
    page.add_text("This is a chess replay app. It allows you to replay chess games from the PGN file format.")

    pgn_param = server_request.params("pgn")

    if pgn_param is None or pgn_param == "":
        with page.add_card() as card:
            card.add_header("Upload PGN")
            with card.add_form(action="/") as form:
                form.add_formtextarea("PGN", "pgn", value="1. e4 e5 2. Nf3 f5 3. d4 g5")
                form.add_formsubmit("Upload")
        
        return page

    pgn = io.StringIO(pgn_param)
    game = chess.pgn.read_game(pgn)

    frames = get_frames(game)

    js = """
    <div class="flex h-screen">
        <div id="svg-container" class="mx-auto"></div>
    </div>
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

app = cob.App("")

app.register_function(home)

server = app.run()