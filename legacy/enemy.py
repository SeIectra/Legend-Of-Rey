import pygame
from settings import *
from util import wall_collision

class Enemy:
    def __init__(self, x, y, image_path):
        self.x, self.y = x, y
        self.width, self.height = 40, 40
        self.image = pygame.image.load(image_path)
        self.image = pygame.transform.scale(self.image, (40, 40))
        self.alive = True
        self.speed = 2  # Düşman hareket hızı
        self.attack_range = 50  # Saldırı menzili
        self.attack_timer = 0
        self.attack_cooldown = 60  # Saldırılar daha yavaş olacak
        self.health = 3  # Düşman canı

        # **Saldırı Efektleri PNG'leri**
        self.attack_effect = None  # Varsayılan olarak görünmez

        # **Ses Efektleri**
        self.attack_sound = pygame.mixer.Sound("assets/enemy_attack.wav")
        self.hit_sound = pygame.mixer.Sound("assets/enemy_hit.wav")

    def update(self, screen, player, walls):
        if not self.alive:
            return
            

        # Oyuncuya yaklaşma
        if abs(self.x - player.x) > self.attack_range:
            if self.x < player.x and wall_collision(self, self.speed, 0, walls) == False:
                wall_collision(self, self.speed, 0, walls)
            elif self.x > player.x:
                wall_collision(self, -1*self.speed, 0, walls)
        if abs(self.y - player.y) > self.attack_range:
            if self.y < player.y:
                wall_collision(self, 0, self.speed, walls) 
            elif self.y > player.y:
                wall_collision(self, 0, -1*self.speed, walls)
        else:
            self.attack_timer += 1
            if self.attack_timer >= self.attack_cooldown:  # Daha yavaş saldırılar
                self.attack(player, screen)
                self.attack_timer = 0

    def attack(self, player, screen):
        if self.alive:
            self.attack_sound.play()
            player.take_damage()  # Oyuncuya hasar ver
            self.show_attack_effect(screen)

    def show_attack_effect(self, screen):
        self.attack_display_timer = 240  # Saldırı efekti daha uzun süre görünsün
        """Saldırı efektini gösterir (Goblin: bıçak, Spider: ağ, Skeleton: kemik)"""
        if self.attack_effect and self.attack_display_timer > 0:
            self.attack_display_timer -= 1
            screen.blit(self.attack_effect, (self.x + self.width // 2, self.y + self.height // 2))

    def draw(self, screen):
        if self.alive:
            screen.blit(self.image, (self.x, self.y))

    def take_damage(self):
        if self.alive:
            self.health -= 1
            self.hit_sound.play()
            if self.health <= 0:
                self.alive = False

    def collides(self, x, y, walls):
        """Oyuncunun duvarlara çarpmasını önler."""
        player_rect = pygame.Rect(x, y, self.width, self.height)
        for wall in walls:
            if player_rect.colliderect(wall):
                return True
        return False


# **Goblin Sınıfı**
class Goblin(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/goblin.png")
        self.attack_effect = pygame.image.load("assets/goblin_knife.png")  # **Bıçak PNG**
        self.attack_effect = pygame.transform.scale(self.attack_effect, (50, 20))

    def attack(self, player, screen):
        super().attack(player, screen)
        print("👹 Goblin bıçakla saldırdı!")

# **Spider Sınıfı (Ağ Fırlatma)**
class Spider(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/spider.png")
        self.attack_effect = pygame.image.load("assets/spider_web.png")  # **Ağ PNG**
        self.attack_effect = pygame.transform.scale(self.attack_effect, (50, 50))

    def attack(self, player, screen):
        super().attack(player, screen)
        print("🕷️ Spider ağ fırlattı!")

# **Skeleton Sınıfı (Kemik Fırlatma)**
class Skeleton(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "assets/skeleton.png")
        self.attack_effect = pygame.image.load("assets/bone_projectile.png")  # **Kemik PNG**
        self.attack_effect = pygame.transform.scale(self.attack_effect, (40, 40))

    def attack(self, player, screen):
        super().attack(player, screen)
        print("💀 Skeleton kemik fırlattı!")
