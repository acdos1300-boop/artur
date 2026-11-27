import os
import sys
import math
import random

TEST = "--test" in sys.argv

if getattr(sys, "frozen", False):
    BASE = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    BASE = os.path.dirname(os.path.abspath(__file__))

DURATION = 90
INTRO = 5
VOLUME = 0.9
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
        import ctypes
        from ctypes import POINTER, byref, c_void_p, c_float, c_int, c_long, c_wchar_p
        from ctypes import wintypes

        ole32 = ctypes.windll.ole32
        try:
            ole32.CoInitialize(None)
        except Exception:
            pass

        class GUID(ctypes.Structure):
            _fields_ = [("Data1", ctypes.c_uint32),
                        ("Data2", ctypes.c_uint16),
                        ("Data3", ctypes.c_uint16),
                        ("Data4", ctypes.c_ubyte * 8)]

        def guid(s):
            g = GUID()
            ole32.CLSIDFromString(c_wchar_p(s), byref(g))
            return g

        CLSID_ENUM = guid("{BCDE0395-E52F-467C-8E3D-C4579291692E}")
        IID_ENUM = guid("{A95664D2-9614-4F35-A746-DE8DB63617E6}")
        IID_EPV = guid("{5CDF2C82-841E-4546-9722-0CF74078229A}")
        CLSCTX_ALL = 23

        def call(pobj, idx, restype, argtypes, *args):
            vtbl_addr = ctypes.cast(pobj, POINTER(c_void_p))[0]
            arr = ctypes.cast(c_void_p(vtbl_addr), POINTER(c_void_p))
            fp = arr[idx]
            proto = ctypes.CFUNCTYPE(restype, c_void_p, *argtypes)
            return proto(fp)(pobj, *args)

        enum = c_void_p()
        if ole32.CoCreateInstance(byref(CLSID_ENUM), None, CLSCTX_ALL, byref(IID_ENUM), byref(enum)) != 0 or not enum.value:
            return None
        dev = c_void_p()
        if call(enum, 4, c_long, (c_int, c_int, POINTER(c_void_p)), 0, 0, byref(dev)) != 0 or not dev.value:
            return None
        epv = c_void_p()
        if call(dev, 3, c_long, (POINTER(GUID), wintypes.DWORD, c_void_p, POINTER(c_void_p)),
                byref(IID_EPV), CLSCTX_ALL, None, byref(epv)) != 0 or not epv.value:
            return None

        def apply(level):
            try:
                call(epv, 14, c_long, (c_int, c_void_p), 0, None)
                call(epv, 7, c_long, (c_float, c_void_p), c_float(level), None)
            except Exception:
                pass

        apply(VOLUME)
        return apply
    except Exception:
        return None


def set_volume_keys(pct):
    if TEST:
        return
    try:
        import ctypes
        import time
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        KEYEVENTF_KEYUP = 0x0002

        class KEYBDINPUT(ctypes.Structure):
            _fields_ = [("wVk", wintypes.WORD),
                        ("wScan", wintypes.WORD),
                        ("dwFlags", wintypes.DWORD),
                        ("time", wintypes.DWORD),
                        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))]

        class _I(ctypes.Union):
            _fields_ = [("ki", KEYBDINPUT)]

        class INPUT(ctypes.Structure):
            _anonymous_ = ("i",)
            _fields_ = [("type", wintypes.DWORD), ("i", _I)]

        def send(vk, up):
            inp = INPUT()
            inp.type = 1
            inp.ki = KEYBDINPUT(vk, 0, KEYEVENTF_KEYUP if up else 0, 0, None)
            user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

        def tap(vk):
            send(vk, False)
            send(vk, True)
            time.sleep(0.01)

        for _ in range(55):
            tap(0xAE)
        for _ in range(max(0, int(round(pct / 2.0)))):
            tap(0xAF)
    except Exception:
        try:
            u = ctypes.windll.user32
            for _ in range(55):
                u.keybd_event(0xAE, 0, 0, 0)
                u.keybd_event(0xAE, 0, 2, 0)
            for _ in range(max(0, int(round(pct / 2.0)))):
                u.keybd_event(0xAF, 0, 0, 0)
                u.keybd_event(0xAF, 0, 2, 0)
        except Exception:
            pass


def hold_volume(ctl, level):
    if ctl is None:
        return
    try:
        ctl(level)
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


