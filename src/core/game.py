"""Ana dongu: sabit 60 kare, 480x270 ic yuzey, tam sayi olcekleme.

**Sabit adim, kare birimi.** Fizik her zaman 1/60'lik esit adimlarla ilerler.
Makine yavassa birden fazla adim yakalanir, hizliysa beklenir. `dt` tabanli
fizik yapilmaz - degisken adim combo penceresini bozar (CLAUDE.md 4).

**Olcekleme.** Her sey 480x270 yuzeye cizilir, sonra `pygame.transform.scale`
ile tam sayi katinda buyutulur. `smoothscale` YASAK - piksel art bulaniklasir.

**Hitstop burada yasar.** Vurus aninda birkac kare fizik ve animasyon durur,
cizim surer. `game.hitstop(frames)` cagirmak yeterli; tum sahneler yararlanir.
Bu, en yuksek getirili 15 satirlik kod (docs/dovus-sistemi.md 5).
"""
from __future__ import annotations

import time
from pathlib import Path

import pygame

from src.art import palette, postfx
from src.audio import synth
from src.audio.mixer import AudioMixer
from src.config import (
    FPS, INTERNAL_HEIGHT, INTERNAL_WIDTH, MAX_CATCHUP_FRAMES,
)
from src.core.input import Action, InputManager
from src.core.scene import SceneManager
from src.systems.settings import Settings
from src.ui import cursor, i18n

WINDOW_TITLE = "Legend of Rey"
MIN_SCALE = 1
MAX_SCALE = 8
SCALE_SCREEN_MARGIN = 80        # Pencere modunda ekran kenarina birakilan pay


