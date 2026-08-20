import pygame
from settings import *
from spikes import Spike


class Level:
    def __init__(self, level_number=1):
        self.level_number = level_number
        self.walls = self.generate_walls()
        self.spikes = [Spike(200, 300), Spike(500, 450)]
        
        self.wall_texture = pygame.image.load("assets/platform.png")
        self.wall_texture = pygame.transform.scale(self.wall_texture, (20, 20))

    def generate_walls(self):
        if self.level_number == 1:
            return [
                pygame.Rect(50, 50, 700, 20),
                pygame.Rect(50, 530, 700, 20),
                pygame.Rect(50, 50, 20, 500),
                pygame.Rect(730, 50, 20, 500),
                pygame.Rect(300, 200, 200, 20),
            ]
        elif self.level_number == 2:
            return [
                pygame.Rect(50, 50, 700, 20),
                pygame.Rect(50, 530, 700, 20),
                pygame.Rect(50, 50, 20, 500),
                pygame.Rect(730, 50, 20, 500),
                pygame.Rect(250, 150, 300, 20),
                pygame.Rect(100, 350, 500, 20),
            ]
        elif self.level_number == 3:
            return [
                pygame.Rect(50, 50, 700, 20),
                pygame.Rect(50, 530, 700, 20),
                pygame.Rect(50, 50, 20, 500),
                pygame.Rect(730, 50, 20, 500),
                pygame.Rect(200, 250, 400, 20),
                pygame.Rect(400, 400, 300, 20),
            ]
        elif self.level_number == 4:
            return [
                pygame.Rect(50, 50, 700, 20),
                pygame.Rect(50, 530, 700, 20),
                pygame.Rect(50, 50, 20, 500),
                pygame.Rect(730, 50, 20, 500),
            ]
        return []

    def draw(self, screen):
        for wall in self.walls:
            for x in range(wall.x, wall.x + wall.width, 20):
                for y in range(wall.y, wall.y + wall.height, 20):
                    screen.blit(self.wall_texture, (x, y))

        for spike in self.spikes:
            spike.draw(screen)

    def update(self, player):
        for spike in self.spikes:
            spike.check_collision(player)

    def get_enemy_positions(self):
        if self.level_number == 1:
            return [(100, 200), (400, 300)], "Goblin"
        elif self.level_number == 2:
            return [(200, 150), (500, 400)], "Spider"
        elif self.level_number == 3:
            return [(300, 250), (600, 350)], "Skeleton"
        elif self.level_number == 4:
            return [(400, 300)], "Boss"
        return [], ""
