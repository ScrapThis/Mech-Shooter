import pygame
import sys
import random
import asyncio
import json
import math  # For boss waving

# Setup
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Mech Shooter - Varied Waves")
clock = pygame.time.Clock()

# Colors
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

# Load images (circle mask for enemies/boss/mech, rectangle for background/bullet)
def load_image(name, size, convert_alpha=False, make_circle=False):
    for filename in [f"{name}.png", name]:
        try:
            img = pygame.image.load(filename)
            if convert_alpha:
                img = img.convert_alpha()
            img = pygame.transform.scale(img, size)
            if make_circle:
                mask_surface = pygame.Surface(size, pygame.SRCALPHA)
                radius = size[0] // 2
                pygame.draw.circle(mask_surface, (255, 255, 255, 255), (radius, radius), radius)
                img.blit(mask_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                print(f"{filename} loaded, scaled to {size}, and masked as circle!")
            else:
                print(f"{filename} loaded and scaled to {size} as rectangle!")
            return img
        except Exception as e:
            print(f"Failed to load {filename}: {e}")
    return None

background = load_image("background", (WINDOW_WIDTH, WINDOW_HEIGHT), make_circle=False)
mech_img = load_image("mech", (64, 64), convert_alpha=True, make_circle=True)
bullet_img = load_image("bullet", (8, 16), convert_alpha=True, make_circle=False)
boss_img = load_image("boss", (100, 100), convert_alpha=True, make_circle=True)
enemy1_img = load_image("enemy1", (32, 32), convert_alpha=True, make_circle=True)
enemy2_img = load_image("enemy2", (32, 32), convert_alpha=True, make_circle=True)
enemy3_img = load_image("enemy3", (32, 32), convert_alpha=True, make_circle=True)
enemy4_img = load_image("enemy4", (32, 32), convert_alpha=True, make_circle=True)
enemy5_img = load_image("enemy5", (32, 32), convert_alpha=True, make_circle=True)
enemy6_img = load_image("enemy6", (32, 32), convert_alpha=True, make_circle=True)
enemy7_img = load_image("enemy7", (32, 32), convert_alpha=True, make_circle=True)
enemy8_img = load_image("enemy8", (32, 32), convert_alpha=True, make_circle=True)
enemy9_img = load_image("enemy9", (32, 32), convert_alpha=True, make_circle=True)

enemy_images = [enemy1_img, enemy2_img, enemy3_img, enemy4_img, enemy5_img,
                enemy6_img, enemy7_img, enemy8_img, enemy9_img]

# Player (Mech)
mech_x, mech_y = WINDOW_WIDTH // 2, WINDOW_HEIGHT - 64
mech_speed = 5
mech = pygame.Rect(mech_x, mech_y, 64 if mech_img else 30, 64 if mech_img else 30)
shoot_timer = 0
shoot_delay = 10

# Bullets
bullets = []
bullet_speed = -10

# Enemies and Levels
enemies = []
boss = None
boss_hits = 0
level = 1
total_kills = 0
max_levels = 10
boss_phase = 0  # For boss movement

def spawn_level(level):
    global enemies, boss, boss_hits
    enemies.clear()
    if level < max_levels:
        for _ in range(100):
            radius = 16
            if level % 4 == 1 or level % 4 == 3:  # Down (1, 3, 5, 7, 9)
                x = random.randint(0, WINDOW_WIDTH - 32)
                y = random.randint(-WINDOW_HEIGHT, -50)
                speed = [0, random.uniform(1, 3)]  # [x_speed, y_speed]
            elif level % 4 == 2:  # Right to Left (2, 6)
                x = WINDOW_WIDTH + random.randint(0, 100)
                y = random.randint(0, WINDOW_HEIGHT // 2)
                speed = [-random.uniform(1, 3), 0]
            elif level % 4 == 0:  # Left to Right (4, 8)
                x = -random.randint(0, 100)
                y = random.randint(0, WINDOW_HEIGHT // 2)
                speed = [random.uniform(1, 3), 0]
            enemies.append({"x": x, "y": y, "radius": radius, "speed": speed})
    elif level == max_levels:
        boss = {"x": WINDOW_WIDTH // 2 - 50, "y": 50, "radius": 50, "x_speed": 2, "y_phase": 0}
        boss_hits = 0

# Initial level
spawn_level(level)

# High scores
def load_high_scores():
    try:
        with open("high_scores.json", "r") as f:
            return json.load(f)
    except:
        return [0, 0, 0, 0, 0]

def save_high_scores(scores):
    with open("high_scores.json", "w") as f:
        json.dump(scores, f)

high_scores = load_high_scores()

# Game loop
async def main():
    global running, shoot_timer, level, total_kills, boss, boss_hits, boss_phase
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and mech.left > 0:
            mech.x -= mech_speed
        if keys[pygame.K_RIGHT] and mech.right < WINDOW_WIDTH:
            mech.x += mech_speed

        if keys[pygame.K_SPACE]:
            shoot_timer -= 1
            if shoot_timer <= 0:
                bullet_x = mech.centerx - (4 if bullet_img else 2)
                bullet_y = mech.top
                bullets.append(pygame.Rect(bullet_x, bullet_y, 8 if bullet_img else 4, 16 if bullet_img else 10))
                shoot_timer = shoot_delay
        else:
            shoot_timer = 0

        for bullet in bullets[:]:
            bullet.y += bullet_speed
            if bullet.y < 0:
                bullets.remove(bullet)

        if level < max_levels:
            for enemy in enemies[:]:
                enemy["x"] += enemy["speed"][0]
                enemy["y"] += enemy["speed"][1]
                if (enemy["speed"][1] > 0 and enemy["y"] > WINDOW_HEIGHT) or \
                   (enemy["speed"][0] < 0 and enemy["x"] < -enemy["radius"]) or \
                   (enemy["speed"][0] > 0 and enemy["x"] > WINDOW_WIDTH + enemy["radius"]):
                    enemies.remove(enemy)
        elif boss:
            # Boss yo-yo movement
            boss["x"] += boss["x_speed"]
            boss["y"] = 50 + math.sin(boss_phase) * 100  # Wave up/down
            boss_phase += 0.05
            if boss["x"] > WINDOW_WIDTH - 100:
                boss["x_speed"] = -2
            elif boss["x"] < 0:
                boss["x_speed"] = 2

        for bullet in bullets[:]:
            if level < max_levels:
                for enemy in enemies[:]:
                    bullet_center = (bullet.centerx, bullet.centery)
                    enemy_center = (enemy["x"] + enemy["radius"], enemy["y"] + enemy["radius"])
                    distance = ((bullet_center[0] - enemy_center[0]) ** 2 + (bullet_center[1] - enemy_center[1]) ** 2) ** 0.5
                    if distance < enemy["radius"] + 4:
                        bullets.remove(bullet)
                        enemies.remove(enemy)
                        total_kills += 1
                        break
            elif boss:
                boss_center = (boss["x"] + boss["radius"], boss["y"] + boss["radius"])
                bullet_center = (bullet.centerx, bullet.centery)
                distance = ((bullet_center[0] - boss_center[0]) ** 2 + (bullet_center[1] - boss_center[1]) ** 2) ** 0.5
                if distance < boss["radius"] + 4:
                    bullets.remove(bullet)
                    boss_hits += 1
                    if boss_hits >= 100:
                        boss = None
                        total_kills += 50
                        level += 1

        if level < max_levels and not enemies:
            level += 1
            spawn_level(level)
            print(f"Level {level} started!")
        elif level == max_levels and not boss and not enemies:
            running = False

        if background:
            screen.blit(background, (0, 0))
        else:
            screen.fill(BLACK)
        if mech_img:
            screen.blit(mech_img, mech)
        else:
            pygame.draw.polygon(screen, GRAY, [
                (mech.x + 15, mech.y), (mech.x, mech.y + 30), (mech.x + 30, mech.y + 30)
            ])
        for bullet in bullets:
            if bullet_img:
                screen.blit(bullet_img, bullet)
            else:
                pygame.draw.rect(screen, WHITE, bullet)
        if level < max_levels:
            enemy_img_for_level = enemy_images[level - 1]
            for enemy in enemies:
                if enemy_img_for_level:
                    screen.blit(enemy_img_for_level, (enemy["x"], enemy["y"]))
                else:
                    pygame.draw.circle(screen, RED, (int(enemy["x"] + enemy["radius"]), int(enemy["y"] + enemy["radius"])), enemy["radius"])
        elif boss:
            if boss_img:
                screen.blit(boss_img, (boss["x"], boss["y"]))
            else:
                pygame.draw.circle(screen, YELLOW, (int(boss["x"] + boss["radius"]), int(boss["y"] + boss["radius"])), boss["radius"])
        font = pygame.font.SysFont(None, 36)
        level_text = font.render(f"Level: {level}", True, WHITE)
        kills_text = font.render(f"Kills: {total_kills}", True, WHITE)
        screen.blit(level_text, (10, 10))
        screen.blit(kills_text, (10, 40))
        pygame.display.flip()

        clock.tick(60)
        await asyncio.sleep(0)

    high_scores.append(total_kills)
    high_scores.sort(reverse=True)
    high_scores = high_scores[:5]
    save_high_scores(high_scores)
    print(f"High Scores: {high_scores}")

# Run
asyncio.run(main())
pygame.quit()
print(f"Game Over! Final Kills: {total_kills}")