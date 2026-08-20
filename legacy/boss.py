import pygame
import random

class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 80
        self.height = 80
        self.health = 100
        self.speed = 2
        self.attack_cooldown = 100
        self.attack_timer = 0
        self.image = pygame.image.load("assets/boss.png")
        self.weak_spot = pygame.image.load("assets/boss_weak_spot.png")
        self.visible_weak_spot = False

    def move(self, player):
        if player.x > self.x:
            self.x += self.speed
        elif player.x < self.x:
            self.x -= self.speed
        if player.y > self.y:
            self.y += self.speed
        elif player.y < self.y:
            self.y -= self.speed

    def attack(self, screen):
        if self.attack_timer == 0:
            attack_choice = random.randint(1, 3)
            if attack_choice == 1:
                attack_image = pygame.image.load("assets/boss_attack1.png")
            elif attack_choice == 2:
                attack_image = pygame.image.load("assets/boss_attack2.png")
            else:
                attack_image = pygame.image.load("assets/boss_attack3.png")
            screen.blit(attack_image, (self.x, self.y))
            self.attack_timer = self.attack_cooldown
        else:
            self.attack_timer -= 1

    def take_damage(self, amount):
        if self.visible_weak_spot:
            self.health -= amount
            if self.health <= 0:
                self.health = 0

    def draw(self, screen):
        screen.blit(self.image, (self.x, self.y))
        if self.visible_weak_spot:
            screen.blit(self.weak_spot, (self.x + 20, self.y + 20))
