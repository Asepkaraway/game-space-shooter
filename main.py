import pygame
import random
import sys
import os
import math
import array

# ==========================================
# KONFIGURASI GLOBAL
# ==========================================
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Palette Warna (Cyberpunk/Neon)
COLOR_BG = (10, 10, 25)
COLOR_TEXT_LIGHT = (230, 230, 255)
COLOR_PLAYER = (56, 189, 248)       # Light Blue
COLOR_LASER = (244, 63, 94)         # Rose/Red
COLOR_METEOR = (167, 139, 250)      # Purple
COLOR_STAR_FAR = (71, 85, 105)
COLOR_STAR_NEAR = (148, 163, 184)
COLOR_EXPLOSION = (250, 204, 21)    # Yellow
COLOR_POWERUP = (52, 211, 153)      # Green Teal
COLOR_POWERUP_ALT = (250, 204, 21)  # Gold for rapid
COLOR_POWERUP_HEAL = (248, 113, 113) # Soft red/rose

# ==========================================
# AUDIO SYNTHESIS ENGINE
# ==========================================
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)

def generate_sound_laser():
    sample_rate = 44100
    duration = 0.15
    num_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * num_samples)
    for i in range(num_samples):
        t = float(i) / sample_rate
        # Frequency sweep down fast (pew pew)
        freq = 1200 - 6000 * (t / duration)
        if freq < 100: freq = 100
        envelope = 1.0 - (t / duration)
        value = int(32767 * 0.15 * envelope * math.sin(2.0 * math.pi * freq * t))
        buf[i] = value
    return pygame.mixer.Sound(buffer=buf)

def generate_sound_explosion():
    sample_rate = 44100
    duration = 0.3
    num_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * num_samples)
    for i in range(num_samples):
        t = float(i) / sample_rate
        envelope = (1.0 - (t / duration)) ** 2
        # White noise / distorted sound for explosion
        noise = random.uniform(-1.0, 1.0)
        value = int(32767 * 0.2 * envelope * noise)
        buf[i] = value
    return pygame.mixer.Sound(buffer=buf)

def generate_sound_gameover():
    sample_rate = 44100
    duration = 0.8
    num_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * num_samples)
    for i in range(num_samples):
        t = float(i) / sample_rate
        freq = 300 - 200 * (t / duration)
        envelope = 1.0 - (t / duration)
        wave = math.sin(2.0 * math.pi * freq * t)
        wave_distorted = 0.5 if wave > 0 else -0.5
        value = int(32767 * 0.25 * envelope * wave_distorted)
        buf[i] = value
    return pygame.mixer.Sound(buffer=buf)

try:
    SOUND_LASER = generate_sound_laser()
    SOUND_EXPLOSION = generate_sound_explosion()
    SOUND_GAMEOVER = generate_sound_gameover()
except Exception:
    SOUND_LASER = SOUND_EXPLOSION = SOUND_GAMEOVER = None

def play_sound(sound):
    if sound:
        sound.play()

# ==========================================
# KELAS OBJEK GAME
# ==========================================
class Starfield:
    def __init__(self, num_stars):
        self.stars = []
        for _ in range(num_stars):
            x = random.randint(0, WINDOW_WIDTH)
            y = random.randint(0, WINDOW_HEIGHT)
            speed = random.uniform(0.5, 2.5)
            size = 1 if speed < 1.5 else 2
            color = COLOR_STAR_FAR if speed < 1.5 else COLOR_STAR_NEAR
            self.stars.append([x, y, speed, size, color])

    def update(self):
        for star in self.stars:
            star[1] += star[2]
            if star[1] > WINDOW_HEIGHT:
                star[1] = 0
                star[0] = random.randint(0, WINDOW_WIDTH)

    def draw(self, surface):
        for star in self.stars:
            pygame.draw.rect(surface, star[4], (star[0], int(star[1]), star[3], star[3]))

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = 1.0
        self.decay = random.uniform(0.02, 0.05)
        self.color = COLOR_EXPLOSION

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= self.decay

    def draw(self, surface):
        if self.life > 0:
            alpha = int(self.life * 255)
            s = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, alpha), (3, 3), int(3 * self.life))
            surface.blit(s, (int(self.x) - 3, int(self.y) - 3))

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn(self, x, y, count=15):
        for _ in range(count):
            self.particles.append(Particle(x, y))

    def update(self):
        for p in self.particles[:]:
            p.update()
            if p.life <= 0:
                self.particles.remove(p)

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

