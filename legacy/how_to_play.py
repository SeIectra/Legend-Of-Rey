import pygame
from settings import *
from settings import draw_button  # 🔹 draw_button fonksiyonunu import ettik

def show_how_to_play(screen, back_action):
    screen.fill(DARK_BLUE)
    
    draw_text(screen, "How to Play", WIDTH // 3, 100, 50, WHITE)
    draw_text(screen, "Move: Arrow Buttons, WASD", WIDTH // 4, 200, 30, WHITE)
    draw_text(screen, "Melee Attack: Z", WIDTH // 4, 250, 30, WHITE)
    draw_text(screen, "Shoot: X", WIDTH // 4, 300, 30, WHITE)

    draw_button(screen, WIDTH // 3, 400, 200, 50, "Back", back_action)