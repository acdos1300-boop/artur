import os
import sys
import math
import random

TEST = "--test" in sys.argv

if getattr(sys, "frozen", False):
    BASE = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    BASE = os.path.dirname(os.path.abspath(__file__))

DURATION = 40
VOLUME = 0.6
IMG_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp")
SND_EXT = (".mp3", ".ogg", ".wav")


def get_volume_ctl():
    if TEST:
        return None
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        dev = AudioUtilities.GetSpeakers()
        iface = dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(iface, POINTER(IAudioEndpointVolume))
    except Exception:
        return None


def hold_volume(ctl, level):
    if not ctl:
        return
    try:
        ctl.SetMute(0, None)
        ctl.SetMasterVolumeLevelScalar(level, None)
    except Exception:
        pass


def files(folder, ext):
    out = []
    for root in (folder, os.path.join(folder, "photos"), os.path.join(folder, "music")):
        if os.path.isdir(root):
            out += [os.path.join(root, f) for f in sorted(os.listdir(root)) if f.lower().endswith(ext)]
    return out


PHOTOS = BASE
MUSIC = BASE


def ask():
    if TEST:
        return
    import tkinter as tk
    from tkinter import messagebox
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if not messagebox.askyesno("DANCE.EXE", "Хочешь танцевать?", parent=root):
        messagebox.askyesno("DANCE.EXE", "Точно нет?", parent=root)
    root.destroy()


def grab_desktop(w, h):
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab().convert("RGB").resize((w, h))
        import pygame
        return pygame.image.fromstring(img.tobytes(), img.size, "RGB")
    except Exception:
        return None


class Flyer:
    def __init__(self, img, sw, sh):
        self.base = img
        self.sw, self.sh = sw, sh
        self.size = random.uniform(0.28, 0.5) * sh
        self.x = random.uniform(0.2, 0.8) * sw
        self.y = random.uniform(0.2, 0.8) * sh
        sp = random.uniform(260, 520)
        a = random.uniform(0, math.tau)
        self.vx, self.vy = math.cos(a) * sp, math.sin(a) * sp
        self.rot = random.uniform(-20, 20)
        self.vr = random.uniform(-60, 60)
        self.t = random.uniform(0, 10)
        self.born = 0.0

    def update(self, dt):
        self.t += dt
        self.born = min(1.0, self.born + dt * 3)
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rot += self.vr * dt
        r = self.size * 0.45
        if self.x < r or self.x > self.sw - r:
            self.vx *= -1
            self.vr = random.uniform(-90, 90)
            self.x = max(r, min(self.sw - r, self.x))
        if self.y < r or self.y > self.sh - r:
            self.vy *= -1
            self.vr = random.uniform(-90, 90)
            self.y = max(r, min(self.sh - r, self.y))

    def draw(self, screen, pygame, beat):
        k = self.born * (1 + 0.08 * beat + 0.04 * math.sin(self.t * 7))
        bw, bh = self.base.get_size()
        scale = self.size * k / max(bw, bh)
        img = pygame.transform.rotozoom(self.base, self.rot, scale)
        rect = img.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(img, rect)


def main():
    ask()
    vol_ctl = get_volume_ctl()
    hold_volume(vol_ctl, VOLUME)
    if TEST:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    import pygame
    pygame.init()
    if TEST:
        screen = pygame.display.set_mode((1280, 720))
    else:
        info = pygame.display.Info()
        sw0, sh0 = info.current_w, info.current_h
        desk = grab_desktop(sw0 // 2, sh0 // 2)
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        try:
            pygame.event.set_grab(True)
        except Exception:
            pass
    sw, sh = screen.get_size()
    if TEST:
        desk = None
    pygame.display.set_caption("ARTUR")
    pygame.mouse.set_visible(False)

    photos = []
    for p in files(PHOTOS, IMG_EXT):
        try:
            img = pygame.image.load(p).convert_alpha()
            bw, bh = img.get_size()
            m = 700 / max(bw, bh)
            if m < 1:
                img = pygame.transform.smoothscale(img, (int(bw * m), int(bh * m)))
            frame = pygame.Surface((img.get_width() + 16, img.get_height() + 16), pygame.SRCALPHA)
            frame.fill((255, 255, 255))
            frame.blit(img, (8, 8))
            photos.append(frame)
        except Exception:
            pass
    if not photos:
        s = pygame.Surface((400, 400), pygame.SRCALPHA)
        s.fill((255, 255, 255))
        f = pygame.font.SysFont("arial", 60, bold=True)
        t = f.render("ARTUR", True, (200, 0, 80))
        s.blit(t, t.get_rect(center=(200, 200)))
        photos.append(s)

    songs = files(MUSIC, SND_EXT)
    random.shuffle(songs)
    song_i = 0

    def next_song():
        nonlocal song_i
        if not songs:
            return
        try:
            pygame.mixer.music.load(songs[song_i % len(songs)])
            pygame.mixer.music.play()
        except Exception:
            pass
        song_i += 1

    MUSIC_END = pygame.USEREVENT + 1
    try:
        pygame.mixer.music.set_endevent(MUSIC_END)
    except Exception:
        pass
    next_song()

    colors = [(170, 20, 200), (10, 90, 120), (30, 170, 40), (200, 20, 50), (240, 120, 0), (20, 40, 200)]
    flyers = [Flyer(random.choice(photos), sw, sh)]
    clock = pygame.time.Clock()
    t = 0.0
    spawn = 0.0
    frames = 0
    running = True
    tint = pygame.Surface((sw, sh))
    last_vol = -1.0

    while running:
        dt = min(clock.tick(60) / 1000, 0.05)
        t += dt
        frames += 1
        if t - last_vol > 0.2:
            last_vol = t
            hold_volume(vol_ctl, VOLUME)
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN and e.key == pygame.K_q:
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_CTRL and mods & pygame.KMOD_SHIFT:
                    running = False
            elif e.type == MUSIC_END:
                next_song()
        if t >= DURATION:
            running = False

        beat = max(0.0, math.sin(t * math.pi * 2 * 2)) ** 4

        ci = int(t / 1.2) % len(colors)
        cn = (ci + 1) % len(colors)
        f = (t / 1.2) % 1
        col = tuple(int(colors[ci][i] * (1 - f) + colors[cn][i] * f) for i in range(3))
        screen.fill(col)

        if desk is not None:
            ang = math.sin(t * 1.7) * 12
            zoom = 2.3 + 0.15 * math.sin(t * 2.3)
            d = pygame.transform.rotozoom(desk, ang, zoom)
            d.set_alpha(150)
            screen.blit(d, d.get_rect(center=(sw // 2 + int(math.sin(t * 3) * 40), sh // 2)))
            tint.fill(col)
            tint.set_alpha(90)
            screen.blit(tint, (0, 0))

        spawn += dt
        if spawn > 2.5 and len(flyers) < 12:
            spawn = 0
            flyers.append(Flyer(random.choice(photos), sw, sh))

        for fl in flyers:
            fl.update(dt)
            fl.draw(screen, pygame, beat)

        pygame.display.flip()
        if TEST and frames > 240:
            running = False

    try:
        pygame.mixer.music.fadeout(300)
        pygame.time.wait(300)
    except Exception:
        pass
    pygame.quit()
    if TEST:
        print("ok", frames, "frames,", len(flyers), "photos flying")


if __name__ == "__main__":
    main() 