class Player:
    def __init__(self):
        self.width = 40
        self.height = 30
        self.x = WINDOW_WIDTH // 2 - self.width // 2
        self.y = WINDOW_HEIGHT - self.height - 20
        self.speed = 7
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.health = 3
        self.shield_timer = 0
        self.rapid_fire_timer = 0

    def move(self, dx):
        self.x += dx * self.speed
        if self.x < 0:
            self.x = 0
        elif self.x > WINDOW_WIDTH - self.width:
            self.x = WINDOW_WIDTH - self.width
        self.rect.x = self.x

    def draw(self, surface):
        # Draw sleek spaceship
        points = [
            (self.x + self.width // 2, self.y),                      # Top tip
            (self.x, self.y + self.height),                          # Bottom left
            (self.x + self.width // 2, self.y + self.height - 10),   # Bottom middle
            (self.x + self.width, self.y + self.height)              # Bottom right
        ]
        pygame.draw.polygon(surface, COLOR_PLAYER, points)
        # Glow effect
        pygame.draw.polygon(surface, (186, 230, 253), points, 2)

        if self.shield_timer > 0:
            shield = pygame.Surface((self.width + 18, self.height + 18), pygame.SRCALPHA)
            pygame.draw.ellipse(shield, (90, 220, 255, 120), shield.get_rect())
            surface.blit(shield, (self.x - 9, self.y - 9))

        if self.rapid_fire_timer > 0:
            glow = pygame.Surface((self.width + 16, self.height + 16), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 210, 80, 100), glow.get_rect())
            surface.blit(glow, (self.x - 8, self.y - 8))

class Laser:
    def __init__(self, x, y):
        self.width = 4
        self.height = 15
        self.x = x - self.width // 2
        self.y = y
        self.speed = 10
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self):
        self.y -= self.speed
        self.rect.y = self.y

    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_LASER, self.rect, border_radius=2)
        # Laser Glow
        glow_rect = pygame.Rect(self.x - 2, self.y - 2, self.width + 4, self.height + 4)
        pygame.draw.rect(surface, (253, 164, 175), glow_rect, width=1, border_radius=3)

class Meteor:
    def __init__(self):
        self.size = random.randint(20, 50)
        self.x = random.randint(0, WINDOW_WIDTH - self.size)
        self.y = -self.size
        self.speed = random.uniform(2, 6)
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)
        # Generate random polygon for meteor
        self.points = []
        num_points = random.randint(6, 10)
        for i in range(num_points):
            angle = i * (2 * math.pi / num_points)
            r = self.size // 2 * random.uniform(0.7, 1.0)
            px = self.size // 2 + r * math.cos(angle)
            py = self.size // 2 + r * math.sin(angle)
            self.points.append((px, py))

    def update(self):
        self.y += self.speed
        self.rect.y = int(self.y)

    def draw(self, surface):
        abs_points = [(self.x + p[0], self.y + p[1]) for p in self.points]
        pygame.draw.polygon(surface, COLOR_METEOR, abs_points)
        pygame.draw.polygon(surface, (216, 180, 254), abs_points, 2) # Outline

