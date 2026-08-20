import pygame

class Spike:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.width, self.height = 40, 20  # 📌 Diken boyutları
        self.image = pygame.image.load("assets/spike.png")
        self.image = pygame.transform.scale(self.image, (self.width, self.height))

    def draw(self, screen):
        """Dikenleri ekrana çizer."""
        screen.blit(self.image, (self.x, self.y))

    def check_collision(self, player):
        """Oyuncu dikenlere değerse can kaybetsin."""
        spike_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)

        if spike_rect.colliderect(player_rect):
            player.take_damage()  # 📌 Can kaybettir
