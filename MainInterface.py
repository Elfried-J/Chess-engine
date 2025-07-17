import os
import sys
import pygame as p
import ChessEngine, Chessbot
from multiprocessing import Process, Queue

BOARD_WIDTH = BOARD_HEIGHT = 512
DIMENSION = 8
SQUARE_SIZE = BOARD_HEIGHT // DIMENSION

PRECISION_BAR_WIDTH  = 30
MOVE_LOG_PANEL_WIDTH = 250
PLAYER_BAR_HEIGHT    = 30

WINDOW_WIDTH  = PRECISION_BAR_WIDTH + BOARD_WIDTH + MOVE_LOG_PANEL_WIDTH  # 30 + 512 + 250 = 792
WINDOW_HEIGHT = PLAYER_BAR_HEIGHT + BOARD_HEIGHT + PLAYER_BAR_HEIGHT      # 30 + 512 + 30 = 572

OFFSET_X = PRECISION_BAR_WIDTH
OFFSET_Y = PLAYER_BAR_HEIGHT

MAX_FPS = 15
IMAGES = {}

HUMAN_IS_WHITE = True  # human always White; AI always Black


def loadImages():
    """Load and scale piece images plus the profile pic."""
    image_dir = os.path.join(os.path.dirname(__file__), "images")
    # chess pieces
    for piece in ['wp','wR','wN','wB','wK','wQ','bp','bR','bN','bB','bK','bQ']:
        path = os.path.join(image_dir, piece + ".png")
        IMAGES[piece] = p.transform.scale(
            p.image.load(path), (SQUARE_SIZE, SQUARE_SIZE)
        )
    # profile pic
    pfp_path = os.path.join(image_dir, "blank-default-pfp-wue0zko1dfxs9z2c.jpg")
    IMAGES['pfp'] = p.transform.scale(
        p.image.load(pfp_path),
        (PLAYER_BAR_HEIGHT, PLAYER_BAR_HEIGHT)
    )


def drawPlayerBars(screen, font):
    """Draw top (Robot) and bottom (Player1) bars with their pfp and name."""
    pfp = IMAGES['pfp']
    robot_surf  = font.render("Robot",   True, p.Color("black"))
    player_surf = font.render("Player1", True, p.Color("black"))

    # top bar
    x_pic = PRECISION_BAR_WIDTH
    y_pic = (PLAYER_BAR_HEIGHT - PLAYER_BAR_HEIGHT) // 2
    screen.blit(pfp, (x_pic, y_pic))
    screen.blit(robot_surf, (
        x_pic + PLAYER_BAR_HEIGHT + 5,
        (PLAYER_BAR_HEIGHT - robot_surf.get_height()) // 2
    ))

    # bottom bar
    y_bar_bot = OFFSET_Y + BOARD_HEIGHT
    y_pic_bot = y_bar_bot + (PLAYER_BAR_HEIGHT - PLAYER_BAR_HEIGHT) // 2
    screen.blit(pfp, (x_pic, y_pic_bot))
    screen.blit(player_surf, (
        x_pic + PLAYER_BAR_HEIGHT + 5,
        y_bar_bot + (PLAYER_BAR_HEIGHT - player_surf.get_height()) // 2
    ))


def drawScore(screen, gs, font):
    """
    Compute material difference via gs.piecesTaken() and render:
    +N on bottom if White ahead, +N on top if Black ahead.
    """
    gs.piecesTaken()
    score = gs.gameScore
    if score == 0:
        return

    text = f"+{abs(score)}"
    surf = font.render(text, True, p.Color("black"))
    x = OFFSET_X + BOARD_WIDTH // 2 - surf.get_width() // 2

    if score > 0:
        y = OFFSET_Y + BOARD_HEIGHT + (PLAYER_BAR_HEIGHT - surf.get_height()) // 2
    else:
        y = (PLAYER_BAR_HEIGHT - surf.get_height()) // 2

    screen.blit(surf, (x, y))


