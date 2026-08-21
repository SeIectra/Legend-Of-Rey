import pygame

# 📌 **Pygame'in ses modülünü başlat**
pygame.mixer.init()

# 📌 **RENKLER TANIMLANDI**
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BLUE = (10, 10, 50)
PURPLE = (100, 0, 200)
HOVER_COLOR = (150, 50, 255)
BROWN_YELLOW = (153, 101, 21)
RED = (255, 0, 0)  

WIDTH, HEIGHT = 800, 600

# 📌 **SES DOSYALARINI YÜKLE**
try:
    # 🎵 **Müzik dosyasını pygame.mixer.music ile yükle**
    pygame.mixer.music.load("assets/background_music.wav")
    pygame.mixer.music.set_volume(0.5)  # Varsayılan %50 ses seviyesi
    pygame.mixer.music.play(-1)  # Sonsuz döngüde çal

    # 🔊 **Ses efektlerini pygame.mixer.Sound ile yükle**
    attack_sound = pygame.mixer.Sound("assets/attack.wav")
    jump_sound = pygame.mixer.Sound("assets/jump.wav")
    shoot_sound = pygame.mixer.Sound("assets/shoot.wav")
    walk_sound = pygame.mixer.Sound("assets/footstep.wav")

    # **Varsayılan ses seviyeleri**
    attack_sound.set_volume(0.7)
    jump_sound.set_volume(0.7)
    shoot_sound.set_volume(0.7)
    walk_sound.set_volume(0.5)

except pygame.error as e:
    print(f"Ses yükleme hatası: {e}")
    pygame.mixer.music.stop()
    attack_sound = None
    jump_sound = None
    shoot_sound = None
    walk_sound = None

# 📌 **SCROLL BAR (SES KONTROL) SINIFI**
class ScrollBar:
    def __init__(self, x, y, width, height, min_val=0.0, max_val=1.0, value=0.5):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.handle_rect = pygame.Rect(x + width * value, y, 20, height)
        self.dragging = False

    def draw(self, screen):
        pygame.draw.rect(screen, WHITE, self.rect, 2)
        pygame.draw.rect(screen, PURPLE, self.handle_rect)

    def update(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.dragging = True

        if event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False

        if self.dragging:
            mouse_x, _ = pygame.mouse.get_pos()
            self.handle_rect.x = max(self.rect.x, min(mouse_x, self.rect.x + self.rect.width - 20))
            self.value = (self.handle_rect.x - self.rect.x) / (self.rect.width - 20)

    def get_value(self):
        return self.value

# 📌 **SES KAYDIRICILARINI GLOBAL OLARAK TANIMLA**
music_slider = ScrollBar(WIDTH // 4, 250, 300, 20, value=pygame.mixer.music.get_volume() if pygame.mixer.get_init() else 0.5)
sfx_slider = ScrollBar(WIDTH // 4, 350, 300, 20, value=attack_sound.get_volume() if attack_sound else 0.5)

def draw_text(screen, text, x, y, size=36, color=WHITE):
    font = pygame.font.SysFont("Arial", size)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def show_settings(screen, back_action):
    global music_slider, sfx_slider  
    
    screen.fill(DARK_BLUE)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            music_slider.update(event)
            sfx_slider.update(event)

            # 📌 **Ses seviyelerini her hareket ettiğinde güncelle**
            update_sound_settings()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if WIDTH // 3 <= mouse_x <= WIDTH // 3 + 200 and 400 <= mouse_y <= 450:
                    running = False
                    pygame.time.delay(150)
                    back_action()

        screen.fill(DARK_BLUE)
        draw_text(screen, "Settings", WIDTH // 3, 100, 50, WHITE)
        draw_text(screen, "Müzik Ses Seviyesi", WIDTH // 4, 200, 30, WHITE)
        draw_text(screen, "SFX Ses Seviyesi", WIDTH // 4, 300, 30, WHITE)

        music_slider.draw(screen)
        sfx_slider.draw(screen)

        pygame.draw.rect(screen, PURPLE, (WIDTH // 3, 400, 200, 50), border_radius=10)
        draw_text(screen, "Back", WIDTH // 3 + 50, 410, 30, WHITE)

        pygame.display.flip()

       
def update_sound_settings():
    volume = music_slider.get_value()
    sfx_volume = sfx_slider.get_value()

    pygame.mixer.music.set_volume(volume)  

    
    if attack_sound:
        attack_sound.set_volume(sfx_volume)
    if jump_sound:
        jump_sound.set_volume(sfx_volume)
    if shoot_sound:
        shoot_sound.set_volume(sfx_volume)
    if walk_sound:
        walk_sound.set_volume(sfx_volume)
 

def draw_button(screen, x, y, width, height, text, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    color = HOVER_COLOR if pygame.Rect(x, y, width, height).collidepoint(mouse) else PURPLE

    pygame.draw.rect(screen, color, (x, y, width, height), border_radius=10)

    font = pygame.font.SysFont("Arial", 30)
    text_surface = font.render(text, True, WHITE)
    
    text_x = x + (width - text_surface.get_width()) // 2
    text_y = y + (height - text_surface.get_height()) // 2
    screen.blit(text_surface, (text_x, text_y))

    if pygame.Rect(x, y, width, height).collidepoint(mouse) and click[0] == 1 and action:
        pygame.time.delay(150)
        action()