def viewport_for(width: int, height: int) -> tuple[int, pygame.Rect]:
    """Verilen ekran icin (olcek, ortalanmis dikdortgen).

    Olcek **daima tam sayi**: piksel art kesirli olcekte titrer ve bulanir.
    Artan yer siyah bant olarak kalir - gerdirmek bozmaktan iyidir demiyoruz,
    bant birakmak dogru olan.

    Sahne disinda tutuldu ki tam ekran matematigi bir pencere acmadan
    dogrulanabilsin (tests/test_window.py).
    """
    scale = max(MIN_SCALE,
                min(width // INTERNAL_WIDTH, height // INTERNAL_HEIGHT))
    view_w, view_h = INTERNAL_WIDTH * scale, INTERNAL_HEIGHT * scale
    return scale, pygame.Rect((width - view_w) // 2, (height - view_h) // 2,
                              view_w, view_h)


def desktop_size() -> tuple[int, int]:
    """Gercek masaustu cozunurlugu.

    `pygame.display.Info()` **bunun icin kullanilamaz**: bir pencere
    acildiktan sonra masaustunu degil o anki kipi doner.
    `get_desktop_sizes()` kipten bagimsiz.

    Sahne disinda tutuldu ki `tests/test_display.py` dogrulayabilsin.
    """
    try:
        sizes = pygame.display.get_desktop_sizes()
        if sizes and sizes[0][0] > 0 and sizes[0][1] > 0:
            return sizes[0]
    except (pygame.error, AttributeError):
        pass
    return (INTERNAL_WIDTH * 3, INTERNAL_HEIGHT * 3)


class Game:
    def __init__(self, settings: Settings | None = None) -> None:
        # Mixer formati alt sistem acilmadan ONCE kilitlenir (44.1kHz mono) -
        # sonradan cagrilirsa platforma gore degisen bir varsayimla kalirdik.
        synth.init_mixer()

        # **`pygame.init()` CAGRILMIYOR.** O cagri BUTUN alt sistemleri
        # aciyor, joystick dahil - ve joystick taramasi bu makinede
        # **40.30 saniye** suruyor (olculdu, sonunda sifir kol buluyor):
        #
        #     display.init     0.00 sn
        #     font.init        0.00 sn
        #     joystick.init   40.30 sn   <-- burada
        #     mixer.init       0.00 sn
        #
        # Sebep sistemde: SDL'in cihaz taramasi bozuk bir surucude
        # (Arda'nin tespiti: NGENUITY/HyperX) takilip zaman asimina
        # dusuyor. Yedi ayri SDL ayari denendi (HIDAPI, RAWINPUT, WGI,
        # DIRECTINPUT, XINPUT, THREAD), hicbiri degistirmedi - sure her
        # seferinde 40.3 saniye, yani sabit bir zaman asimi.
        #
        # Oyunun bunu beklemesi gerekmiyor: klavye ve fare hazir, kol
        # `JOYDEVICEADDED` ile zaten sonradan da yakalaniyor
        # (`input.py`). Bu yuzden yalnizca gereken alt sistemler
        # aciliyor; joystick arka planda (`InputState`).
        pygame.display.init()
        pygame.font.init()
        # **Ses alt sistemi elle aciliyor** ve bu satiri unutmak butun
        # oyunun sesini kesti (Arda, 30.08.2026: *"main.py ile
        # calistirdigimda oyunun seslerini duyamiyorum"*).
        #
        # `synth.init_mixer()` yalnizca `pre_init` yapiyor - formati
        # secer, alt sistemi ACMAZ. Acan sey `pygame.init()` idi ve o
        # cagri joystick yuzunden kaldirildi. Yukaridaki olcum
        # tablosunda "mixer.init 0.00 sn" yaziyor; olcup eklemeyi
        # atlamisim.
        #
        # Ses cihazi olmayan bir makinede oyun **calismaya devam
        # etmeli**: mixer acilamazsa `AudioMixer` sessiz calisiyor.
        try:
            pygame.mixer.init()
        except pygame.error as exc:
            print(f"[ses] mixer acilamadi, sessiz devam: {exc}")
        self.settings = settings or Settings()
        self.settings.on_change(self._on_setting_changed)
        # Gorev 10: gercek kaydedilmis ses yok, dalga formlari koddan
        # sentezleniyor (`src/audio/`) - CLAUDE.md 6'nin sprite ilkesiyle
        # ayni. `AudioMixer` kendi paylasilan onbellegini kullanir, burada
        # yalnizca ayarlara (hacim) erisim icin bir ornek tutuluyor.
        self.audio = AudioMixer(self.settings)
        # Kayitli dili **arayuz kurulmadan once** uygula: menuler kurulurken
        # metinleri o anki dilden cozuyor.
        self._apply_language(self.settings.get("language", i18n.DEFAULT_LANGUAGE))
        # Renk korlugu modu da **sprite/tileset hic uretilmeden once**
        # uygulanir - sonradan degisirse _on_setting_changed onbellekleri
        # temizler ve bir sonraki cizimde yeniden uretilirler.
        palette.set_mode(self.settings.get("colorblind", "none"))

        self.input = InputManager(self.settings.get("bindings"),
                                  self.settings.get("pad_bindings"))
        # Kayitli kol ayarini uygula. **Acilis yolunda 40 saniye demek** -
        # ama oyuncu bunu bilerek acti ve kolunu kullanmak istiyor. Kapali
        # (varsayilan) ise hicbir bedel yok.
        if self.settings.get("gamepad", False):
            self.input.set_gamepad_enabled(True)
        self.scenes = SceneManager(self)

        self.running = False
        self.debug_overlay = False
        # F4 uc kip arasinda gezer:
        #   sprite     - normal oyun
        #   silhouette - siluet testi: sprite tek renge iner, okunurluk sinavi
        #   box        - "kutularla oyna": sanat tamamen kalkar, dovusun kendisi
        #                eglenceli mi diye bakilir (DEVIR gorev 1)
        self.render_modes = ("sprite", "silhouette", "box")
        self.render_mode = "sprite"
        self.last_ui_sound = ""      # Gorev 10'da ses sistemine baglanacak

        # --- Zaman ----------------------------------------------------------
        self.clock = pygame.time.Clock()
        self.frame = 0                   # Oyun karesi (donmalarda ilerlemez)
        # Muzik kisilma orani 0..1. Sahne doldurur, ses sistemi (Gorev 10)
        # okuyacak. Simdiden burada durmasi, o gun sahneleri tekrar
        # dolasmak gerekmemesi demek - dikis hazir, govde bos.
        # Muzik yonetmeni - baglama gore parca secer
        # (`src/audio/music.py`). `music_hush` bir donem doldurulup hic
        # okunmuyordu; artik `update()` her kare onu yonetmene veriyor.
        from src.audio.music import MusicDirector
        self.music = MusicDirector(self.settings)
        self.music_hush = 0.0
        self.real_frame = 0              # Gercek kare (asla durmaz)
        self.fps = 0.0
        self._accumulator = 0.0
        self._last_time = time.perf_counter()
        self._hitstop_frames = 0

        # --- Ekran ----------------------------------------------------------
        # Pencere once acilir: convert()/convert_alpha() bir ekran bicimi
        # olmadan calismaz ve pygame hata firlatir.
        self.screen: pygame.Surface | None = None
        self.scale = 1
        # Gorunumun hangi ekran boyutuna gore hesaplandigi -
        # her karede karsilastiriliyor (bkz. `_render`).
        self._viewport_for_size = (0, 0)
        self.viewport = pygame.Rect(0, 0, INTERNAL_WIDTH, INTERNAL_HEIGHT)
        self._create_window()
        self.canvas = pygame.Surface(
            (INTERNAL_WIDTH, INTERNAL_HEIGHT)).convert_alpha()
        # Isletim sisteminin varsayilan oku bu oyunun piksel-art diline
        # uymuyor - kendi imlecimizi ciziyoruz (src/ui/cursor.py), OS
        # oku bir daha hic gorunmuyor.
        pygame.mouse.set_visible(False)

    # --- Pencere ------------------------------------------------------------
    def _best_scale(self) -> int:
        """Pencere modunda masaustune sigan en buyuk tam sayi olcek.

        **`pygame.display.Info()` KULLANILMAZ.** O cagri bir pencere
        acildiktan sonra masaustunu degil **o anki kipi** doner - yani
        pencerenin kendi boyutunu. Olcegi ondan hesaplayinca her ayar
        degisimi pencereyi bir kat daha kucultuyordu:

            1920 -> olcek 3 -> pencere 1440 -> olcek 2 -> pencere 960 -> ...

        Arda bunu canli oynanista buldu (29.08.2026): ayari degistirince
        pencere kuculuyor ve arayuz kirpiliyordu.

        `get_desktop_sizes()` gercek masaustunu veriyor ve kipten
        etkilenmiyor.
        """
        width, height = desktop_size()
        available_h = height - SCALE_SCREEN_MARGIN
        scale = min(width // INTERNAL_WIDTH, available_h // INTERNAL_HEIGHT)
        return max(MIN_SCALE, min(scale, MAX_SCALE))

    def _create_window(self) -> None:
        """Pencereyi kurar.

        **`pygame.SCALED` KULLANILMAZ.** O bayrak pygame'in kendi olceklemesini
        devreye sokar ve o olcek tam sayi olmak zorunda degildir: 1920x1080
        ekranda mantiksal 1440x810 yuzey 1.333x gerilir, piksel art bozulur.
        Ustelik `screen.get_size()` fiziksel degil **mantiksal** boyutu doner,
        yani viewport hesabi gercek ekrani hic gormez.

        Bunun yerine olcegi kendimiz hesapliyoruz (`_recompute_viewport`):
        daima tam sayi kat, ortalanmis, artan yer siyah bant. 480x270 icin
        1920x1080 tam 4x - bu makinede tam ekran hic bant birakmiyor.
        """
        fullscreen = bool(self.settings.get("fullscreen", False))
        if fullscreen:
            # **Kenarliksiz pencere, gercek tam ekran DEGIL.**
            #
            # `pygame.FULLSCREEN` SDL'in ozel (exclusive) kipini aciyor ve
            # o kip ekran modunu gercekten degistiriyor. Windows'ta bu
            # surucuye gore saniyeler surebiliyor, bazen hic donmuyor -
            # Arda'nin "ayari degistirince oyun donuyor" bildiriminin
            # ikinci sebebi bu.
            #
            # Masaustu boyutunda kenarliksiz bir pencere ayni gorunuyu
            # veriyor ama mod degisimi YOK: gecis aninda, alt-tab
            # calisiyor, surucu kilitlenmesi riski ortadan kalkiyor.
            flags = pygame.NOFRAME
            size = desktop_size()
        else:
            flags = pygame.RESIZABLE
            configured = int(self.settings.get("scale") or 0)
            scale = configured or self._best_scale()
            size = (INTERNAL_WIDTH * scale, INTERNAL_HEIGHT * scale)

        # **vsync YALNIZCA ilk pencerede isteniyor.**
        #
        # Tekrarli `set_mode(..., vsync=1)` pygame-ce 2.5.8'de SEGFAULT
        # veriyor - ikinci cagrida. Bu LORE'a ozel degil, saf pygame ile
        # de uretiliyor:
        #
        #     for i in range(6):
        #         pygame.display.set_mode((960,540), RESIZABLE, vsync=1)
        #         pygame.display.set_mode((1024,768), NOFRAME, vsync=1)
        #     -> 2. turda "pygame parachute: Segmentation Fault"
        #
        # Ayni dongu `vsync` olmadan sekiz tur sorunsuz donuyor. Arda'nin
        # "ayari degistirince oyun donuyor" bildiriminin ucuncu ve en sert
        # sebebi buydu: surec cokuyor ama ses is parcacigi bir sure daha
        # calmaya devam ediyor - ekrandan tam olarak "dondu" gibi
        # gorunuyor.
        #
        # Bedeli: vsync ayari **bir sonraki acilista** etkili oluyor.
        # Cokmeyen bir oyun, aninda uygulanan bir ayardan onemli.
        first_window = self.screen is None
        vsync = 1 if (first_window and self.settings.get("vsync", True)) else 0
        try:
            self.screen = pygame.display.set_mode(size, flags, vsync=vsync)
        except pygame.error:
            # vsync bazi surucularde reddedilir; onsuz tekrar dene.
            self.screen = pygame.display.set_mode(size, flags)

        pygame.display.set_caption(WINDOW_TITLE)

        # **Onbellekleri at.** Uretilen her yuzey `convert()` gormus ve
        # donusum O ANKI ekranin piksel bicimine gore yapilmis; ekran
        # yeniden kurulunca hepsi bayatliyor. Pygame bunu hata olarak
        # bildirmiyor, sessizce her blit'te tek tek donusturuyor - karede
        # yuzlerce blit oldugu icin sonuc "donma" gibi gorunuyor.
        #
        # Bu, Arda'nin bildirdigi donmanin BIRINCI sebebiydi.
        from src.art import caches
        caches.invalidate_all()

        self._recompute_viewport()



    def _recompute_viewport(self) -> None:
        if self.screen is None:
            return
        size = self.screen.get_size()
        self._viewport_for_size = size
        self.scale, self.viewport = viewport_for(*size)

    def toggle_fullscreen(self) -> None:
        # `Settings.set` degisiklik olayini tetikler, o da pencereyi kurar.
        self.settings.set("fullscreen",
                          not self.settings.get("fullscreen", False))

    def _on_setting_changed(self, key: str, value: object) -> None:
        """Ayar degisince aninda uygula - 'Kaydet' butonu yok."""
        if key == "gamepad":
            # Acmak 40 saniye blokluyor (bkz. `InputState`). Ayarlar
            # ekrani bu cagridan once uyari yazisini ciziyor.
            self.input.set_gamepad_enabled(bool(value))
        elif key in ("fullscreen", "scale", "vsync"):
            self._create_window()
        elif key == "bindings" and isinstance(value, dict):
            self.input.apply_bindings(value)
        elif key == "pad_bindings" and isinstance(value, dict):
            self.input.apply_bindings(value, gamepad=True)
        elif key == "language" and isinstance(value, str):
            self._apply_language(value)
        elif key == "colorblind" and isinstance(value, str):
            palette.set_mode(value)
            # Onbellekteki her sprite/karo/portre eski renklerle cizilmis.
            # Liste `src/art/caches.py`'de tek yerde: bir donem burada
            # elle sayiliyordu ve `postfx` unutulmustu - renk korlugu
            # moduna gecince sahne yeni renklerde, vinyet eski tonda
            # kaliyordu.
            from src.art import caches
            caches.invalidate_all()
        # Ses ve sarsinti ayarlarini sahneler kendi okur; burada zorlamiyoruz.

    def _apply_language(self, code: object) -> None:
        """Dili degistirir. Basarisiz olursa varsayilana doner.

        Yeniden baslatma gerekmiyor: arayuz metinleri cizim aninda cozuluyor,
        metin yuzeyleri de dizeyle anahtarlandigi icin onbellek kendiliginden
        tazeleniyor.
        """
        try:
            i18n.set_language(str(code))
        except i18n.LanguageError as exc:
            # Elle duzenlenmis ya da bozulmus bir ayar dosyasi oyunu
            # baslatmamazlik etmesin.
            print(f"[game] dil yuklenemedi ({code}): {exc}")
            i18n.set_language(i18n.DEFAULT_LANGUAGE)

    def screenshot(self, directory: Path | None = None) -> Path:
        target = directory or Path.cwd() / "build" / "screenshots"
        target.mkdir(parents=True, exist_ok=True)
        path = target / f"lore_{int(time.time())}.png"
        pygame.image.save(self.canvas, str(path))
        print(f"[game] ekran goruntusu: {path}")
        return path

    # --- Ses (Gorev 10) -------------------------------------------------------
    def play_sound(self, name: str, muffled: bool = False,
                  bus: str = "volume_sfx", volume: float = 1.0) -> None:
        """Tek seferlik efekt calar. `muffled=True` -> Yanki'nin bogulmus
        kopyasi (yalnizca `sfx.MUFFLED_KEYS` icindekiler icin gecerli)."""
        self.last_ui_sound = name
        self.audio.play(name, muffled=muffled, bus=bus, volume=volume)

    def play_loop(self, channel_key: str, name: str,
                 bus: str = "volume_music", volume: float = 1.0) -> None:
        """Mantiksal bir kanalda surekli ses baslatir (ruzgar, Yanki
        fisiltisi, ...). Ayni ses zaten caliyorsa yalnizca hacmi guncellenir."""
        self.audio.play_loop(channel_key, name, bus=bus, volume=volume)

    def set_loop_volume(self, channel_key: str, volume: float,
                        bus: str = "volume_music") -> None:
        self.audio.set_loop_volume(channel_key, volume, bus=bus)

    def stop_loop(self, channel_key: str) -> None:
        self.audio.stop_loop(channel_key)

    # --- Zaman kontrolu -----------------------------------------------------
    def hitstop(self, frames: int) -> None:
        """Vurus aninda oyunu dondurur. En uzun istek kazanir, birikmez."""
        self._hitstop_frames = max(self._hitstop_frames, frames)

    @property
    def frozen(self) -> bool:
        return self._hitstop_frames > 0

    # --- Ana dongu ----------------------------------------------------------
    def run(self, first_scene: type) -> None:
        self.scenes.set_root(first_scene, transition=False)
        self.running = True
        self._last_time = time.perf_counter()
        try:
            while self.running:
                self.tick()
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def tick(self) -> None:
        """Tek bir gercek kare: girdi, yakalanan tickler, cizim."""
        now = time.perf_counter()
        elapsed = min(now - self._last_time, MAX_CATCHUP_FRAMES / FPS)
        self._last_time = now
        self.real_frame += 1
        self.fps = self.clock.get_fps()

        self.input.begin_frame()
        self._pump_events()

        self._accumulator += elapsed * FPS
        steps = 0
        while self._accumulator >= 1.0 and steps < MAX_CATCHUP_FRAMES:
            self._step()
            self._accumulator -= 1.0
            steps += 1
        if steps == 0:
            # Donma sirasinda bile girdi okunmali; yoksa tuslar yutulur.
            self.input.end_frame()

        self._render()
        self.clock.tick(FPS)

    def _step(self) -> None:
        """Bir oyun karesi. Hitstop varsa fizik atlanir, cizim surer."""
        self.input.end_frame()
        if self._hitstop_frames > 0:
            self._hitstop_frames -= 1
            # Sahne guncellemesi atlanir ama sahne degisimi kuyrugu islenmeli,
            # yoksa donma sirasinda istenen gecis kaybolur.
            self.scenes.transition.update()
            return
        self.music.duck(self.music_hush)
        self.music.update()
        self.scenes.update()
        self.frame += 1

    def _pump_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
                return
            if event.type == pygame.VIDEORESIZE:
                self._recompute_viewport()
                continue
            self.input.handle_event(event)

            if event.type == pygame.KEYDOWN and self._handle_debug_key():
                continue
            self.scenes.handle_event(event)

    def _handle_debug_key(self) -> bool:
        """Hata ayiklama tuslarini yakalar. Yakalarsa True doner."""
        if self.input.pressed(Action.FULLSCREEN):
            self.toggle_fullscreen()
            return True
        if self.input.pressed(Action.SCREENSHOT):
            self.screenshot()
            return True
        if self.input.pressed(Action.DEBUG_OVERLAY):
            self.debug_overlay = not self.debug_overlay
            return True
        if self.input.pressed(Action.DEBUG_SILHOUETTE):
            index = self.render_modes.index(self.render_mode)
            self.render_mode = self.render_modes[(index + 1) % len(self.render_modes)]
            print(f"[game] cizim kipi: {self.render_mode}")
            return True
        return False

    @property
    def silhouette_mode(self) -> bool:
        return self.render_mode == "silhouette"

    @property
    def box_mode(self) -> bool:
        return self.render_mode == "box"

    def _render(self) -> None:
        if self.screen is None:
            return
        self.canvas.fill(palette.color("void"))
        self.scenes.draw(self.canvas)
        # Post-fx sahneden SONRA, hata ayiklama/imlecten ONCE: vinyet
        # oyunu cerceveler ama arayuzu ve imleci karartmamali.
        self._apply_postfx()
        if self.debug_overlay:
            self._draw_debug()
        self._draw_cursor()
        self.present()

    def present(self) -> None:
        """Tuvali ekrana olcekleyip **basar**.

        `_render`'dan ayri duruyor cunku bazen normal dongu disinda bir
        kare gostermek gerekiyor: uzun surecek bir isten (kol taramasi)
        hemen once. Dongu o sirada donmus oluyor; bu cagri olmadan
        oyuncu ekranin cakildigini sanir.
        """
        if self.screen is None:
            return
        self.screen.fill((0, 0, 0))
        if self.viewport.size == self.canvas.get_size():
            self.screen.blit(self.canvas, self.viewport.topleft)
        else:
            # Tam sayi olceklemede `scale` en hizli ve en keskin yol.
            # smoothscale burada YASAK - piksel art bulaniklasir.
            # **Her karede dogrula.** `VIDEORESIZE` her zaman gelmiyor -
            # ozellikle `set_mode` ile programatik kip degisiminde. Bayat
            # bir gorunum, pencereden BUYUK bir yuzey uretip her karede
            # olceklemek demek: ekran kirpilir ve oyun "donar" (ses
            # devam ettigi icin tam olarak oyle gorunur).
            #
            # Karsilastirma iki tamsayi; maliyeti yok, kazanci butun bir
            # hata sinifinin kapanmasi.
            if self.screen.get_size() != self._viewport_for_size:
                self._recompute_viewport()
            scaled = pygame.transform.scale(self.canvas, self.viewport.size)
            self.screen.blit(scaled, self.viewport.topleft)
        pygame.display.flip()

    def _apply_postfx(self) -> None:
        """Vinyet + bolum renk derecelendirmesi (src/art/postfx.py).

        Derecelendirmeyi sahne secer (`Scene.postfx_grade`); vermeyen
        sahne katmani hic almaz - menu ve sinematikler kendi kompozisyonunu
        zaten kuruyor.
        """
        scene = self.scenes.current
        grade = getattr(scene, "postfx_grade", "") if scene else ""
        if not grade:
            return
        strength = float(self.settings.get("postfx", 1.0))
        postfx.apply(self.canvas, grade, strength)

    def _draw_cursor(self) -> None:
        """Ozel imlec - yalnizca fare **son kullanilan** girdiyse gorunur.

        Ic cozunurlukte cizilir (dis cizimden once) ki geri kalan her sey
        gibi tam sayida buyusun - ekran uzayinda cizilseydi piksel art
        olceklemesiyle uyumsuz, bulanik bir imlec olurdu.
        """
        if self.input.last_device != "mouse":
            return
        position = self.virtual_mouse_pos()
        if position is not None:
            cursor.draw(self.canvas, position)

    def virtual_mouse_pos(self) -> tuple[float, float] | None:
        """Gercek fare konumunu ic (480x270) cozunurluge cevirir.

        Menu/ayarlar/karakter secimi kendi kopyalarini tutuyordu; tek
        kaynaga tasimak yerine (gerek yoksa dokunma) burada da var -
        ozel imlec ayni donusumu kullanmak zorunda.
        """
        mx, my = pygame.mouse.get_pos()
        if not self.viewport.collidepoint(mx, my) or self.scale <= 0:
            return None
        return ((mx - self.viewport.x) / self.scale,
                (my - self.viewport.y) / self.scale)

    def _draw_debug(self) -> None:
        from src.ui import text
        scene = self.scenes.current
        lines = [
            f"FPS {self.fps:5.1f}   kare {self.frame}",
            f"sahne {type(scene).__name__ if scene else '-'} "
            f"x{len(self.scenes.stack)}",
        ]
        if self.render_mode != "sprite":
            lines.append(f"cizim kipi: {self.render_mode.upper()} (F4)")
        extra = getattr(scene, "debug_lines", None)
        if callable(extra):
            lines.extend(extra())

        # Koyu zemin: hata ayiklama metni HUD'un ya da sahnenin uzerine binince
        # ikisi de okunmaz hale geliyordu.
        width = max((text.text_width(line) for line in lines), default=0) + 8
        height = len(lines) * 13 + 6
        backdrop = pygame.Surface((width, height), pygame.SRCALPHA)
        backdrop.fill((*palette.color("void"), 205))
        self.canvas.blit(backdrop, (2, 2))

        for index, line in enumerate(lines):
            text.draw(self.canvas, line, 6, 6 + index * 13,
                      color=palette.color("echo_bright"))

    # --- Kapanis ------------------------------------------------------------
    def quit(self) -> None:
        self.running = False

    def shutdown(self) -> None:
        self.scenes.shutdown()
        # Cozulemeyen dil anahtarlarini kapanista bildir: eksik ceviri
        # sessizce gecmesin (font'un eksik glif davranisiyla ayni mantik).
        i18n.report_missing()
        pygame.quit()