def drawBoard(screen):
    colors = [p.Color("white"), p.Color("light blue")]
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            rect = p.Rect(
                OFFSET_X + c * SQUARE_SIZE,
                OFFSET_Y + r * SQUARE_SIZE,
                SQUARE_SIZE, SQUARE_SIZE
            )
            p.draw.rect(screen, colors[(r + c) % 2], rect)


def highlightSquares(screen, gs, valid_moves, square_selected):
    if gs.move_log:
        last = gs.move_log[-1]
        s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
        s.set_alpha(100)
        s.fill(p.Color("blue"))
        screen.blit(s, (
            OFFSET_X + last.end_col * SQUARE_SIZE,
            OFFSET_Y + last.end_row * SQUARE_SIZE
        ))
    if square_selected:
        r, c = square_selected
        if gs.board[r][c][0] == ('w' if gs.white_to_move else 'b'):
            s = p.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(p.Color("blue"))
            screen.blit(s, (OFFSET_X + c * SQUARE_SIZE, OFFSET_Y + r * SQUARE_SIZE))
            s.fill(p.Color("light green"))
            for m in valid_moves:
                if m.start_row == r and m.start_col == c:
                    screen.blit(s, (
                        OFFSET_X + m.end_col * SQUARE_SIZE,
                        OFFSET_Y + m.end_row * SQUARE_SIZE
                    ))


def drawPieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            pce = board[r][c]
            if pce != "--":
                screen.blit(
                    IMAGES[pce],
                    p.Rect(
                        OFFSET_X + c * SQUARE_SIZE,
                        OFFSET_Y + r * SQUARE_SIZE,
                        SQUARE_SIZE, SQUARE_SIZE
                    )
                )


def drawMoveLog(screen, gs, font):
    x, y = OFFSET_X + BOARD_WIDTH, OFFSET_Y
    p.draw.rect(screen, p.Color("black"),
                (x, y, MOVE_LOG_PANEL_WIDTH, BOARD_HEIGHT))
    moves = gs.move_log
    texts = []
    for i in range(0, len(moves), 2):
        txt = f"{i//2+1}. {moves[i]}"
        if i+1 < len(moves):
            txt += f" {moves[i+1]}"
        texts.append(txt)
    pad, spacing = 5, 2
    ty = y + pad
    for i in range(0, len(texts), 3):
        row = "  ".join(texts[i:i+3])
        surf = font.render(row, True, p.Color("white"))
        screen.blit(surf, (x + pad, ty))
        ty += surf.get_height() + spacing


def drawEndGameText(screen, text):
    font = p.font.SysFont("Helvetica", 32, True, False)
    shadow = font.render(text, True, p.Color("gray"))
    main   = font.render(text, True, p.Color("black"))
    cx = OFFSET_X + BOARD_WIDTH // 2 - main.get_width() // 2
    cy = OFFSET_Y + BOARD_HEIGHT // 2 - main.get_height() // 2
    screen.blit(shadow, (cx + 2, cy + 2))
    screen.blit(main,   (cx,       cy))


def animateMove(move, screen, board, clock):
    d_r = move.end_row - move.start_row
    d_c = move.end_col - move.start_col
    frames = (abs(d_r) + abs(d_c)) * 7
    for frame in range(frames + 1):
        # redraw board & pieces only
        drawBoard(screen)
        drawPieces(screen, board)

        # landing square
        landing = p.Rect(
            OFFSET_X + move.end_col * SQUARE_SIZE,
            OFFSET_Y + move.end_row * SQUARE_SIZE,
            SQUARE_SIZE, SQUARE_SIZE
        )
        p.draw.rect(
            screen,
            [p.Color("white"), p.Color("light blue")][(move.end_row + move.end_col) % 2],
            landing
        )

        # captured piece (en passant)
        if move.piece_captured != "--":
            if move.is_enpassant_move:
                er = move.end_row + (1 if move.piece_captured[0] == "b" else -1)
                landing = p.Rect(
                    OFFSET_X + move.end_col * SQUARE_SIZE,
                    OFFSET_Y + er * SQUARE_SIZE,
                    SQUARE_SIZE, SQUARE_SIZE
                )
            screen.blit(IMAGES[move.piece_captured], landing)

        # moving piece
        r = move.start_row + d_r * frame / frames
        c = move.start_col + d_c * frame / frames
        screen.blit(
            IMAGES[move.piece_moved],
            p.Rect(
                OFFSET_X + c * SQUARE_SIZE,
                OFFSET_Y + r * SQUARE_SIZE,
                SQUARE_SIZE, SQUARE_SIZE
            )
        )

        p.display.flip()
        clock.tick(60)


