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
| `rey` | 48x40 | 34 | 44 | Oynanabilir - Yankisoyleyen |
| `ardo` | 48x40 | 34 | 44 | Oynanabilir - yabanci |
| `shambler` | 40x36 | 31 | 44 | Katman 1 - Suruklenen |
| `climber` | 40x36 | 30 | 44 | Katman 1 - Tirmanan |
| `bloated` | 40x36 | 31 | 44 | Katman 1 - Sismek |
| `cemo` | 40x32 | 27 | 44 | Rey'in kucuk kardesi - menu 5. asama |

**Animasyon durumlari (kare sayisi):** attack1 (5) · attack2 (5) · attack3 (5) · death (6) · dodge (2) · fall (4) · hurt (2) · idle (6) · jump (1) · run (8)

Her karakter bu durumlarin tamamini uretir; toplam kare sayisi bu
yuzden kadroda ayni.

## Palet

Tek kaynak: `tools/palette.json` - **32 renk**, 
degistirilemez. `src/art/palette.py` okur ve palet disi her rengi 
`PaletteError` ile reddeder. Golge zincirleri (14 adet) rampalar arasi gecerek renk 
sinirini asmadan tonlama saglar.

## Font

`src/ui/font_data.py` - 5x11 bitmap, tam Turkce seti. Eksik glif 
sessizce dusmez, konsola rapor edilir.

## Dil

`src/ui/lang/tr.json` (kanonik) ve `en.json`. Anahtar paritesi 
`tests/test_lang.py` ile korunuyor.

## Ses

Henuz yok. Gorev 10.
