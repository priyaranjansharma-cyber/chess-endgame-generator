import random
import re
import chess
import chess.svg
import streamlit as st

# Set web page styling
st.set_page_config(page_title="Chess Endgame Generator", page_icon="♟️", layout="centered")

def generate_endgame_position(piece_string, side_to_move, difficulty, platform):
    """
    Parses a string of piece symbols, generates a random valid chess position,
    and returns (fen, platform_url) with manually managed character formatting.
    """
    # 1. Clean the input string and separate by spaces or commas
    cleaned_input = re.sub(r'[^a-zA-Z]', ' ', piece_string)
    requested_pieces = cleaned_input.split()
    
    # 2. Validation
    valid_symbols = set('PNBRQpnbrq')
    for p in requested_pieces:
        if p not in valid_symbols:
            raise ValueError(f"Invalid piece symbol: '{p}'. Use P, N, B, R, Q (White) or p, n, b, r, q (Black).")

    # Always include kings
    pieces_to_place = [
        (chess.KING, chess.WHITE),
        (chess.KING, chess.BLACK)
    ]
    
    symbol_map = {
        'P': (chess.PAWN, chess.WHITE), 'N': (chess.KNIGHT, chess.WHITE),
        'B': (chess.BISHOP, chess.WHITE), 'R': (chess.ROOK, chess.WHITE),
        'Q': (chess.QUEEN, chess.WHITE),
        'p': (chess.PAWN, chess.BLACK), 'n': (chess.KNIGHT, chess.BLACK),
        'b': (chess.BISHOP, chess.BLACK), 'r': (chess.ROOK, chess.BLACK),
        'q': (chess.QUEEN, chess.BLACK)
    }
    
    for symbol in requested_pieces:
        pieces_to_place.append(symbol_map[symbol])
        
    if len(pieces_to_place) > 64:
        raise ValueError("Too many pieces requested for a standard board.")

    all_squares = list(chess.SQUARES)
    max_attempts = 3000
    
    for attempt in range(max_attempts):
        board = chess.Board(None) # Empty board
        
        # Difficulty Logic: 
        # 'Easy' clusters pieces on middle ranks (index 2 to 5)
        # 'Hard' forces pieces into highly scattered/disorganized setups
        if difficulty == "Easy":
            # Restrict core pool slightly to create structured tactical clusters
            filtered_squares = [s for s in all_squares if chess.square_rank(s) in range(2, 6)]
            if len(filtered_squares) >= len(pieces_to_place):
                squares_pool = random.sample(filtered_squares, len(pieces_to_place))
            else:
                squares_pool = random.sample(all_squares, len(pieces_to_place))
        else:
            squares_pool = random.sample(all_squares, len(pieces_to_place))
            
        illegal_placement = False
        for square, (piece_type, color) in zip(squares_pool, pieces_to_place):
            # Enforce absolute pawn rank rules (cannot go on 1st or 8th rank)
            if piece_type == chess.PAWN and (chess.square_rank(square) in range(0, 8, 7)):
                illegal_placement = True
                break
            board.set_piece_at(square, chess.Piece(piece_type, color))
            
        if illegal_placement:
            continue
            
        # Set active player
        board.turn = chess.WHITE if side_to_move == "White" else chess.BLACK
        
        # Check rule engine validity (no touching kings, side not moving isn't in check)
        if board.is_valid():
            raw_fen = board.fen()
            
            # --- Platform URL Routing ---
            if platform == "Lichess":
                fen_url_safe = raw_fen.replace(" ", "_")
                url = f"https://lichess.org/?fen={fen_url_safe}#ai"
            else:
                # Direct string formatting safely translates characters for Chess.com without trigger errors
                fen_url_safe = raw_fen.replace(" ", "+")
                url = f"https://chess.com/analysis?fen={fen_url_safe}"
            
            return raw_fen, url
            
    raise RuntimeError("Could not find a legally valid random configuration. Try fewer pieces.")

# --- Streamlit Web Interface Design ---
st.title("♟️ Custom Chess Endgame Generator")
st.write("Generate custom endgame configurations instantly and export them directly to your favorite platform to play against the engine.")

# Platform Choice
platform_selection = st.radio("Choose Target Platform:", ["Lichess", "Chess.com"], horizontal=True)

# Input Layout
piece_input = st.text_input(
    "Enter Pieces (excluding Kings):", 
    value="R, p, p", 
    help="White: P, N, B, R, Q | Black: p, n, b, r, q (Separated by spaces or commas)"
)

col1, col2 = st.columns(2)

with col1:
    turn_selection = st.selectbox("Who moves first?", ["White", "Black"])

with col2:
    difficulty_selection = st.select_slider("Difficulty Setup Level:", options=["Easy", "Standard", "Hard"])

st.markdown("---")

if st.button("Generate & Practice Position", type="primary"):
    if not piece_input.strip():
        st.warning("Please enter at least one piece to generate an endgame scenario.")
    else:
        with st.spinner("Finding a legally valid board position..."):
            try:
                fen, target_url = generate_endgame_position(
                    piece_string=piece_input,
                    side_to_move=turn_selection,
                    difficulty=difficulty_selection,
                    platform=platform_selection
                )
                # Persist the result so it survives reruns (e.g. toggling "Flip board")
                st.session_state["result"] = {
                    "fen": fen,
                    "url": target_url,
                    "platform": platform_selection,
                    "turn": turn_selection,
                }
            except ValueError as ve:
                st.session_state.pop("result", None)
                st.error(f"Input Error: {ve}")
            except Exception as e:
                st.session_state.pop("result", None)
                st.error(f"Generation Failed: {e}. Try adjusting your piece composition.")

# --- Display the most recent result ---
if "result" in st.session_state:
    result = st.session_state["result"]
    board = chess.Board(result["fen"])

    st.success(f"🎉 Board layout successfully built for {result['platform']}!")

    # Feature 1: visual board
    flip = st.checkbox(
        "Flip board",
        value=(result["turn"] == "Black"),
        help="Defaults to the side that moves first"
    )
    svg = chess.svg.board(
        board,
        orientation=chess.BLACK if flip else chess.WHITE,
        size=400,
    )
    st.image(svg, use_container_width=True)
    st.caption(f"{result['turn']} to move")

    # Feature 2: copyable FEN (st.code includes a copy icon at the top right)
    st.markdown("**FEN** (use the copy icon at the top right of the box):")
    st.code(result["fen"], language=None)

    # Using a native text link inside st.info is the safest layout option for mobile browsers
    st.info("💡 Your position is ready! Click the link below to start practicing:")
    st.link_button(f"👉 Open & Practice on {result['platform']}", result["url"], use_container_width=True)
