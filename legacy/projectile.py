import pygame

class Projectile:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.width = 10
        self.height = 5
        self.speed = 8
        self.direction = direction  # Sağ mı sol mu?
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill((255, 255, 0))  # Sarı renkli mermi

    def update(self):
        """Mermi hareket eder"""
        if self.direction == "right":
            self.x += self.speed
        else:
            self.x -= self.speed

    def draw(self, screen):
        """Mermiyi ekrana çizer"""
        screen.blit(self.image, (self.x, self.y))

    def check_collision(self, enemies):
        """Mermi düşmana çarpınca onu öldür ve kendini yok et"""
        projectile_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        for enemy in enemies:
            enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.width, enemy.height)
            if projectile_rect.colliderect(enemy_rect) and enemy.alive:
                enemy.take_damage()  # 📌 Düşman hasar alsın
                return True  # Mermi yok olsun
        return False