class PowerUp:
    def __init__(self):
        self.types = ["shield", "rapid", "heal"]
        self.type = random.choice(self.types)
        self.size = 14
        self.x = random.randint(20, WINDOW_WIDTH - 20 - self.size)
        self.y = -self.size
        self.speed = random.uniform(2.0, 3.5)
        self.rect = pygame.Rect(self.x, self.y, self.size, self.size)

    def update(self):
        self.y += self.speed
        self.rect.y = int(self.y)

    def draw(self, surface):
        colors = {
            "shield": COLOR_POWERUP,
            "rapid": COLOR_POWERUP_ALT,
            "heal": COLOR_POWERUP_HEAL,
        }
        color = colors.get(self.type, COLOR_POWERUP)
        center = (self.x + self.size // 2, self.y + self.size // 2)
        pygame.draw.circle(surface, color, center, self.size // 2)
        pygame.draw.circle(surface, (255, 255, 255), center, self.size // 2, 2)

        label = "S" if self.type == "shield" else "R" if self.type == "rapid" else "+"
        text = pygame.font.SysFont("Consolas", 10, bold=True).render(label, True, (15, 15, 30))
        surface.blit(text, (center[0] - text.get_width() // 2, center[1] - text.get_height() // 2))

# ==========================================
# ENGINE GAME UTAMA
# ==========================================
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Cyberpunk Space Shooter")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        
        self.font_main = pygame.font.SysFont("Segoe UI", 36, bold=True)
        self.font_ui = pygame.font.SysFont("Consolas", 20, bold=True)
        
        self.starfield = Starfield(100)
        self.particle_sys = ParticleSystem()
        
        self.highscore_file = "space_highscore.txt"
        self.high_score = self.load_highscore()
        
        self.reset_game()
        self.state = "MENU"
        self.fire_cooldown = 0

    def load_highscore(self):
        if os.path.exists(self.highscore_file):
            try:
                with open(self.highscore_file, "r") as f:
                    return int(f.read().strip())
            except:
                pass
        return 0

    def save_highscore(self):
        try:
            with open(self.highscore_file, "w") as f:
                f.write(str(self.high_score))
        except:
            pass

    def reset_game(self):
        self.player = Player()
        self.lasers = []
        self.meteors = []
        self.powerups = []
        self.score = 0
        self.meteor_spawn_timer = 0
        self.powerup_spawn_timer = 0
        self.meteor_spawn_rate = 60 # Frames between spawns
        self.fire_cooldown = 0

    def run(self):
        while True:
            self.handle_events()
            if self.state == "PLAYING":
                self.update_logic()
            self.draw_screen()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if self.state == "MENU":
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                        self.state = "PLAYING"
                elif self.state == "GAMEOVER":
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                        self.state = "PLAYING"
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "MENU"
                elif self.state == "PLAYING":
                    if event.key == pygame.K_SPACE:
                        self.fire_laser()
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "PAUSED"
                elif self.state == "PAUSED":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "PLAYING"
                    elif event.key == pygame.K_SPACE:
                        self.state = "PLAYING"

    def fire_laser(self):
        if self.fire_cooldown > 0:
            return
        play_sound(SOUND_LASER)
        laser = Laser(self.player.x + self.player.width // 2, self.player.y)
        self.lasers.append(laser)
        self.fire_cooldown = 3 if self.player.rapid_fire_timer > 0 else 8

    def apply_powerup(self, powerup):
        if powerup.type == "shield":
            self.player.shield_timer = 500
        elif powerup.type == "rapid":
            self.player.rapid_fire_timer = 500
        elif powerup.type == "heal":
            if self.player.health < 3:
                self.player.health += 1
            else:
                self.score += 25

    def update_logic(self):
        keys = pygame.key.get_pressed()
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1

        if self.player.shield_timer > 0:
            self.player.shield_timer -= 1
        if self.player.rapid_fire_timer > 0:
            self.player.rapid_fire_timer -= 1

        if self.fire_cooldown > 0:
            self.fire_cooldown -= 1
        if keys[pygame.K_SPACE]:
            self.fire_laser()
        
        if dx != 0:
            self.player.move(dx)
            
        # Update Lasers
        for laser in self.lasers[:]:
            laser.update()
            if laser.y < 0:
                self.lasers.remove(laser)

        # Spawn meteors and powerups
        self.meteor_spawn_timer += 1
        self.powerup_spawn_timer += 1

        if self.meteor_spawn_timer >= self.meteor_spawn_rate:
            self.meteor_spawn_timer = 0
            self.meteors.append(Meteor())
            if self.meteor_spawn_rate > 20:
                self.meteor_spawn_rate -= 1 # Gradually gets harder

        if self.powerup_spawn_timer >= 420:
            self.powerup_spawn_timer = 0
            self.powerups.append(PowerUp())

        # Update Power Ups
        for powerup in self.powerups[:]:
            powerup.update()
            if powerup.y > WINDOW_HEIGHT:
                self.powerups.remove(powerup)
                continue

            if self.player.rect.colliderect(powerup.rect):
                self.apply_powerup(powerup)
                self.particle_sys.spawn(powerup.x + powerup.size // 2, powerup.y + powerup.size // 2, 18)
                self.powerups.remove(powerup)

        # Update Meteors & Collisions
        player_hitbox = self.player.rect.inflate(-10, -10)
        for meteor in self.meteors[:]:
            meteor.update()
            if meteor.y > WINDOW_HEIGHT:
                self.meteors.remove(meteor)
                continue

            # Meteor hits player
            if player_hitbox.colliderect(meteor.rect):
                if self.player.shield_timer > 0:
                    play_sound(SOUND_EXPLOSION)
                    self.particle_sys.spawn(meteor.x + meteor.size//2, meteor.y + meteor.size//2, 18)
                    self.meteors.remove(meteor)
                    self.player.shield_timer = 0
                    continue

                play_sound(SOUND_EXPLOSION)
                self.particle_sys.spawn(meteor.x + meteor.size//2, meteor.y + meteor.size//2, 30)
                self.meteors.remove(meteor)
                self.player.health -= 1
                if self.player.health <= 0:
                    play_sound(SOUND_GAMEOVER)
                    if self.score > self.high_score:
                        self.high_score = self.score
                        self.save_highscore()
                    self.state = "GAMEOVER"
                continue

            # Laser hits meteor
            for laser in self.lasers[:]:
                if laser.rect.colliderect(meteor.rect):
                    play_sound(SOUND_EXPLOSION)
                    self.particle_sys.spawn(meteor.x + meteor.size//2, meteor.y + meteor.size//2, 20)
                    if meteor in self.meteors: self.meteors.remove(meteor)
                    if laser in self.lasers: self.lasers.remove(laser)
                    self.score += 10
                    break

        self.particle_sys.update()
        self.starfield.update()

    def draw_screen(self):
        self.screen.fill(COLOR_BG)
        self.starfield.draw(self.screen)
        
        if self.state in ["PLAYING", "GAMEOVER", "PAUSED"]:
            for laser in self.lasers:
                laser.draw(self.screen)
            for meteor in self.meteors:
                meteor.draw(self.screen)
            for powerup in self.powerups:
                powerup.draw(self.screen)
            self.particle_sys.draw(self.screen)
            if self.state == "PLAYING" or self.state == "PAUSED" or (self.state == "GAMEOVER" and self.player.health > 0):
                self.player.draw(self.screen)

            # Draw UI
            score_txt = self.font_ui.render(f"SCORE: {self.score}", True, COLOR_TEXT_LIGHT)
            self.screen.blit(score_txt, (10, 10))

            lives_txt = self.font_ui.render(f"LIVES: {self.player.health}", True, (244, 63, 94))
            self.screen.blit(lives_txt, (WINDOW_WIDTH - 120, 10))

            if self.player.shield_timer > 0:
                shield_txt = self.font_ui.render("SHIELD", True, COLOR_POWERUP)
                self.screen.blit(shield_txt, (10, 40))
            if self.player.rapid_fire_timer > 0:
                rapid_txt = self.font_ui.render("RAPID FIRE", True, COLOR_POWERUP_ALT)
                self.screen.blit(rapid_txt, (10, 70))

            if self.state == "PAUSED":
                overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 150))
                self.screen.blit(overlay, (0, 0))

                title = self.font_main.render("PAUSED", True, COLOR_PLAYER)
                self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 200))

                sub = self.font_ui.render("Tekan ESC atau SPASI untuk Lanjut", True, COLOR_TEXT_LIGHT)
                self.screen.blit(sub, (WINDOW_WIDTH//2 - sub.get_width()//2, 260))

        if self.state == "MENU":
            title = self.font_main.render("SPACE SHOOTER", True, COLOR_PLAYER)
            self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 200))
            
            sub = self.font_ui.render("Tekan SPASI untuk Memulai", True, COLOR_TEXT_LIGHT)
            self.screen.blit(sub, (WINDOW_WIDTH//2 - sub.get_width()//2, 260))
            
            hs = self.font_ui.render(f"High Score: {self.high_score}", True, COLOR_EXPLOSION)
            self.screen.blit(hs, (WINDOW_WIDTH//2 - hs.get_width()//2, 300))
            
        elif self.state == "GAMEOVER":
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            self.screen.blit(overlay, (0, 0))
            
            title = self.font_main.render("GAME OVER", True, COLOR_LASER)
            self.screen.blit(title, (WINDOW_WIDTH//2 - title.get_width()//2, 200))
            
            score_res = self.font_ui.render(f"Final Score: {self.score}", True, COLOR_TEXT_LIGHT)
            self.screen.blit(score_res, (WINDOW_WIDTH//2 - score_res.get_width()//2, 260))
            
            sub = self.font_ui.render("Tekan SPASI untuk Ulangi", True, COLOR_TEXT_LIGHT)
            self.screen.blit(sub, (WINDOW_WIDTH//2 - sub.get_width()//2, 320))
            
        pygame.display.flip()

if __name__ == "__main__":
    Game().run()