def drawGameState(screen, gs, valid_moves, square_selected):
    drawBoard(screen)
    highlightSquares(screen, gs, valid_moves, square_selected)
    drawPieces(screen, gs.board)


def main():
    p.init()
    screen = p.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = p.time.Clock()
    loadImages()

    gs = ChessEngine.GameState()
    move_made = animate = move_undone = False
    game_over = False
    ai_thinking = False
    move_finder_process = None

    move_log_font = p.font.SysFont("Times New Roman", 14, False, False)
    score_font    = p.font.SysFont("Arial", 18, True, False)
    name_font     = p.font.SysFont("Arial", 16, True, False)

    square_selected = ()
    player_clicks = []

    while True:
        valid_moves = gs.getValidMoves()
        human_turn = (
            (gs.white_to_move and HUMAN_IS_WHITE)
            or (not gs.white_to_move and not HUMAN_IS_WHITE)
        )

        for e in p.event.get():
            if e.type == p.QUIT:
                p.quit()
                sys.exit()

            #human clicking
            elif e.type == p.MOUSEBUTTONDOWN and human_turn and not game_over:
                mx, my = p.mouse.get_pos()
                bx, by = mx - OFFSET_X, my - OFFSET_Y
                if 0 <= bx < BOARD_WIDTH and 0 <= by < BOARD_HEIGHT:
                    col = bx // SQUARE_SIZE
                    row = by // SQUARE_SIZE
                    if square_selected == (row, col):
                        square_selected = ()
                        player_clicks = []
                    else:
                        square_selected = (row, col)
                        player_clicks.append(square_selected)

                    if len(player_clicks) == 2:
                        mv = ChessEngine.Move(player_clicks[0], player_clicks[1], gs.board)
                        for m in valid_moves:
                            if mv == m:
                                gs.makeMove(m)
                                move_made = True
                                animate = True
                                square_selected = ()
                                player_clicks = []
                                break
                        else:
                            player_clicks = [square_selected]

            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:  # undo
                    gs.undoMove()
                    move_made = True
                    animate = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False
                    move_undone = True
                elif e.key == p.K_r:  # reset
                    gs = ChessEngine.GameState()
                    square_selected = ()
                    player_clicks = []
                    move_made = animate = move_undone = False
                    game_over = False
                    if ai_thinking:
                        move_finder_process.terminate()
                        ai_thinking = False


        if not game_over and not human_turn and not move_undone:
            if not ai_thinking:
                ai_thinking = True
                return_queue = Queue()
                move_finder_process = Process(
                    target=Chessbot.findBestMove,
                    args=(gs, valid_moves, return_queue)
                )
                move_finder_process.start()

            if not move_finder_process.is_alive():
                ai_mv = return_queue.get() or Chessbot.findRandomMove(valid_moves)
                gs.makeMove(ai_mv)
                move_made = True
                animate = True
                ai_thinking = False

        if move_made:
            if animate:
                animateMove(gs.move_log[-1], screen, gs.board, clock)
            move_made = animate = move_undone = False

        screen.fill(p.Color("white"))
        drawPlayerBars(screen, name_font)
        drawGameState(screen, gs, valid_moves, square_selected)
        drawMoveLog(screen, gs, move_log_font)
        drawScore(screen, gs, score_font)

        if gs.checkmate:
            game_over = True
            winner = "Black" if gs.white_to_move else "White"
            drawEndGameText(screen, f"{winner} wins by checkmate")
        elif gs.stalemate:
            game_over = True
            drawEndGameText(screen, "Stalemate")

        clock.tick(MAX_FPS)
        p.display.flip()


if __name__ == "__main__":
    main()