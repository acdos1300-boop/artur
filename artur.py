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
SND_EXT = (".ogg", ".wav", ".mp3")


def asset_files(exts):
    out = []
    try:
        for f in sorted(os.listdir(BASE)):
            if f.lower().endswith(exts):
                out.append(os.path.join(BASE, f))
    except Exception:
        pass
    return out


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


def force_foreground(hwnd):
    if not hwnd:
        return
    try:
        import ctypes
        u = ctypes.windll.user32
        k = ctypes.windll.kernel32
        u.ShowWindow(hwnd, 9)
        u.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
        fg = u.GetForegroundWindow()
        t1 = u.GetWindowThreadProcessId(fg, 0)
        t2 = k.GetCurrentThreadId()
        if t1 and t1 != t2:
            u.AttachThreadInput(t1, t2, True)
            u.BringWindowToTop(hwnd)
            u.SetForegroundWindow(hwnd)
            u.AttachThreadInput(t1, t2, False)
        else:
            u.SetForegroundWindow(hwnd)
    except Exception:
        pass


def ask():
    if TEST:
        return
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        if not messagebox.askyesno("DANCE.EXE", "Хочешь танцевать?", parent=root):
            messagebox.askyesno("DANCE.EXE", "Точно нет?", parent=root)
        root.destroy()
    except Exception:
        pass


def grab_desktop_pil():
    if TEST:
        return None
    try:
        from PIL import ImageGrab
        return ImageGrab.grab().convert("RGB")
    except Exception:
        return None


def init_audio(pygame):
    try:
        if pygame.mixer.get_init():
            pygame.mixer.quit()
    except Exception:
        pass
    try:
        pygame.mixer.init(44100, -16, 2, 1024)
        return True
    except Exception:
        pass
    for drv in ("directsound", "wasapi", "winmm"):
        try:
            os.environ["SDL_AUDIODRIVER"] = drv
            pygame.mixer.init(44100, -16, 2, 1024)
            return True
        except Exception:
            continue
    return False


class Flyer:
    def __init__(self, base_img, pygame, sw, sh):
        size = int(sh * random.uniform(0.24, 0.34))
        bw, bh = base_img.get_size()
        sc = size / max(bw, bh)
        self.img = pygame.transform.smoothscale(base_img, (max(1, int(bw * sc)), max(1, int(bh * sc))))
        self.r = max(self.img.get_size()) * 0.5
        self.sw, self.sh = sw, sh
        self.x = random.uniform(self.r, sw - self.r)
        self.y = random.uniform(self.r, sh - self.r)
        sp = random.uniform(230, 440)
        a = random.uniform(0, math.tau)
        self.vx, self.vy = math.cos(a) * sp, math.sin(a) * sp
        self.rot = random.uniform(0, 360)
        self.vr = random.uniform(-45, 45)
        self._bucket = None
        self._surf = pygame.transform.rotate(self.img, self.rot)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rot += self.vr * dt
        if self.x < self.r:
            self.x = self.r
            self.vx = abs(self.vx)
        elif self.x > self.sw - self.r:
            self.x = self.sw - self.r
            self.vx = -abs(self.vx)
        if self.y < self.r:
            self.y = self.r
            self.vy = abs(self.vy)
        elif self.y > self.sh - self.r:
            self.y = self.sh - self.r
            self.vy = -abs(self.vy)

    def draw(self, screen, pygame):
        b = int(self.rot) // 5
        if b != self._bucket:
            self._bucket = b
            self._surf = pygame.transform.rotate(self.img, self.rot)
        screen.blit(self._surf, self._surf.get_rect(center=(int(self.x), int(self.y))))


