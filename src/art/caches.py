"""Yuzey onbelleklerinin tek elden temizlenmesi.

## Neden var

Arda, canli oynanis (29.08.2026): *"Oyunun tam ekran / pencereli ayarini
degistirdiginde oyun donuyor."*

Sebep `set_mode`'un kendisi degil, **ondan sonra olan sey**. Bu projede
uretilen her yuzey `convert()` / `convert_alpha()` goruyor (`CLAUDE.md` 4:
*"unutulursa oyun 3-5 kat yavaslar"*) ve donusum **o anki ekranin piksel
bicimine** gore yapiliyor. `pygame.display.set_mode()` ekrani yeniden
kurunca bicim degisebiliyor; onbellekteki butun sprite'lar, karolar,
portreler ve vinyetler bir anda **yanlis bicimde** kaliyor.

Pygame bunu bir hata olarak bildirmiyor - sessizce her blit'te tek tek
donusturuyor. Karede yuzlerce blit oldugu icin sonuc tam olarak "donma"
gibi gorunuyor: oyun calisiyor ama saniyede birkac kare.

Ayni ders bir kez `postfx` icin ogrenilmisti: renk korlugu moduna
gecince sahne yeni renklerde, vinyet eski tonda kaliyordu. O zaman tek
bir onbellek elle eklenmisti. Uc onbellek daha eklendikten sonra elle
tutmak surdurulemez oldu - burasi tek liste.

## Yeni bir onbellek eklerken

Buraya da ekle. `tests/test_display.py` kaynagi tarayip `src/` altinda
tanimli her yuzey onbelleginin bu listede oldugunu dogruluyor; unutursan
test kirilir. Guvence bir yorumda degil, testte.
"""
from __future__ import annotations


def invalidate_all() -> None:
    """Ekran yeniden kurulunca cagrilir - bayat bicimli her yuzeyi atar.

    Import'lar **fonksiyonun icinde**: bu modul `pygame.init()`'ten once
    de import edilebiliyor ve alt moduller yuklenirken yuzey uretmeye
    kalkarsa patlar. Ayrica cagri seyrek (yalnizca ayar degisiminde),
    yani import maliyeti onemsiz.
    """
    from src.art import animator, portrait, postfx, tileset
    from src.scenes import staging
    from src.ui import echo_view, text

    animator.clear_cache()
    tileset.clear_cache()
    postfx.clear_cache()
    portrait.clear_cache()
    echo_view.clear_cache()
    text.clear_cache()
    # Ara sahne panelleri de diskten gelen YUZEY: hem ekran bicimi
    # hem renk korlugu modu degisiminde bayatliyor. Testin tarayicisi
    # `src/scenes` altina bakmadigi icin bunu yakalayamadi - kural
    # yine de gecerli (`CLAUDE.md`: guvence yorumda degil testte, ama
    # test kapsami disi kalan yeri de biz kapatiriz).
    staging.clear_panel_cache()
