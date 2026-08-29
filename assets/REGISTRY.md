# ASSET KAYDI

`CLAUDE.md` 6: uretilen her asset buraya kaydedilir.

**Bu projede sprite'lar PNG degil.** Hepsi `src/art/spritegen.py`
icindeki `draw_humanoid()` ile **calisma zamaninda** uretiliyor;
disk uzerinde sprite dosyasi yok. Bu yuzden kayit "hangi dosya"
degil, **hangi spec** sorusunu cevapliyor.

> Bu dosya `tools/registry.py` tarafindan uretilir. **Elle
> duzenleme** - spec degisince araci yeniden calistir.

## Karakterler

Uretici: `src/art/spritegen.py :: draw_humanoid(spec, pose)`  
Spec'ler: `src/art/animation.py :: CHARACTERS`

| Ad | Hucre | Taban (foot_y) | Kare | Rol |
|---|---|---|---|---|
| `rey` | 48x40 | 34 | 50 | Oynanabilir - Yankisoyleyen |
| `rey_armed` | 48x40 | 34 | 50 | Rey, kilic kusanmis (Bolum 1 sonrasi) |
| `rey_dagger` | 48x40 | 34 | 50 | Rey + Hancer (Bolum 2 mini-boss odulu) |
| `rey_axe` | 48x40 | 34 | 50 | Rey + Balta (Bolum 2 mini-boss odulu) |
| `ardo` | 48x40 | 34 | 50 | Oynanabilir - yabanci |
| `ardo_dagger` | 48x40 | 34 | 50 | Ardo + Hancer (Bolum 2 mini-boss odulu) |
| `ardo_axe` | 48x40 | 34 | 50 | Ardo + Balta (Bolum 2 mini-boss odulu) |
| `cemo` | 40x32 | 27 | 50 | Rey'in kucuk kardesi - menu 5. asama |
| `villager` | 40x38 | 32 | 50 | Bolum 1 koylusu - olay patlayinca evine kaciyor |
| `shambler` | 40x36 | 31 | 50 | Katman 1 - Suruklenen |
| `climber` | 44x34 | 28 | 50 | Katman 1 - Tirmanan |
| `bloated` | 44x40 | 34 | 50 | Katman 1 - Sismek |
| `shieldbearer` | 44x40 | 34 | 50 | Katman 2 - Kalkanli (AI VAR, B5'te tanitiliyor) |
| `spearman` | 56x40 | 34 | 50 | Katman 2 - Mizrakli (sanat var, AI yok) |
| `archer` | 48x40 | 34 | 50 | Katman 2 - Okcu (sanat var, AI yok) |
| `commander` | 52x48 | 41 | 50 | Katman 2 - Komutan (sanat var, AI yok) |
| `silent` | 44x40 | 34 | 50 | Katman 3 - Sessiz (sanat var, AI yok) |
| `echoing` | 48x42 | 36 | 50 | Katman 3 - Yankilayan (sanat var, AI yok) |
| `splitter` | 48x42 | 36 | 50 | Katman 3 - Bolunen (sanat var, AI yok) |

**Animasyon durumlari (kare sayisi):** attack1 (5) · attack2 (5) · attack3 (5) · death (6) · dodge (2) · fall (4) · hurt (2) · idle (6) · jump (1) · land (3) · run (8) · turn (3)

Her karakter bu durumlarin tamamini uretir; toplam kare sayisi bu
yuzden kadroda ayni.

## Portreler

Uretici: `src/art/portrait.py :: draw_portrait(spec)`  
Spec'ler: `src/art/portrait.py :: PORTRAITS`

| Ad | Boyut | Rol |
|---|---|---|
| `rey` | 64x96 | Diyalog + karakter secimi |
| `ardo` | 64x96 | Diyalog + karakter secimi |
| `cemo` | 64x96 | Diyalog |

**Neden ayri bir varlik sinifi:** oyun ici sprite'ta kafa ~7 piksel ve 
goz kapagi/iris/highlight/burun kumesi/dudak oraya sigmiyor. Sprite'i 
buyutmek de mumkun degil - oyunun en dar gecidi 2 tile = 32 piksel 
(olculdu, `tests/test_sprites.py` koruyor). Portrede kafa 40 piksel ve 
istenen her sey gercekten ciziliyor.

Yanki'nin portresi **yok**: kafanin icindeki sesin yuzu olmaz (ayni 
gerekce onun diyalog kutusunu da kaldirmisti).

## Palet

Tek kaynak: `tools/palette.json` - **37 renk**, 
degistirilemez. `src/art/palette.py` okur ve palet disi her rengi 
`PaletteError` ile reddeder. Golge zincirleri (15 adet) rampalar arasi gecerek renk 
sinirini asmadan tonlama saglar.

## Font

`src/ui/font_data.py` - 5x11 bitmap, tam Turkce seti. Eksik glif 
sessizce dusmez, konsola rapor edilir.

## Dil

`src/ui/lang/tr.json` (kanonik) ve `en.json`. Anahtar paritesi 
`tests/test_lang.py` ile korunuyor.

## Ses

`src/audio/sfx.py :: SFX` - **71 efekt**, hepsi calisma zamaninda 
sentezleniyor (numpy). Sprite'lar gibi: diskte dosya yok, kaynak koddur. 
Her tekrarli ses +-%8 rastgele perdeyle calinir (`CLAUDE.md` 7).

**Muzik yok.** Donguli/surekli sesler bilerek kaldirildi (Arda: *"cizirti gibi, 
rahatsiz edici"*); altyapi (`play_loop`/`stop_loop`) duruyor.
