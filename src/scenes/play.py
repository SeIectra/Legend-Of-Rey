"""Oynanabilir sahne temeli - bolumler ve test odasi bundan turer.

Dovus odasi bir donem butun bu baglantiyi kendi icinde tutuyordu. Bolum 1
gelince ayni sey ikinci kez yazilacakti; **game feel'in tek gecis noktasi
olmasi** tam da bunu yasaklıyor (CLAUDE.md 7): hitstop, sarsinti ve parcacik
tek bir `on_hit()` cagrisindan tetiklenmeli. Iki kopya olsaydi biri
guncellenir digeri geride kalirdi ve fark "bir sahnede vurus daha iyi
hissettiriyor" diye ortaya cikardi - bulmasi cok zor bir hata.

Alt sinif yalnizca **sahneyi** kurar: tilemap, oyuncu, dusmanlar, kamera
sinirlari. Dongu, hasar cozumu, kalicilik ve kancalarin tamami burada.
"""
from __future__ import annotations

import pygame

from src.art import palette
from src.art.ambience import Ambience
from src.art.particles import ParticleField
from src.combat.attack_token import AttackTokenManager
from src.combat.hitbox import HitboxManager, Team
from src.config import (
    SENSE_BETRAYAL_DELAY, SENSE_BETRAYAL_RANGE,
    COMBO_THRESHOLD_HIGH, COMBO_THRESHOLD_MID, DEATH_SCREEN_DELAY,
    HARD_LAND_AIR_FRAMES,
    INTERNAL_WIDTH, NECKLACE_BEAT_MIN_WARMTH, TILE_SIZE,
)
from src.systems.echo import COMBO_TO_RESTORE
from src.core.camera import Camera
from src.core.input import Action
from src.core.juice import ImpactEvent, ImpactWeight, Juice
from src.core.scene import Scene
from src.entities.character_stats import ARDO, REY
from src.entities.player import Player
from src.systems import abilities
from src.systems.compass import Compass
from src.systems.echo import Answer, EchoState
from src.systems.tracking import BLOOD, SCORCH, TraceField, TrackingState
from src.systems.save import read_save
from src.ui import echo_view, tracking_view
from src.ui.chapter_card import ChapterCard
from src.ui.dialogue import Dialogue, Line
from src.ui import text
from src.ui.hud import HUD
from src.ui.i18n import t
from src.world.decals import DecalField

HUD_MARGIN = 6


class _WallTarget:
    """Yanki'nin parlatacagi duvar. `echo_view` `.rect` bekliyor."""

    __slots__ = ("rect",)

    def __init__(self, rect) -> None:
        self.rect = rect