def draw_intro(screen, pygame, sw, sh, t, big_font, mid_font, small_font):
    screen.fill((8, 0, 0) if random.random() > 0.06 else (32, 0, 0))
    pygame.draw.rect(screen, (150, 10, 16), (0, 0, sw, 10))
    pygame.draw.rect(screen, (150, 10, 16), (0, sh - 10, sw, 10))
    cx = sw // 2
    red = (235, 25, 25)
    ty = sh // 2 - int(sh * 0.28)
    tw = max(60, sh // 9)
    th = int(tw * 1.5)
    pygame.draw.polygon(screen, red, [(cx, ty), (cx - tw, ty + th), (cx + tw, ty + th)], max(6, sh // 120))
    bar_w = max(6, tw // 9)
    pygame.draw.rect(screen, red, (cx - bar_w // 2, ty + int(th * 0.34), bar_w, int(th * 0.32)))
    pygame.draw.circle(screen, red, (cx, ty + int(th * 0.80)), bar_w)
    jitter = random.randint(-5, 5) if random.random() < 0.3 else 0
    if random.random() > 0.08:
        for i, line in enumerate(("ВАШ КОМПЬЮТЕР", "ЗАБЛОКИРОВАН")):
            y = sh // 2 + 35 + i * big_font.get_height()
            shadow = big_font.render(line, True, (85, 0, 0))
            main = big_font.render(line, True, red)
            screen.blit(shadow, shadow.get_rect(center=(cx - 5 + jitter, y + 2)))
            screen.blit(main, main.get_rect(center=(cx + jitter, y)))
    if int(t * 4) % 2 == 0:
        sub = mid_font.render("ДОСТУП ЗАПРЕЩЁН", True, (255, 70, 70))
        screen.blit(sub, sub.get_rect(center=(cx, sh // 2 + 45 + 2 * big_font.get_height())))
    warn = small_font.render("НЕ ПЫТАЙТЕСЬ ЗАКРЫТЬ ОКНО", True, (175, 30, 30))
    screen.blit(warn, warn.get_rect(center=(cx, sh // 2 + 100 + 2 * big_font.get_height())))
    for _ in range(45):
        screen.fill((120, 0, 0), (random.randint(0, sw), random.randint(0, sh), 2, 2))


def main():
    ask()
    pil_desk = grab_desktop_pil()
    vol = get_volume_ctl()
    vol_stop = [False]
    if vol is not None:
        hold_volume(vol, VOLUME)
    elif not TEST:
        set_volume_keys(int(VOLUME * 100))
        import threading

        def _locker():
            import time
            while not vol_stop[0]:
                set_volume_keys(int(VOLUME * 100))
                for _ in range(25):
                    if vol_stop[0]:
                        break
                    time.sleep(0.1)

        threading.Thread(target=_locker, daemon=True).start()

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
    pygame.display.set_caption("DANCE")
    pygame.mouse.set_visible(False)

    hwnd = None
    if not TEST:
        try:
            hwnd = pygame.display.get_wm_info().get("window")
        except Exception:
            hwnd = None
    force_foreground(hwnd)

    desk = None
    if pil_desk is not None:
        try:
            surf = pygame.image.fromstring(pil_desk.tobytes(), pil_desk.size, "RGB")
            desk = pygame.transform.smoothscale(surf, (sw, sh)).convert()
            desk.set_alpha(205)
        except Exception:
            desk = None

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

    running = True
    FOCUS_LOST = getattr(pygame, "WINDOWFOCUSLOST", -999)
    MINIMIZED = getattr(pygame, "WINDOWMINIMIZED", -998)

    big_font = pygame.font.SysFont("arial", max(30, sh // 11), bold=True)
    mid_font = pygame.font.SysFont("arial", max(16, sh // 26), bold=True)
    small_font = pygame.font.SysFont("arial", max(13, sh // 40), bold=True)
    intro_clock = pygame.time.Clock()
    it = 0.0
    intro_vol = -1.0
    intro_limit = 0.3 if TEST else INTRO
    while it < intro_limit and running:
        d = min(intro_clock.tick(60) / 1000.0, 0.05)
        it += d
        if it - intro_vol > 0.05:
            intro_vol = it
            hold_volume(vol, VOLUME)
        if not TEST:
            force_foreground(hwnd)
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN and e.key == pygame.K_q:
                mods = pygame.key.get_mods()
                if (mods & pygame.KMOD_CTRL) and (mods & pygame.KMOD_SHIFT):
                    running = False
            elif e.type == FOCUS_LOST or e.type == MINIMIZED:
                force_foreground(hwnd)
        draw_intro(screen, pygame, sw, sh, it, big_font, mid_font, small_font)
        pygame.display.flip()

    wav_songs = asset_files((".wav",))
    other_songs = asset_files((".ogg", ".mp3"))
    audio_mode = None
    if not TEST and sys.platform.startswith("win") and wav_songs:
        try:
            import winsound
            winsound.PlaySound(wav_songs[0], winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP)
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
    frames = 0

    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        t += dt
        frames += 1

        if t - last_vol > 0.05:
            last_vol = t
            hold_volume(vol, VOLUME)
        if not TEST:
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

        if desk is not None:
            amp = 4 + 14 * beat
            ox = int(math.sin(t * 20) * amp)
            oy = int(math.cos(t * 17) * amp)
            screen.blit(desk, (ox, oy))

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

    vol_stop[0] = True
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
