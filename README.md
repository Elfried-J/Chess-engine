# Chess-engine
Chess game created after following the instructions of Eddie Sharick(eddie) with a few additions of my own
The system includes full support for chess rules such as castling, en passant, pawn promotion, and move legality validation. A unique feature is the dynamic precision bar, which visually indicates which player has played more accurately based on the engine’s evaluation throughout the game.

The project is structured around three core Python files, each serving a specific role in the game’s architecture.

The file MainInterface.py manages the graphical user interface and is responsible for initializing the display, loading and drawing piece images, capturing player input through mouse clicks, and rendering the board, move history, material score, and the precision bar. The layout consists of three key zones: a left-side precision bar, the main 8×8 chessboard, and a move log panel on the right. The top and bottom bars display the players’ identities with avatars, and the board updates dynamically as the game progresses.

The Chessbot.py module contains the artificial intelligence logic. It uses a modified version of the NegaMax algorithm with alpha-beta pruning to simulate and evaluate possible move sequences up to a specified depth. Each position is assessed using a combination of material values (e.g., pawn = 1, queen = 9) and position-specific scores for non-king pieces. The evaluation is done from the perspective of the side to move. The AI selects the move that maximizes its advantage while minimizing the opponent’s.

The file ChessEngine.py implements the game’s rules and internal state management. It defines the GameState class, which keeps track of the board configuration, king positions, castling rights, en passant targets, and the move history. It provides the logic to generate all possible legal moves by filtering out those that would leave the king in check. The Move class encodes each move’s details, including start and end coordinates, whether it is a capture, promotion, or special move like castling or en passant, and provides algebraic notation conversion.

The engine continuously recalculates the material score based on captured pieces and updates a precision score, which is reflected on the left precision bar. The bar is initially split evenly between both players and shifts based on how optimal each move is relative to the engine’s evaluation, giving a visual indicator of performance over time.

To run the program, ensure that the three core Python files are placed in the same directory along with a folder named images/ containing piece images (e.g., wR.png, bK.png) and a default avatar image for the player bars. You will also need to install Pygame via:

By default, the human player always plays as White, and pawn promotions are handled automatically by upgrading to a Queen. The engine does not use machine learning or external opening databases; it makes decisions purely based on handcrafted evaluation and recursive search.

This project provides a hands-on demonstration of how classic AI techniques like search trees and heuristic evaluation can be applied in a real-time strategy context. It also showcases how object-oriented design can be used to manage game state, rule enforcement, and graphical interaction. It serves as a solid foundation for anyone looking to build a chess engine, extend a game interface, or understand the internals of AI-driven game agents.