class PlayScene(Scene):
    """Oynanabilir bir alan: tilemap, oyuncu, dusmanlar, game feel."""

    # Adim sesi zemine gore degil **sahneye** gore degisir (SES-LISTESI 2:
    # "Taş zeminde"/"Toprak/koy zemininde") - zindan varsayilan, Bolum 1
    # (koy) kendi degerini ezer.
    footstep_sound = "step_stone"

    # Bolum basi karti - alt sinif ikisini de verirse gosterilir.
    # `0` = kart yok (dovus test odasi, temel dogrulama ekrani gibi
    # bolum olmayan sahneler).
    chapter_number: int = 0
    chapter_name_key: str = ""

    # Odanin havasi (src/art/ambience.py). Bos = atmosfer katmani yok.
    # `particles` olaylar icin (vurus/olum), bu SUREKLI olan sey - oda
    # hicbir sey olmasa bile yasiyor gorunsun.
    ambience_preset: str = ""

    def setup(self) -> None:
        """Alt sinif sahneyi burada kurar.

        `self.tilemap` ve `self.player` **zorunlu**; `self.enemies` istege
        bagli (varsayilan bos).
        """
        raise NotImplementedError

    def on_enter(self, character: str = "rey", **kwargs: object) -> None:
        self.character = character
        self.enemies: list = []
        self.toast = ""
        self.toast_frames = 0
        self.total_hits = 0

        self.particles = ParticleField()
        self.juice = Juice(self.game, spawn_particles=self._emit_particles)
        # Ekran sarsintisi ayarlardan gelir - erisilebilirlik icin kapatilabilir.
        shake = float(self.game.settings.get("screen_shake", 1.0))
        self.juice.configure(shake_enabled=shake > 0.0, shake_scale=shake)
        self.hitboxes = HitboxManager(on_hit=self.on_hit)
        # Ayni anda en fazla 2 dusman saldirabilir.
        self.tokens = AttackTokenManager()
        self.camera = Camera()
        self.save_data, _ = read_save()

        # **Yanki'nin tersine donmesi** (`docs/yapi.md` B14). Bayrak
        # kayittan geliyor, yani B15-B18 hicbir sey yazmadan
        # devraliyor. Gerekce `config.py`de: "her bolum bir satir
        # eklemek zorunda" bu projede uc kez hatanin sekli oldu.
        self.sense_betrayed = bool(
            self.save_data is not None
            and self.save_data.flags.get("sense_betrayed"))
        self._sense_open_frames = 0
        self.hud = HUD(self.game)

        # Yanki yalnizca Rey'de. Ardo'da `None` kalir ve kod her yerde
        # "Yanki var mi?" diye dallanmaz - `has_echo` tek yerde sorulur.
        self.echo = (EchoState(tier=self.echo_tier)
                     if self.character != "ardo" else None)
        self._echo_was_active = False   # echo_open/close kenar tespiti icin

        # IZ SURME - Ardo'nun karsi mekanigi (`src/systems/tracking.py`,
        # `docs/derinlestirme.md` 2.4). Yanki'nin tam simetrigi: Rey'de
        # `None`, Ardo'da dolu. Ayni tus (`Action.ECHO`) ikisini de aciyor;
        # ayrilan sey duyu.
        #
        # Ardo artik bir EKSIKLIKLE tanimli degil - belgenin en net
        # tespitiydi: *"Su an Ardo'nun oynanisi 'Yanki yok'. Bu zayif
        # tasarim."*
        self.tracking = (TrackingState() if self.character == "ardo"
                         else None)
        # Izler her karakterde toplaniyor - Rey oynarken de dunya iz
        # birakiyor. Ayni kayitla Ardo bolumu bastan oynadiginda tutarli
        # bir gecmis buluyor; ayrica ileride "zindan hatirliyor"
        # (derinlestirme 3.4) ayni alandan beslenebilir.
        self.traces = TraceField()
        self.compass = Compass()
        self._beat_index = -1            # necklace_beat kenar tespiti icin
        self.breakables: list = []
        # Diyalog oynanisi **durdurmuyor**: oyuncu konusma surerken
        # yuruyebilir. Durdursaydik her replik bir kesinti olurdu ve oyuncu
        # okumak yerine gecmeye calisirdi.
        self.dialogue = Dialogue()

        # Bolum basi karti - alt sinif `chapter_number`/`chapter_name_key`
        # verirse gosterilir. Ara sahne DEGIL, bindirme: oynanisi
        # durdurmuyor, oyuncu ilk kareden itibaren yuruyebilir.
        self.card = (ChapterCard(self.chapter_number, self.chapter_name_key)
                     if self.chapter_number else None)
        self.ambience = (Ambience(self.ambience_preset)
                         if self.ambience_preset else None)
        # Su seviyesi - yalnizca suyu olan bolumlerde (`setup()` kuruyor).
        # `self.echo` ile ayni desen: yoksa `None` ve kod her yerde
        # "su var mi?" diye dallanmiyor.
        self.water = None

        self.setup()

        # Mermiler duvarda olsun: `setup()` tilemap'i kurdu.
        self.hitboxes.tilemap = self.tilemap

        # Yetenek agacindan acilanlar oyuncuya biniyor. `setup()`'tan
        # SONRA: oyuncu orada yaratiliyor. Duz bonuslar (can, pencere,
        # sarj) burada bir kez uygulaniyor.
        if self.save_data is not None:
            self._restore_abilities()
            self.player.apply_skills(getattr(self.save_data, "skills", ()))
            self._equip_saved_weapon()

        self.camera.set_bounds(self.tilemap.bounds)
        self.decals = DecalField(*self.tilemap.bounds.size)
        self.camera.snap_to(self.player.body.center_x, self.player.body.center_y)

    def _restore_abilities(self) -> None:
        """Kazanilmis yetenekleri kayittan geri yukler.

        **Bu yoktu ve oyunun yarisini sessizce bozuyordu.** Arda
        (30.08.2026): *"Ardo karakterinin geldigi bolumde yine silahimiz
        yok."* Sebep sanildigi gibi silah degil, yetenekti:

        `SaveData.abilities` alani vardi ama **hicbir yer ona yazmiyor,
        hicbir yer geri yuklemiyordu.** Rey `REY_STARTING = frozenset()`
        ile basliyor, kilici Bolum 1'de `grant()` ile aliyor - ve o
        yalnizca bellekte. Bolum 2'den sonraki her bolumde Rey:

            kilic YOK  -  yumrukla dovusuyor
            kacinma YOK - `Action.DODGE` hicbir sey yapmiyor
            Yanki YOK   - bolumun anlati araci calismiyor

        Ucu de sessiz: hata vermiyor, sadece eksik. `_persist_abilities`
        yazma tarafi.
        """
        for ability in getattr(self.save_data, "abilities", ()) or ():
            # Yanki yetenekleri Rey'e ait; Ardo'nun karsiligi Iz Surme.
            # Kayit tek dosya ve ayni kayitla iki karakter de
            # oynanabiliyor, yani Rey'in `echo_sight`i orada duruyor.
            if self.character == "ardo" and ability in abilities.ECHO_SET:
                continue
            # **Tanitildigi bolumden once geri yuklenmiyor.** Gerekce
            # `abilities.INTRODUCED_IN` tablosunda.
            if not abilities.restorable(ability, self.chapter_number):
                continue
            self.player.grant(ability)
        self._grant_baseline()

    def _grant_baseline(self) -> None:
        """Bu bolume gelmis bir oyuncunun **mutlaka** sahip oldugu seyler.

        Iki isi birden yapiyor:

        1. **Eski kayitlari onariyor.** `abilities` alani bir donem hic
           yazilmiyordu (bkz. `_restore_abilities`), yani 30.08 oncesi
           her kayit bos. Yalnizca kayittan okusaydik o kayitlar
           duzelmezdi - Arda'nin *"Bolum 6'da hala kilicim yoktu"*
           bildirimi tam olarak buydu.

        2. **Yeni bolumlerin unutmasini onluyor.** Bolum 3 ve 4 bunu
           `setup()` icinde elle yapiyordu; 5, 6 ve 7 yapmayi unutmustu
           ve kimse fark etmedi. Her bolume bir satir eklemek, birini
           unutmanin yoluydu - nitekim ucu unutulmus.

        Taban **bolum numarasindan** turuyor: oraya gelebilmis olmak o
        yetenege sahip olmayi gerektiriyor.
        """
        if self.chapter_number <= 1:
            return                      # B1 hikayenin kendisi - eli bos baslar
        self.player.grant(abilities.SWORD)
        if self.chapter_number >= 3:
            self.player.grant(abilities.DODGE)
            # Yanki gormesi Rey'e ait; Ardo'nun karsiligi Iz Surme.
            if self.character != "ardo":
                self.player.grant(abilities.ECHO_SIGHT)

    def _persist_abilities(self) -> None:
        """Oyuncunun yeteneklerini kayda yazar.

        Sirali degil **kumeleyerek**: bir bolumde kazanilan sonrakinde
        kaybolmasin.
        """
        if self.save_data is None:
            return
        known = set(getattr(self.save_data, "abilities", ()) or ())
        self.save_data.abilities = sorted(known | set(self.player.abilities))

    def _update_inventory_hint(self) -> None:
        """Gercek bir **secimi** olan oyuncuya envanteri ogret.

        Kosul "birden fazla silah" degil, "Bolum 2'nin odulu var mi":
        yumruk + kilic de iki silah ama bir secim degil - kilic her
        acidan daha iyi ve kimse yumruga donmez. Ipucu Bolum 1'de
        cikiyordu ve orada tamamen anlamsizdi (test yakaladi).

        Hancer/Balta ise gercek bir tercih (`src/ui/weapon_choice.py`):
        hizli ve zayif mi, yavas ve agir mi.
        """
        if self.save_data is None:
            return
        from src.combat import weapons
        from src.ui.equipment import owned
        choices = owned(self.save_data)
        if weapons.DAGGER not in choices and weapons.AXE not in choices:
            return
        self.hint_once("hint_inventory", "hint.inventory", Action.NEXT_TAB)

    def _sync_abilities(self) -> None:
        """Yetenek sayisi degistiyse kayda yaz.

        Her bolume "burada da kaydet" satiri eklemek yerine tek yerde:
        bir bolum unutursa sessizce kaybolurdu ve bu tam olarak bir kez
        yasandi - `SaveData.abilities` alani vardi, kimse yazmiyordu.

        Maliyeti kare basina bir tamsayi karsilastirmasi. Kayit diske
        burada yazilmiyor; `pause`/`death`/bolum sonu zaten yaziyor.
        """
        count = len(self.player.abilities)
        if count != getattr(self, "_ability_count", -1):
            self._ability_count = count
            self._persist_abilities()

    def _equip_saved_weapon(self) -> None:
        """Kayittaki silahi kusandirir - Bolum 2'deki secim burada tasiniyor.

        Yalnizca oyuncunun **gercekten sahip oldugu** bir silah kusaniliyor.
        Kilic/yumruk yolu `Player.grant()` ile ilerliyor; burasi onu
        ezmiyor, sadece Bolum 2 odulunu (Hancer/Balta) geri yukluyor.
        Kosul olmasaydi kayitsiz/varsayilan "sword" degeri Bolum 1'de
        yumrukla baslayan Rey'e kilic verirdi ve o bolumun butun anlati
        ani ("kilici buluyor") bozulurdu.

        Kilic artik `_restore_abilities` uzerinden geliyor: yetenek
        kazanildiysa `grant(SWORD)` zaten kusandiriyor. Burasi hala
        yalnizca Hancer/Balta ile ilgileniyor - o ikisi bir yetenek
        degil bir **secim**.
        """
        from src.combat import weapons
        key = getattr(self.save_data, "weapon", "")
        if key in (weapons.DAGGER, weapons.AXE):
            self.player.equip_weapon(key)

    @property
    def enemy_fade(self) -> float:
        """Yasayan dusmanlarin solma orani - `enemy_render` okuyor.

        Iz Surme'nin bedeli. Rey'de `tracking is None`, yani hep 0.0.
        """
        return self.tracking.enemy_fade if self.tracking is not None else 0.0

    # --- Yardimcilar --------------------------------------------------------
    def make_player(self, x: float, y: float) -> Player:
        stats = ARDO if self.character == "ardo" else REY
        return Player(self, x, y, stats)

    @property
    def gold(self) -> int:
        return self.save_data.gold if self.save_data else 0

    @property
    def echo_tier(self) -> int:
        return self.save_data.echo_tier if self.save_data else 2

    # --- Dongu --------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        # **Bolume ait bir bindirme aciksa ESC once ONU kapatir.**
        #
        # Arda (30.08.2026): *"Mum Bekcisi ile bir seyler almaya
        # girdigimizde hicbir sey almadan cikamiyoruz."* Sebep buydu:
        # ticaret ekrani ESC'yi dinliyordu ama ESC buraya once ugrayip
        # duraklatma menusunu aciyordu. Menuyu kapatinca ticaret hala
        # acik, ESC yine menuyu aciyor - sonsuz dongu. Yalnizca
        # Backspace (`Action.CANCEL`'in oteki tusu) ise yariyordu ve onu
        # kimse tahmin edemez.
        #
        # Cozum tek yerde: sahne "su an modal bir sey aciyim" diyebiliyor
        # ve duraklatma o tusu calmiyor.
        if self.modal_active:
            return
        if self.game.input.pressed(Action.PAUSE):
            from src.ui.pause import PauseScene
            self.scenes.push(PauseScene, save_data=self.save_data)
            return
        # Envanter **dogrudan** Tab ile. Arda (30.08.2026): *"r veya tab
        # tusuyla envanterimiz falan acilsa da gorsek."*
        #
        # Ekran zaten vardi (`src/ui/equipment.py`) ama yalnizca
        # duraklatma menusunun icinden aciliyordu - yani oyuncunun once
        # onu orada bulmasi gerekiyordu. Silahini merak eden biri ESC'ye
        # basip menu okumak istemiyor.
        #
        # R kullanilmadi: o, olum ekraninda "yeniden dene" ve iki islevli
        # bir tus kazayla yeniden baslatma riski demek.
        if self.game.input.pressed(Action.NEXT_TAB) and not self.player.dead:
            from src.ui.equipment import EquipmentScene
            self.game.play_sound("ui_tick")
            self.scenes.push(EquipmentScene, save_data=self.save_data,
                             player=self.player)
            return
        if event.key == pygame.K_r and self.player.dead:
            self.restart()

    def restart(self) -> None:
        """Olumden sonra sahneyi bastan kurar.

        **Bu bir yumusak kilit duzeltmesi.** Olum ekrani "OLDUN - R ile
        sifirla" yaziyordu ama R'yi YALNIZCA dovus test odasi dinliyordu;
        bolumlerde tusun hicbir karsiligi yoktu, yazi bos bir soz
        veriyordu (24.08.2026'da bulundu).

        Boss arenasinin cikisi anahtarla acilir hale gelince bu gercek bir
        kilitlenmeye donustu: boss'a yenilen oyuncu ne sifirlayabiliyor ne
        de cikabiliyordu. Cikis kapisini "olunce de ac" yapmak daha kolay
        olurdu ama o zaman olmek boss'u atlamanin YOLU olurdu - dogru
        cozum sifirlamanin gercekten calismasi.

        `on_enter` sahneyi bastan kuruyor (dovus odasinin `K_r`'siyle ayni
        yol). Kayit dosyasina dokunulmuyor: altin ve Yanki kademesi
        olumden once neyse o kaliyor.

        ## Kontrol noktasi (29.08.2026)

        Bastan kurmak **dogru** ama tek basina acimasiz: on dakikalik bir
        bolumun sonunda olen oyuncu her seye yeniden basliyordu ve bu,
        Arda'nin yapacagi ara degerlendirmeyi zehirlerdi.

        Cozum bir "kismi geri alma" DEGIL - o yol her zaman bayat durum
        birakir (kapilar, anahtarlar, arena muhru, su seviyesi... her
        bolumun kendi degismezleri var ve biri mutlaka unutulur). Sahne
        yine **tamamen** bastan kuruluyor; sonra oyuncu oldugu ODANIN
        basina isinlaniyor ve o odanin dusmanlari yeniden doguyor.

        Yani: butun degismezler taze, ilerleme korunuyor. Bedeli odayi
        bastan oynamak - retry'in olmasi gereken bedeli tam olarak bu.
        Boss arenasi da dogal calisiyor: arena bir oda, yani boss'a
        yenilen oyuncu arenanin basindan devam ediyor, bolumun basindan
        degil.
        """
        # `entered_rooms` yalnizca oda tabanli bolumlerde var (Bolum 1 ve
        # dovus odasi oda kullanmiyor) - `getattr` ile soruluyor, ozniteligi
        # olmayan sahnelerde sistem sessizce devre disi kaliyor.
        self.death_frames = 0        # bekleyen olum ekrani iptal
        room = self.checkpoint_room
        entered = set(getattr(self, "entered_rooms", ())) if room else set()
        x, y = self.checkpoint_x, self.checkpoint_y

        self.on_enter(character=self.character)

        if not room:
            return
        # `entered_rooms` geri konuyor ki anlati TEKRARLAMASIN - ust uste
        # olen oyuncuya ayni replikleri okutmak ogut olur. Ama odanin
        # dusmanlari yine de dogmali, o yuzden `_spawn_room` DOGRUDAN
        # cagriliyor (`_enter_room` "zaten girilmis" deyip donerdi).
        self.entered_rooms = entered
        self.room = room
        self.player.body.set_feet(x, y)
        spawn_room = getattr(self, "_spawn_room", None)
        if spawn_room is not None:
            spawn_room(room)
        # Sahne icinde KAZANILMIS durumlar geri kuruluyor (yoldas gibi).
        self.after_restart(room)
        self.camera.snap_to(self.player.body.center_x,
                            self.player.body.center_y)

    # --- Kontrol noktasi ----------------------------------------------------
    # Oda tabanli. Alt siniflar bunun icin **hicbir sey yapmiyor**: hepsi
    # zaten `self.room` tutuyor ve odaya girerken degistiriyor, biz de
    # o degisimi izliyoruz. Her bolume ayri bir kanca eklemek besinde
    # birini unutmanin yoluydu.
    #
    # Sadece **ayaktayken** kaydediliyor: havadayken kaydedilseydi oyuncu
    # bosluga dusup oldugunde tekrar bosluga dogar ve sonsuz olum
    # dongusune girerdi.
    checkpoint_room: str = ""
    checkpoint_x: float = 0.0
    checkpoint_y: float = 0.0

    # Dovus muzigi son uyanik dusmandan sonra bu kadar kare daha calar.
    _combat_frames: int = 0
    # Dovus yokken calacak parca. Alt sinif ezerek kendi havasini
    # seciyor.
    #
    # ## Varsayilan neden "combat"
    #
    # Arda, canli oynanis (31.08.2026): *"combat ve kesif icin
    # kullandigimiz sarkilar farkli oldugundan muzik hizli degisiyor.
    # Arka planda sadece combat icin olan muzik kalsin."*
    #
    # Sebep yapisaldi: varsayilan "explore" idi ve bir dusman
    # uyandiginda "combat"a geciliyordu. Zindanda dusmanlar surekli
    # uyanip uyudugu icin parca dakikada birkac kez takas ediyordu -
    # ve iki parca birbirinden cok farkli oldugu icin her takas
    # duyuluyordu.
    #
    # Artik ikisi de "combat": `_update_music` dovuste de dovus
    # disinda da ayni baglami hesapliyor, `MusicDirector.play` ayni
    # baglamda **hicbir sey yapmiyor**, yani takas yok.
    #
    # Kesif parcasi (Fade) atilmadi - **saklandi**. Bulmaca agirlikli
    # bolumlerde (`docs/ekonomi-uretim.md` boyle etiketliyor: B5, B11
    # ve sirasi gelince B17) `music_context = "explore"` veriliyor.
    # Orada dovus seyrek oldugu icin gecis nadir ve **anlamli**:
    # muzigin degismesi bir sey oldugunu soyluyor.
    music_context: str = "combat"

    def _update_music(self) -> None:
        """Sahnenin durumundan muzik baglamini turetir.

        Sahne "hangi dosya" demiyor, "ne oluyor" diyor
        (`src/audio/music.py`). Dosya adlari tek yerde.

        Gecikme (`COMBAT_LINGER_FRAMES`) sart: tek bir dusmanin gozden
        kaybolmasi muzigi kesip acsaydi ses **titrerdi**. Dovus bittikten
        sonra gerilim de hemen dusmuyor - bu hem dogru his hem dogru
        muhendislik.
        """
        from src.audio.music import COMBAT_LINGER_FRAMES, combat_context

        context = combat_context(self)
        if not context:
            if any(getattr(e, "aware", False) and not e.dead
                   for e in self.enemies):
                self._combat_frames = COMBAT_LINGER_FRAMES
            elif self._combat_frames > 0:
                self._combat_frames -= 1
            if self._combat_frames > 0:
                context = "combat"
            else:
                # Sahne kendi sakin baglamini bildiriyor. Varsayilan
                # "combat" (gerekce `music_context`te); Bolum 4 "sad",
                # bulmaca bolumleri "explore".
                context = self.music_context or "combat"

        from src.audio.music import COMBAT_FADE_IN_MS
        fade = COMBAT_FADE_IN_MS if context != "explore" else None
        self.game.music.play(context, fade_ms=fade)

    def sense_open(self) -> bool:
        """Oyuncunun duyusu (Yanki ya da Iz Surme) su an acik mi.

        Iki sistem de ayni `active` sozlesmesini tasiyor, o yuzden
        cagiran taraf "hangi karakter?" diye sormuyor - `EchoState` ve
        `TrackingState` ayni desenle yazildiginin karsiligi burada
        toplaniyor.
        """
        if self.echo is not None:
            return self.echo.active
        if self.tracking is not None:
            return self.tracking.active
        return False

    def _update_betrayal(self) -> None:
        """Duyuyu acmak seni **ele veriyor** - B14'ten sonra kalici.

        `docs/yapi.md` B14: *"Yanki tersine doner - actiginda dusmanlar
        da seni gorur."*

        On uc bolumdur refleks suydu: emin degilsen Yanki'yi ac. Bu
        bayraktan sonra ayni tus odanin tamamini uyandiriyor. Arac
        degismedi, **sozlesme degisti**.

        Kisa bir gecikme var (`SENSE_BETRAYAL_DELAY`): bir an bakmak
        ile acik tutmak ayni sey olmamali, yoksa yanlislikla dokunan
        oyuncu cezalandirilir ve mekanik bir tuzaga doner.

        Ardo'da ayni kural, baska kurgu: onun twist'i "sesler benim
        degil" degil, **"izler benim icin birakilmis"**.
        """
        if not self.sense_betrayed:
            self._sense_open_frames = 0
            return
        if not self.sense_open():
            self._sense_open_frames = 0
            return
        self._sense_open_frames += 1
        if self._sense_open_frames < SENSE_BETRAYAL_DELAY:
            return
        body = self.player.body
        for enemy in self.enemies:
            if enemy.dead or enemy.aware:
                continue
            dx = enemy.body.center_x - body.center_x
            dy = enemy.body.center_y - body.center_y
            if dx * dx + dy * dy > SENSE_BETRAYAL_RANGE ** 2:
                continue
            enemy.aware = True
            self.on_betrayal_wake(enemy)

    def on_betrayal_wake(self, enemy) -> None:
        """Bir dusman **duyu yuzunden** uyandi. Bolum kendi dilinde
        gosterebilsin diye kanca; varsayilan sessiz."""

    def _update_traces(self) -> None:
        """Dunya iz birakiyor - oyuncu ve dusmanlarin ayak izleri.

        **Her karakterde** calisiyor, yalnizca Ardo'da degil: Rey oynarken
        de gecmis birikiyor. Kayit sahne omruyle sinirli (bolum bitince
        gidiyor), yani "gecmis" burada tek bir oturumun gecmisi.

        Kare butcesi: dusman basina karede bir `dict` bakisi. Izler
        yalnizca Iz Surme acikken ve yalnizca menzildekiler CIZILIYOR
        (`tracking_view.draw_traces`), yani asil maliyet orada ve o da
        Ardo'ya ozel.
        """
        self.traces.update()
        self.traces.record_step(self.player)
        for enemy in self.enemies:
            if not enemy.dead:
                self.traces.record_step(enemy)

    # Olum ekrani bu kadar kare sonra aciliyor: olum vurusunun hitstop'u,
    # sarsintisi ve parcaciklari once bitsin. Aninda acilirsa oyuncu neyle
    # oldugunu goremiyor.
    death_frames: int = 0

    def _update_death(self) -> None:
        if self.death_frames <= 0:
            return
        self.death_frames -= 1
        if self.death_frames == 0:
            self._open_death_screen()

    def _update_checkpoint(self) -> None:
        room = getattr(self, "room", "")
        if not room or self.player.dead:
            return
        if room != self.checkpoint_room:
            if not self.player.body.grounded:
                return          # havada kaydetme - bkz. yukaridaki not
            self.checkpoint_room = room
            self.checkpoint_x = self.player.body.center_x
            self.checkpoint_y = self.player.body.bottom

    def update(self) -> None:
        self._update_music()
        self.player.update()
        self._sync_abilities()
        self._update_inventory_hint()
        self._update_companion_order()
        self._update_death()
        self._update_checkpoint()
        self.tokens.update()
        for enemy in self.enemies:
            enemy.update()
        self.enemies = [e for e in self.enemies if not e.remove]

        self.hitboxes.update({
            Team.ENEMY: self.enemies,
            Team.PLAYER: [self.player],
        })

        self.particles.update()
        self.juice.update()
        self.camera.shake_offset = self.juice.shake.offset
        self.camera.update(self.player.body.center_x,
                           self.player.body.center_y - 6,
                           facing=self.player.facing,
                           grounded=self.player.body.grounded)

        self._update_traces()
        self._update_betrayal()
        if self.echo is not None:
            self.echo.update(self.echo_held())
            self._update_echo_audio()
            if self.game.input.pressed(Action.ECHO_ASK):
                self.on_echo_ask()
        if self.tracking is not None:
            # **Ayni tus.** Rey'de Yanki, Ardo'da Iz Surme. Girdi
            # sozlesmesi ortak, duyu farkli (derinlestirme 2.4).
            self.tracking.update(self.echo_held())
        self.compass.update(self.player)
        self._update_necklace_audio()
        self.dialogue.update(self.game)
        if self.card is not None:
            self.card.update()
        if self.ambience is not None:
            self.ambience.update(self.camera.offset)
        if self.water is not None:
            self._update_water()
        # Kirilabilir duvarlar Yanki ile parliyor. Liste kucuk (oda basina
        # birkac tane), her karede uretmek sorun degil.
        self.breakables = [_WallTarget(r)
                           for r in self.tilemap.breakable_rects()]

        self.hud.update(self.player, self.gold, self.echo_tier)
        if self.toast_frames > 0:
            self.toast_frames -= 1
        self.update_scene()

    def _update_water(self) -> None:
        """Suyun seviyesini surer ve butun aktorlere etkisini uygular.

        Dusmanlar da suyun icinde: yalnizca oyuncuya uygulasaydik su
        "oyuncuya ozel bir kural" olurdu, mekan degil. Yuzme YALNIZCA
        oyuncuda - dusmanlarin yuzme davranisi ayri bir tasarim isi ve
        Bolum 5'te sudaki dusman yok (tasarim geregi: su bir bulmaca,
        dovus alani degil).
        """
        self.water.update()
        swimming = (self.game.input.held(Action.JUMP)
                    and not self.player.dead)
        self.player.water_ratio = self.water.apply(self.player.body,
                                                   swimming)
        for enemy in self.enemies:
            self.water.apply(enemy.body)

    def echo_held(self) -> bool:
        """Yanki bu karede acik mi?

        Normalde tusun kendisi. Bolum, anlatimin gerektirdigi anlarda
        (Bolum 2'nin Yanki odasi: ses **kendiliginden** yukselir) bunu
        ezebilsin diye ayri bir kanca. Ezme `EchoState`'in icine
        yazilsaydi bedel muhasebesi iki yere dagilirdi.
        """
        return self.game.input.held(Action.ECHO)

    def update_scene(self) -> None:
        """Alt sinifa ait kare islemleri (tetikleyiciler, anlatim)."""

    @property
    def modal_active(self) -> bool:
        """Bolume ait bir bindirme acik mi (ticaret, secim, bulmaca)?

        Aciksa duraklatma ve envanter tuslari **calismiyor** - o an
        ekrandaki sey kendi tuslarini kullaniyor. Alt sinif ezip kendi
        durumunu doner (`Chapter03Scene`: `self.trading`).
        """
        return False

    def after_restart(self, room: str) -> None:
        """Olumden sonra sahne kuruldu ve oyuncu odasina kondu.

        `setup()` her seyi sifirdan kuruyor - dogru ve kasitli - ama
        sahne icinde **kazanilmis** durumlar var: Bolum 6'da yoldas
        `setup()`'ta `None`, ancak "kose"de kurtarilinca dogar. Olum
        arenada gerceklestiginde o an bir daha hic gelmiyordu ve boss
        yalniz doguluyordu (Arda, 30.08.2026: *"oldukten sonra o boss
        fight ta hic dogmuyor"*).

        Alt sinif burada o durumlari geri kuruyor.
        """

    # --- Ipuclari -----------------------------------------------------------
    def hint_once(self, flag: str, message_key: str, action: Action,
                  frames: int = 210) -> None:
        """Bir tusu **bir kez** ogretir ve kayda isaretler.

        Arda (30.08.2026): *"Tab ile envanter acacagimi ve U ile komut
        verecegimin hint'i yok."* Iki yeni tus eklendi ve ikisi de
        oyuncuya hic soylenmedi - bir tus varsa ama kimse bilmiyorsa
        yok demektir.

        **Tus adi tablodan okunuyor, sabit yazilmiyor.** Tuslar artik
        yeniden atanabilir (`src/systems/bindings.py`); "Tab" diye
        yazsaydik tusu degistiren oyuncuya yalan soylerdik.

        Bir kez: `SaveData.flags`'e yaziliyor. Her odada tekrarlanan bir
        ipucu ogut olur.
        """
        data = self.save_data
        if data is None or data.flags.get(flag):
            return
        data.flags[flag] = True
        from src.systems import bindings as binds
        table = binds.read(self.game.settings)
        self.show_toast(t(message_key,
                          key=binds.labels_for(table, action)),
                        frames=frames)

    # --- Yoldas komutu ------------------------------------------------------
    def _update_companion_order(self) -> None:
        """"Burada bekle / pesimden gel" - tek tus, iki durum.

        Yoldasi olan her bolumde calisiyor: `self.companion` varsa
        yeter, bolume ozel kod gerekmiyor.
        """
        companion = getattr(self, "companion", None)
        if companion is None or self.player.dead:
            return
        # Yoldas ilk kez yanindayken komutu ogret.
        self.hint_once("hint_companion", "hint.companion_wait",
                       Action.COMPANION_WAIT)
        if not self.game.input.pressed(Action.COMPANION_WAIT):
            return
        if companion.hold_x is None:
            companion.hold(companion.body.center_x)
            self.show_toast(t("companion.waiting"), frames=110)
        else:
            companion.release()
            self.show_toast(t("companion.following"), frames=110)
        self.game.play_sound("ui_tick")

    @property
    def has_echo(self) -> bool:
        """Yanki bu oynanista var mi? (Rey'de var, Ardo'da yok.)

        `docs/gdd.md` 4: Yanki **Rey'in laneti**. Bir donem replikler
        karakterden bagimsiz oynuyordu ve Ardo da mor sesi duyuyordu -
        sahip olmadigi bir gucun sesini. Her Yanki repligi bunun ardina
        alinmali.
        """
        return self.echo is not None

    def say_player(self, key: str, ardo_key: str = "", **kwargs) -> None:
        """Oynanan karakterin agzindan replik.

        Sabit `Line("rey", ...)` yaziliydi ve Ardo oynarken ekranda REY
        etiketi cikiyordu. `ardo_key` verilmezse ayni metin kullanilir -
        cogu tepki iki karakter icin de gecerli.
        """
        chosen = ardo_key if (self.character == "ardo" and ardo_key) else key
        self.say(Line(self.character, chosen), **kwargs)

    def say(self, *lines, auto_advance: bool = False) -> None:
        """Replik dizisi baslatir. `lines` `Line` nesneleri.

        `auto_advance=True` yalnizca bir sahne-zamanlayicisiyla yarisan
        (orn. Bolum 1'in prolog beat'leri) dizilerde kullanilir - normal
        kesif/dovus repligi oyuncu onaylayana kadar ekranda kalir.
        """
        self.dialogue.start(tuple(lines), auto_advance=auto_advance)

    # --- Yanki --------------------------------------------------------------
    def on_echo_ask(self) -> None:
        """Oyuncu Yanki'ya soru sordu. Alt sinif cevabin **anlamini** verir.

        Taban yalnizca cevabin turunu uretiyor (dogru/eksik/yalan); o
        cevabin neyi gosterdigine bolum karar veriyor - cikis mi, gizli oda
        mi, Cemo mu.
        """
        if self.echo is None:
            return
        answer = self.echo.ask()
        self.game.play_sound("echo_ask", bus="volume_echo")
        # `echo_answer_lie` **bilerek** `echo_answer_truth` ile ayni dalga
        # formu (sfx_world.py) - kulaktan ayirt edilebilir olsaydi mekanik
        # olurdu (docs/dovus-sistemi.md 5).
        answer_sound = {
            Answer.TRUTH: "echo_answer_truth",
            Answer.PARTIAL: "echo_answer_partial",
            Answer.LIE: "echo_answer_lie",
        }.get(answer)
        if answer_sound:
            self.game.play_sound(answer_sound, bus="volume_echo")

    def _update_echo_audio(self) -> None:
        """Yanki acilirken/kapanirken kenar tespiti - `EchoState` kendisi
        sesle ilgilenmiyor (systems/ katmani salt mantik), kenar burada.

        Surekli `echo_loop` dongusu **kaldirildi** (Arda'nin canli oynanis
        geri bildirimi, 22.08.2026: "cizirti gibi, rahatsiz edici").
        Sentezlenmis surekli/donguluk sesler bu oturumda genel olarak
        guvenilir bulunmadi; kisa, nedeni belli tek seferlik sesler
        (echo_open/close gibi) kaliyor.
        """
        active = self.echo.active
        if active and not self._echo_was_active:
            self.game.play_sound("echo_open", bus="volume_echo")
        elif not active and self._echo_was_active:
            self.game.play_sound("echo_close", bus="volume_echo")
        self._echo_was_active = active

    def _update_necklace_audio(self) -> None:
        """Kalp atisi periyodu her devri tamamladiginda tek `tak` sesi.

        `Compass.pulse` surekli bir 0..1 egri veriyor (cizim icin); ses
        icin **kenar** gerekiyor - donguyu kendisi saymiyor, burada sayilir.
        """
        if self.compass.warmth <= NECKLACE_BEAT_MIN_WARMTH:
            self._beat_index = -1
            return
        index = self.compass.frame // max(1, self.compass.beat_period)
        if index != self._beat_index:
            self._beat_index = index
            self.game.play_sound("necklace_beat", volume=self.compass.warmth)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(palette.color("abyss_dark"))
        offset = self.camera.offset

        self.draw_background(surface, offset)
        self.tilemap.draw(surface, offset)
        self.decals.draw(surface, offset)
        for enemy in self.enemies:
            enemy.draw(surface, offset)
        self.player.draw(surface, offset)
        self.particles.draw(surface, offset)
        # Su aktorlerin USTUNE ama yari saydam ciziliyor: suya giren
        # oyuncu kaybolmamali, "suyun icinde" gorunmeli.
        if self.water is not None:
            from src.world import water as water_draw
            water_draw.draw(surface, offset, self.water)
        self.draw_foreground(surface, offset)
        # Atmosfer aktorlerin ONUNDE: toz "odanin icinde" degil "kamerayla
        # oyuncu arasinda" olmali, yoksa zemin dokusu sanilir. Yanki
        # karartmasinin ALTINDA kaliyor - Yanki acikken hava da bulaniyor.
        if self.ambience is not None:
            self.ambience.draw(surface)

        # Sira: once dunya kararir (bedel), sonra gizli seyler o karanligi
        # delerek cikar (kazanc). Ters sirada Yanki acilinca ekran
        # aydinlaniyordu - bedel tam tersine donmustu.
        if self.echo is not None:
            echo_view.draw_dim(surface, self.echo)
            echo_view.draw_reveal(surface, offset, self.echo, self.player,
                                  self.enemies, self.breakables)
            echo_view.draw_answer(surface, offset, self.echo, self.player)

        # Iz Surme ayni yerde ama **karartma yok**: Yanki'nin bedeli
        # dunyanin kararmasi, Iz Surme'ninki dusmanlarin solmasi (o
        # `_draw_enemies`'de). Ayni gorseli kullansalardi "Ardo'nun
        # Yankisi" gibi okunurdu - oysa mesele farkli bir duyu olmasi.
        if self.tracking is not None:
            # Sira: once dunya agarir (isaret), sonra gecmis o soluklugun
            # icinden cikar. Yanki'nin sirasinin aynadaki hali - orada
            # once kararir sonra gizli seyler karanligi deler.
            tracking_view.draw_wash(surface, self.tracking)
            tracking_view.draw_traces(surface, offset, self.tracking,
                                      self.player, self.traces)
            tracking_view.draw_cracks(surface, offset, self.tracking,
                                      self.player, self.breakables)

        if self.game.debug_overlay:
            self._draw_hitboxes(surface, offset)
        self._draw_hud(surface)
        self.dialogue.draw(surface, self.game.frame)
        # Kart diyalogun USTUNDE ama Yanki saciliminin ALTINDA: bolum
        # adi her zeminde okunmali, ama Yanki acikken o da bulanir.
        if self.card is not None:
            self.card.draw(surface)
        self._draw_boss_bar(surface)
        self.draw_overlay(surface)

        # Kromatik kayma en son: arayuz dahil her seyin uzerine. Yanki
        # acikken oyuncu her seyi biraz daha zor goruyor.
        if self.echo is not None:
            echo_view.draw_fringe(surface, self.echo)

    def draw_background(self, surface, offset) -> None: ...

    def draw_foreground(self, surface, offset) -> None: ...

    def draw_overlay(self, surface) -> None: ...

    def _draw_boss_bar(self, surface) -> None:
        """Boss can bari - **her bolumde, otomatik.**

        `CLAUDE.md` 7: *"Dusman can bari yok. Sadece boss'larda bar
        var."* Bar `Boss.draw_health_bar` icinde ama cagirmak her
        bolumun kendi isiydi ve Bolum 6 unutmustu: BOSS 1'in cani hic
        gorunmuyordu (Arda, 30.08.2026). `DEVIR.md` 21 bu tuzagi bir
        kez zaten yakalamisti - "unutulmasin" demek yetmemis.

        Artik burada: `self.boss` varsa ve yasiyorsa cizilir. Bolum
        hicbir sey yapmiyor, dolayisiyla unutamiyor.
        """
        boss = getattr(self, "boss", None)
        if boss is None or getattr(boss, "dead", True):
            return
        boss.draw_health_bar(surface)

    def free_spot_near(self, x: float, y: float, body) -> tuple[float, float]:
        """Verilen govde icin yakinda **bos** bir yer bulur.

        Arda (30.08.2026): *"Oldukten sonra yeniden dene dedigimizde
        Ardo duvarin icinde kaliyor."* `after_restart` yoldasi
        oyuncunun 24 piksel soluna koyuyordu ve orasi bir duvar
        sutunuysa icinde sikisiyordu - `Companion` kendi kendini
        kurtarmiyor.

        Once istenen yer, sonra iki yana artan mesafeler deneniyor.
        Hicbiri olmazsa oyuncunun tam ustu (orasi kesin bos, oyuncu
        orada duruyor).
        """
        probe = body.rect.copy()
        for dx in (0, -14, 14, -28, 28, -44, 44, -60, 60):
            probe.x = int(x + dx - probe.width * 0.5)
            probe.y = int(y - probe.height)
            if not self.tilemap.solid_overlap(probe):
                return (x + dx, y)
        return (self.player.body.center_x, self.player.body.feet[1])

    # --- Game feel kancalari ------------------------------------------------
    def on_hit(self, box, target, result, direction) -> None:
        """Bir vurus degdi. **Ucu birden tek cagridan** - kare kaymasi olmasin."""
        weight = ImpactWeight.NORMAL
        if result.killed:
            weight = ImpactWeight.KILL
        elif box.is_finisher:
            weight = ImpactWeight.FINISHER

        self.juice.on_hit(
            ImpactEvent(
                x=target.body.center_x,
                y=target.body.center_y,
                direction=direction,
                weight=weight,
                particle_path="violet" if box.is_counter else "blood",
                particle_count=10 if box.is_finisher else 6,
            ),
            target_flash=target.flash,
            target_squash=target.squash,
        )

        if box.owner is self.player:
            self.total_hits += 1
            self.player.register_hit()
            self.game.play_sound(self._hit_sound(box, result),
                                 muffled=self._echo_active())
            if box.is_counter:
                self.show_toast(t("combat.counter"))
            if result.killed:
                # Kill cancel: recovery aninda kesilir, akis surer.
                self.player.notify_kill()

    def _hit_sound(self, box, result) -> str:
        if result.killed:
            return "hit_kill"
        if box.is_counter:
            return "hit_counter"
        if box.is_finisher:
            return "hit_heavy"
        return "hit_light"

    def _echo_active(self) -> bool:
        return self.echo is not None and self.echo.active

    def on_enemy_died(self, enemy) -> None:
        self.juice.explosion(enemy.body.center_x, enemy.body.center_y,
                             ImpactWeight.FINISHER)
        self.particles.burst(enemy.body.center_x, enemy.body.center_y, 16,
                             path="blood", speed=(1.0, 3.0))
        # Parcaciklar soner, leke kalir: koridora donunce dovusun izi durur.
        self.decals.splatter(enemy.body.center_x, enemy.body.feet[1], amount=10)
        # Ayni an `TraceField`'e de yaziliyor: leke CIZILMIS PIKSEL,
        # iz SORGULANABILIR VERI. Iz Surme "yakindakileri yasina gore
        # goster" diyor, pisirilmis bir yuzey bunu cevaplayamaz.
        self.traces.add(enemy.body.center_x, enemy.body.feet[1], BLOOD)
        # Bos dize = sessiz kal (orn. Sismek zaten patlama sesiyle oldu,
        # ustune binmesin - src/entities/enemies/bloated.py).
        if enemy.death_sound:
            self.game.play_sound(enemy.death_sound)

    def on_enemy_tell(self, enemy) -> None:
        """Tell basladi - hangi ses calinacagini dusmanin kendi tipi
        soyluyor (`Enemy.tell_sound`, varsayilan genel "enemy_tell")."""
        self.game.play_sound(enemy.tell_sound, muffled=self._echo_active())

    def on_climber_drop(self, enemy) -> None:
        """Tirmanan tavandan koptu - toz doksun, telegraf tamamlansin."""
        self.particles.burst(enemy.body.center_x, enemy.body.bottom, 5,
                             direction=(0.0, 1.0), path="dust",
                             speed=(0.2, 0.7), life=(10, 20), gravity=0.03)
        self.game.play_sound("climber_drop")

    def on_bloated_explode(self, enemy) -> None:
        """Patlama radyal - yonlu degil (docs/derinlestirme.md 1.2)."""
        self.juice.explosion(enemy.body.center_x, enemy.body.center_y,
                             ImpactWeight.KILL)
        self.particles.burst(enemy.body.center_x, enemy.body.center_y, 22,
                             path="spark", speed=(1.2, 3.6))
        self.decals.scorch(enemy.body.center_x, enemy.body.feet[1])
        self.traces.add(enemy.body.center_x, enemy.body.feet[1], SCORCH)
        self.game.play_sound("bloated_explode")

    def on_shield_block(self, enemy) -> None:
        """Vurus Kalkanli'nin kalkanina carpti (Katman 2, `shieldbearer.py`).

        Blok **hasar vermiyor** - ceza ritmi kaybetmek. Ama geri bildirim
        vurustan daha GURULTULU olmali: oyuncu "vurdum ama olmadi"
        belirsizligini bir kare bile yasamamali. Kivilcim + sert sarsinti
        + kalkan sesi, ucu birden `juice.on_hit`'ten degil ama ayni ruhla.
        """
        x = enemy.body.center_x + enemy.facing * 8
        self.juice.explosion(x, enemy.body.center_y, ImpactWeight.NORMAL)
        self.particles.burst(x, enemy.body.center_y, 8, path="spark",
                             speed=(0.8, 2.2))
        self.game.play_sound("enemy_blocked", muffled=self._echo_active())

    def on_shield_turn(self, enemy) -> None:
        """Kalkanli donmeye karar verdi - okunur olmali.

        Sessizce donmek "arkasindayim" sozlesmesini bozar; oyuncu bunu
        haksizlik olarak okur (docs/derinlestirme.md 4.2).
        """
        self.game.play_sound("enemy_tell", muffled=self._echo_active())

    def on_combo_threshold(self, player, threshold: int) -> None:
        # Saldirgan oynayan kademesini geri kazanir (DEVIR gorev 3.1).
        # Korkak oynayan iyilesemez - can siseleri nadir tutuluyor.
        # ONARIM yetenegi esigi dusuruyor (20 -> 14). Tabani degistirmiyor,
        # ustune indirim biniyor - `docs/dovus-sistemi.md`'nin sayilari
        # yerinde kaliyor.
        needed = COMBO_TO_RESTORE
        if self.player.skills:
            from src.systems import skilltree
            needed = max(1, needed
                         - skilltree.restore_combo_reduction(self.player.skills))
        if (threshold >= needed and self.echo is not None
                and self.echo.restore()):
            self.on_echo_tier_changed(self.echo.tier, gained=True)
        if threshold >= COMBO_THRESHOLD_HIGH:
            self.show_toast(t("combat.combo_echo", count=threshold))
        elif threshold >= COMBO_THRESHOLD_MID:
            self.show_toast(t("combat.combo_health", count=threshold))
        else:
            self.show_toast(t("combat.combo", count=threshold))

    def on_combo_reset(self) -> None: ...

    def on_player_attack(self, player, index: int) -> None:
        """Zincir bir sonraki vurusa gecti - degip degmemesinden bagimsiz,
        kilic her savrulduğunda calar (SES-LISTESI 1: "vurus degmese de
        calar")."""
        self.game.play_sound(
            "swing_heavy" if player.chain.is_finisher else "swing_light")

    def on_attack_swing(self, player, box) -> None:
        """Vurus kirilabilir duvara degdi mi?

        Hitbox sistemi yalnizca **varliklara** bakiyor; duvar bir tile.
        Burada ayrica sorulmasi gerekiyor - yoksa oyuncu duvara vurur ve
        hicbir sey olmaz.
        """
        broken: list[pygame.Rect] = []
        for rect in self.tilemap.breakable_rects():
            if not box.rect.colliderect(rect):
                continue
            tx = rect.x // TILE_SIZE
            ty = rect.y // TILE_SIZE
            if self.tilemap.break_at(tx, ty):
                broken.append(rect)
                self.particles.burst(rect.centerx, rect.centery, 8,
                                     path="dust", speed=(0.5, 1.8))
                self.decals.splatter(rect.centerx, rect.bottom, amount=4,
                                     path="soot", spread=7.0)
        if broken:
            self.juice.explosion(player.body.center_x, player.body.center_y,
                                 ImpactWeight.NORMAL)
            self.on_wall_broken(broken)

    def on_wall_broken(self, rects: list[pygame.Rect]) -> None:
        """Gizli gecit acildi. `rects` yikilan tile'lar.

        Hangi duvarin yikildigi bolume soyleniyor: bir bolumde birden fazla
        kirilabilir duvar olabiliyor ve hepsi ayni sey anlamina gelmiyor
        (Bolum 2: biri yolu aciyor, digeri gizli odayi).
        """
        self.show_toast(t("echo.wall_broken"), frames=120)

    def on_player_jump(self, player) -> None:
        self.particles.burst(player.body.feet[0], player.body.feet[1], 4,
                             direction=(0.0, -1.0), path="dust",
                             speed=(0.3, 0.9), life=(8, 16), gravity=0.04)
        self.game.play_sound("jump")

    def on_player_land(self, player, air_frames: int) -> None:
        self.particles.burst(player.body.feet[0], player.body.feet[1], 6,
                             direction=(0.0, -1.0), path="dust",
                             speed=(0.4, 1.2), life=(10, 20), gravity=0.05)
        hard = air_frames >= HARD_LAND_AIR_FRAMES
        self.game.play_sound("land_hard" if hard else "land_soft")

    def on_player_dodge(self, player) -> None:
        self.particles.burst(player.body.center_x, player.body.feet[1], 8,
                             direction=(-player.facing, 0.0), path="dust",
                             speed=(0.5, 1.6), life=(10, 22), gravity=0.03)
        self.game.play_sound("dodge")

    def on_dodge_trail(self, player) -> None:
        if player.dodge.frames_left % 3 == 0:
            self.particles.burst(player.body.center_x, player.body.center_y, 1,
                                 direction=(-player.facing, 0.0), path="echo",
                                 speed=(0.1, 0.4), life=(8, 14), gravity=0.0)

    def on_player_step(self, player) -> None:
        """Adim - hangi ses calinacagi sahnenin `footstep_sound`'undan gelir
        (zemine gore degil **sahneye** gore, bkz. sinif tanimi)."""
        self.game.play_sound(self.footstep_sound, muffled=self._echo_active())

    def on_player_hurt(self, player, result) -> None:
        self.show_toast(t("combat.hurt"))
        self.game.play_sound("player_hurt", muffled=self._echo_active())

    def on_echo_tier_changed(self, tier: int, gained: bool) -> None:
        """Kademe degisti. Asamali aciga cikarma: yalnizca **degisince**
        gosteriliyor (CLAUDE.md 9)."""
        # Anahtarlar **acikca** yazili: f-string ile kurulan anahtari
        # tests/test_lang.py kaynak taramasinda goremiyor ve "olu anahtar"
        # sayiyor. Bu tuzaga ikinci kez dusuldu.
        self.show_toast(t("echo.tier_up" if gained else "echo.tier_down"),
                        frames=120)
        self.game.play_sound("echo_tier_up" if gained else "echo_tier_down",
                             bus="volume_echo")

    def on_player_died(self, player) -> None:
        # Olunce Yanki bir kademe zayiflar. Dip SESSIZ - daha asagi inmez,
        # olum sarmali boyle engelleniyor (docs/gdd.md 4).
        if self.echo is not None and self.echo.weaken():
            self.on_echo_tier_changed(self.echo.tier, gained=False)
        self.game.play_sound("player_death")
        self.death_frames = DEATH_SCREEN_DELAY

    def _open_death_screen(self) -> None:
        """Olum ekranini acar.

        **Toast yeterli degildi** (Arda, 29.08.2026 canli oynanis: *"boss
        fight'ta olunce kaldik oyle, hicbir sey yapilmiyor"*). `restart()`
        calisiyordu ama onu soyleyen yazi 72 karede sonuyor ve oyuncu
        hareketsiz bir ekranla bas basa kaliyordu. Gecici bir bildirim
        kalici bir durumu anlatamaz.

        Gecikme bilincli: olum vurusunun hitstop'u, sarsintisi ve
        parcaciklari once bitsin. Menu aninda acilirsa oyuncu neyle
        oldugunu goremiyor.
        """
        from src.ui.death import DeathScene
        self.scenes.push(DeathScene, save_data=self.save_data,
                         room_label=self.room_label(),
                         on_retry=self.restart)

    def room_label(self) -> str:
        """Olum ekraninda gosterilecek yer.

        **Bolum adi KULLANILMIYOR.** Ilk surum onu gosteriyordu ve Bolum
        6'da ekranda "ARDO - odanin basindan" yaziyordu: bolumun adi ama
        oyuncu bir KARAKTER adi okuyor ve "Ardo'nun odasi mi?" diye
        soruyor. Belirsiz bir etiket, etiketsizlikten kotudur.

        Oda adlari ic anahtar (`vana_odasi`, `arena`) ve cevrilmiyor;
        cevirmek her bolume dokuz anahtar eklerdi. Onun yerine ekran
        **numarayi** soyluyor - hangi bolumde oldugu zaten belli, eksik
        olan bilgi "bastan mi basliyorum" sorusuydu ve ona `death.resume_at`
        cevap veriyor.
        """
        return str(self.chapter_number) if self.chapter_number else ""

    def on_ability_gained(self, ability: str) -> None:
        """Yetenek kazanildi. Bir sey **kazanmis** olmali - sessiz gecmesin.

        Paylasilan (chapter01.py'den tasindi): her bolum kendi yetenek
        anini yasiyor, ama "kazanmak" hep ayni goruntu/ses/yaziya sahip
        olmali - dagitilsaydi biri farkli hissettirirdi.
        """
        self.show_toast(t(abilities.label_key(ability)), frames=180)
        self.pickup_juice()

    def pickup_juice(self, gold: bool = False) -> None:
        """Bir sey kazanmanin GORUNTUSU - yaziyi cagiran belirler.

        `gold=True` altin sesini caliyor. Ses paketinde `gold_pickup`
        vardi ama **hicbir yerden cagrilmiyordu**: sandiklar da altin
        da genel `item_pickup` sesini kullaniyordu ve para sesi hic
        duyulmuyordu. `tests/test_audio.py` bunu ilk calistirmasinda
        buldu.

        `on_ability_gained`'dan ayrildi: anahtar, tilsim, silah gibi
        yetenek OLMAYAN kazanimlar da ayni parlama/parcacik/sesi
        kullanmali ama kendi yazisini yazmali. Once anahtar icin
        `on_ability_gained("")` cagirmistim - `abilities.label_key("")`
        "?" donuyor ve ekranda soru isareti cikiyordu.
        """
        self.juice.explosion(self.player.body.center_x,
                             self.player.body.center_y, ImpactWeight.NORMAL)
        self.particles.burst(self.player.body.center_x,
                             self.player.body.center_y, 14,
                             path="spark", speed=(0.6, 2.2))
        self.game.play_sound("gold_pickup" if gold else "item_pickup")

    def _emit_particles(self, event: ImpactEvent) -> None:
        self.particles.burst(event.x, event.y, event.particle_count,
                             direction=event.direction, path=event.particle_path)

    def show_toast(self, message: str, frames: int = 72) -> None:
        self.toast = message
        self.toast_frames = frames

    def _draw_hitboxes(self, surface: pygame.Surface,
                       offset: tuple[int, int]) -> None:
        ox, oy = offset
        for box in self.hitboxes.boxes:
            pygame.draw.rect(surface, palette.color("danger_bright"),
                             box.rect.move(-ox, -oy), 1)
        for actor in [self.player, *self.enemies]:
            pygame.draw.rect(surface, palette.color("echo"),
                             actor.hurtbox.move(-ox, -oy), 1)

    def _draw_hud(self, surface: pygame.Surface) -> None:
        # Asamali aciga cikarma: bilgi yalnizca ilgili oldugunda gorunur.
        self.hud.draw(surface, self.player, self.gold, self.echo_tier)
        if self.toast_frames > 0:
            text.draw(surface, self.toast, INTERNAL_WIDTH // 2, 42,
                      color=palette.color("violet_bright"), align="center",
                      outline=True)

    def debug_lines(self) -> list[str]:
        return [
            *self.player.debug_lines(),
            f"hitbox {self.hitboxes.active_count}  "
            f"parcacik {self.particles.alive_count}  "
            f"sarsinti {self.juice.shake.frames_left}",
            f"dusman {len(self.enemies)}  hak {self.tokens.active_count}  "
            f"leke {self.decals.count}",
        ]
