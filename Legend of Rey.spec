# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller paket tanimi - tester surumu.

## Bu dosya bir kez SESSIZCE bozuldu

Onceki surum yalnizca `assets` klasorunu paketliyordu. Ama oyun uc yerden
daha diskten okuyor ve ikisi `assets` altinda **degil**:

    tools/palette.json     37 rengin tek kaynagi (`src/art/palette.py`)
    src/ui/lang/*.json     Turkce/Ingilizce metinler (`src/ui/i18n.py`)

Ikisi de eksik oldugu icin paketlenen oyun **acilir acilmaz cokerdi** -
ve bu, calistirilana kadar gorunmezdi. `tests/test_build.py` artik
kaynaktaki her disk yolunu tarayip burada bildirildigini dogruluyor;
yeni bir varlik klasoru eklenip buraya yazilmazsa test kiriliyor.

## Neyin paketlenmedigi de bilincli

    assets/portraits/kaynak/   yuksek cozunurluklu asillar (5.7 MB) -
                               yalnizca yeniden uretim icin, oyun
                               64x96 olanlari okuyor
    assets/*.md                belgeler
    docs/, tools/, tests/      gelistirme

## console=True - bilerek

Bir tester surumunde cokme **gorunur** olmali. Konsol kapaliysa oyun
sessizce kapaniyor ve elimizde hicbir sey kalmiyor; acikken tester
ekran goruntusu alabiliyor. Yayin surumunde `False` olacak.
"""

DATAS = [
    # Palet - `src/art/palette.py` acilista okuyor. Olmazsa oyun baslamaz.
    ('tools/palette.json', 'tools'),
    # Diller - `src/ui/i18n.py`. Olmazsa her metin anahtar adi olarak cikar.
    ('src/ui/lang', 'src/ui/lang'),
    # Muzik (53 MB) ve logo.
    ('assets/audio', 'assets/audio'),
    ('assets/logo', 'assets/logo'),
    # Elle cizilmis portreler ve ara sahne panelleri. Klasor bos olsa da
    # kalsin: oyun once diske bakip yoksa prosedurele donuyor.
    ('assets/portraits/rey.png', 'assets/portraits'),
    ('assets/portraits/ardo.png', 'assets/portraits'),
    ('assets/portraits/cemo.png', 'assets/portraits'),
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=DATAS,
    hiddenimports=[
        # Bolumler ve sahneler `importlib` ile **ada gore** yukleniyor
        # (`main.py` SCENES, `chapter*.py` ENEMY_CLASSES). PyInstaller
        # statik analizle bunlari goremiyor - tek tek bildirilmezse
        # paketlenen oyun "modul yok" diye coker.
        # **Duz dize, uretilmis degil.** Ilk surum
        # `f'src.scenes.chapter{n:02d}'` yaziyordu; PyInstaller onu
        # dogru cozerdi ama `tests/test_build.py` goremezdi - ve
        # bu projede tam olarak o tuzak dort kez patladi (dil
        # anahtarlari, ses adlari, panel onekleri, bu).
        # Denetlenemeyen bir liste, olmayan bir listedir.
        'src.scenes.chapter01',
        'src.scenes.chapter02',
        'src.scenes.chapter03',
        'src.scenes.chapter04',
        'src.scenes.chapter05',
        'src.scenes.chapter06',
        'src.scenes.chapter07',
        'src.scenes.chapter08',
        'src.scenes.chapter09',
        'src.scenes.chapter10',
        'src.scenes.chapter11',
        'src.scenes.chapter12',
        'src.scenes.chapter13',
        'src.scenes.chapter14',
        'src.scenes.chapter15',
        'src.world.rooms.chapter01',
        'src.world.rooms.chapter02',
        'src.world.rooms.chapter03',
        'src.world.rooms.chapter04',
        'src.world.rooms.chapter05',
        'src.world.rooms.chapter06',
        'src.world.rooms.chapter07',
        'src.world.rooms.chapter08',
        'src.world.rooms.chapter09',
        'src.world.rooms.chapter10',
        'src.world.rooms.chapter11',
        'src.world.rooms.chapter12',
        'src.world.rooms.chapter13',
        'src.world.rooms.chapter14',
        'src.world.rooms.chapter15',
        'src.scenes.intro',
        'src.scenes.prologue',
        'src.scenes.combat_room',
        'src.scenes.foundation_check',
        'src.ui.menu',
        'src.scenes.chapter02_cinematics',
        'src.scenes.chapter03_cinematics',
        'src.scenes.chapter06_cinematics',
        'src.scenes.chapter07_cinematics',
        'src.scenes.chapter08_cinematics',
        'src.scenes.chapter09_cinematics',
        'src.scenes.chapter10_cinematics',
        'src.scenes.chapter12_cinematics',
        'src.scenes.chapter13_cinematics',
        'src.scenes.chapter14_cinematics',
        'src.scenes.chapter15_cinematics',
        'src.entities.enemies.shambler',
        'src.entities.enemies.climber',
        'src.entities.enemies.bloated',
        'src.entities.enemies.bloated_one',
        'src.entities.enemies.shieldbearer',
        'src.entities.enemies.spearman',
        'src.entities.enemies.archer',
        'src.entities.enemies.commander',
        'src.entities.enemies.silent',
        'src.entities.enemies.echoing',
        'src.entities.enemies.splitter',
        'src.entities.enemies.shadow_shambler',
        'src.entities.enemies.extinguished_one',
        'src.entities.bosses.rotted_one',
        'src.entities.bosses.gaoler',
        'src.entities.bosses.source',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Legend of Rey',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    # Tester surumu: cokme gorunur olsun. Gerekce dosya basliginda.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