def main():
    ask()
    pil_desk = grab_desktop_pil()
    vol = get_volume_ctl()
    hold_volume(vol, VOLUME)

    if TEST:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    else:
        os.environ["SDL_VIDEO_MINIMIZE_ON_FOCUS_LOSS"] = "0"
        os.environ["SDL_VIDEO_WINDOW_POS"] = "0,0"
    import pygame
    pygame.init()
    audio_ok = False if TEST else init_audio(pygame)

    if TEST:
        screen = pygame.display.set_mode((1280, 720))
    else:
        info = pygame.display.Info()
        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
        try:
            pygame.event.set_grab(True)
        except Exception:
            pass
    sw, sh = screen.get_size()
    pygame.display.set_caption("ARTUR")
    pygame.mouse.set_visible(False)

    hwnd = None
    if not TEST:
        try:
            hwnd = pygame.display.get_wm_info().get("window")
        except Exception:
            hwnd = None
    force_foreground(hwnd)

    tiles = []
    if pil_desk is not None:
        try:
            surf = pygame.image.fromstring(pil_desk.tobytes(), pil_desk.size, "RGB")
            desk = pygame.transform.smoothscale(surf, (sw, sh)).convert()
            cols, rows = 8, 5
            tw, th = sw // cols, sh // rows
            for r in range(rows):
                for c in range(cols):
                    x, y = c * tw, r * th
                    w = tw if c < cols - 1 else sw - x
                    h = th if r < rows - 1 else sh - y
                    try:
                        sub = desk.subsurface((x, y, w, h)).copy()
                        sub.set_alpha(205)
                        tiles.append([sub, x, y, random.uniform(0, math.tau)])
                    except Exception:
                        pass
        except Exception:
            tiles = []

    base_imgs = []
    for p in asset_files(IMG_EXT):
        try:
            img = pygame.image.load(p).convert()
            bw, bh = img.get_size()
            m = (sh * 0.5) / max(bw, bh)
            if m < 1:
                img = pygame.transform.smoothscale(img, (int(bw * m), int(bh * m)))
            bw, bh = img.get_size()
            frame = pygame.Surface((bw + 16, bh + 16), pygame.SRCALPHA)
            frame.fill((255, 255, 255))
            frame.blit(img, (8, 8))
            base_imgs.append(frame)
        except Exception:
            pass
    if not base_imgs:
        s = pygame.Surface((420, 420), pygame.SRCALPHA)
        s.fill((255, 255, 255))
        f = pygame.font.SysFont("arial", 70, bold=True)
        tx = f.render("ARTUR", True, (210, 0, 70))
        s.blit(tx, tx.get_rect(center=(210, 210)))
        base_imgs.append(s)

    wav_songs = asset_files((".wav",))
    other_songs = asset_files((".ogg", ".mp3"))
    audio_mode = None
    if not TEST and sys.platform.startswith("win") and wav_songs:
        try:
            import winsound
            winsound.PlaySound(wav_songs[0], winsound.SND_FILENAME | winsound.SND_ASYNC)
            audio_mode = "winsound"
        except Exception:
            audio_mode = None
    if audio_mode is None and audio_ok and other_songs:
        try:
            pygame.mixer.music.load(other_songs[0])
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play(-1)
            audio_mode = "pygame"
        except Exception:
            audio_mode = None

    colors = [(170, 20, 200), (10, 90, 150), (30, 170, 60), (210, 20, 60), (240, 130, 0), (20, 40, 200)]
    flyers = [Flyer(random.choice(base_imgs), pygame, sw, sh) for _ in range(3)]
    clock = pygame.time.Clock()
    t = 0.0
    spawn = 0.0
    last_vol = -1.0
    last_focus = -1.0
    frames = 0
    running = True

    FOCUS_LOST = getattr(pygame, "WINDOWFOCUSLOST", -999)
    MINIMIZED = getattr(pygame, "WINDOWMINIMIZED", -998)

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        t += dt
        frames += 1

        if t - last_vol > 0.2:
            last_vol = t
            hold_volume(vol, VOLUME)
        if not TEST and t - last_focus > 0.05:
            last_focus = t
            force_foreground(hwnd)

        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN and e.key == pygame.K_q:
                mods = pygame.key.get_mods()
                if (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
                    running = False
            elif e.type == FOCUS_LOST or e.type == MINIMIZED:
                force_foreground(hwnd)
        if t >= DURATION:
            running = False

        beat = max(0.0, math.sin(t * math.pi * 4)) ** 4

        ci = int(t / 1.1) % len(colors)
        cn = (ci + 1) % len(colors)
        fr = (t / 1.1) % 1
        col = tuple(int(colors[ci][i] * (1 - fr) + colors[cn][i] * fr) for i in range(3))
        screen.fill(col)

        if tiles:
            gx = int(math.sin(t * 7) * (2 + 6 * beat))
            gy = int(math.cos(t * 6) * (2 + 6 * beat))
            for tl in tiles:
                sub, hx, hy, ph = tl
                amp = 5 + 17 * beat
                ox = int(math.sin(t * 11 + ph) * amp) + gx
                oy = int(math.cos(t * 9 + ph * 1.3) * amp) + gy
                screen.blit(sub, (hx + ox, hy + oy))

        spawn += dt
        if spawn > 2.2 and len(flyers) < 8:
            spawn = 0.0
            flyers.append(Flyer(random.choice(base_imgs), pygame, sw, sh))
        for fl in flyers:
            fl.update(dt)
            fl.draw(screen, pygame)

        pygame.display.flip()
        if TEST and frames > 240:
            running = False

    if audio_mode == "winsound":
        try:
            import winsound
            winsound.PlaySound(None, 0)
        except Exception:
            pass
    else:
        try:
            pygame.mixer.music.fadeout(300)
            pygame.time.wait(300)
        except Exception:
            pass
    pygame.quit()


if __name__ == "__main__":
    main()        
