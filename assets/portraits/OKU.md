# Elle çizilmiş portreler

Bu klasöre `<ad>.png` koyarsan oyun **prosedürel portre yerine onu**
kullanır. Dosya yoksa hiçbir şey bozulmaz — kod ürettiğini çizmeye
devam eder. Yani birini çizip ötekileri sonraya bırakabilirsin.

## Kurallar

| | |
|---|---|
| **Boyut** | `64 × 96` piksel (bust — göğüsten yukarısı) |
| **Kafa yüksekliği** | ~40 piksel (satır 7 → 47) |
| **Palet** | 37 renk, `tools/palette.json`. Dışına çıkma. |
| **Şeffaflık** | Arka plan tamamen saydam (alfa 0) |
| **Işık** | **Sol üstten**, istisnasız — bütün oyun böyle |

Beklenen dosya adları: `rey.png`, `ardo.png`, `cemo.png`

## Çizim yöntemi

Referansın kendi teknik notu doğru:

1. Önce `64×96`'da çiz (ya da `72×108` çizip küçült).
2. Büyütürken **nearest-neighbor** kullan.
3. **Anti-aliasing, blur, gradient yok.** Temiz piksel kümeleri.
4. Siluet güçlü olsun — tek renge indirdiğinde kim olduğu anlaşılmalı.

## Bitirince

```
python tools/quantize.py assets/portraits/rey.png
```

Bu, paletin dışına taşan pikselleri en yakın palet rengine çeker.
`CLAUDE.md` §6 bağlayıcı: *kaynağı ne olursa olsun her görsel bu
filtreden geçer.*

Atlarsan oyun yine çalışır ama açılışta uyarı yazar ve renkler öteki
varlıklarla tutmaz.

## Anatomi şeması (prosedürel portrenin kullandığı satırlar)

Bunlara uymak zorunda değilsin — ama uyarsan portre, diyalog kutusu ve
sinematik yakın çekimleriyle aynı hizada durur.

```
  7  kafatasının tepesi
 17  saç çizgisi
 24  kaş çizgisi
 27  göz çizgisi      ← kafanın dikey ortası
 32  elmacık kemiği
 36  burun tabanı
 41  ağız
 43  çene köşeleri
 47  çenenin ucu
 46  boyun başlangıcı
 57  omuz
```

İki göz arası mesafe = **bir göz genişliği**. Bu şemadan çıkınca yüz
hemen bozuluyor; ilk sürümde gözler 8 piksel arayla duruyordu ve şaşı
görünüyordu.
