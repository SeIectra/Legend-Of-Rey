# LORE — Legend of Rey: Echoes

2D yandan kaydırmalı aksiyon-platformer. Samsung tuşlu telefonlardaki
*Forgotten Warrior*'dan ilham alır: silahsız başlarsın, gizlice vurursun,
ilerledikçe kılıcı ve büyüleri kazanırsın.

> **Durum:** Faz 1–6 tamamlandı (motor, sanat üretimi, oynanış, dünya,
> düşmanlar, arayüz). Act I oynanabilir. Kalan içerik için
> [docs/ROADMAP.md](docs/ROADMAP.md).

## Hikâye

Aethelmoor'da *Bölünme* dünyanın Özü'nü paramparça etti. Kırılan anılar
"Yankı" olarak geride kaldı. Rey uyurken Kül Korosu kardeşi Ardo'yu
kaçırır; ağabeyi Cael sesiyle ona yol gösterir — ama Cael'in kendisi de bir
yankıdır.

**Rey** — esmer, uzun koyu saçlı bir kadın savaşçı. Silahsız başlar; Echobrand'i
Act I'in sonunda kuşanır.

## Kurulum

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
.venv/Scripts/python run.py
```

Linux/macOS'ta `.venv/bin/python`. Python 3.11+ gerekir.

## Kontroller

| Tuş | Eylem |
|-----|-------|
| `←` `→` / `A` `D` | Hareket |
| `Space` / `W` / `↑` / `Z` | Zıpla — **basılı tut = daha yüksek** |
| `J` / `X` | Saldır (kılıçla 3'lü kombo) |
| `Shift` / `L` | Atılma *(Act I sonunda açılır)* |
| `E` | Etkileşim (sandık, kapı, Echo Shrine) |
| `Esc` | Duraklat |
| `F3` `F11` `F12` | Hata ayıklama · Tam ekran · Ekran görüntüsü |

Gamepad desteklenir (A zıpla, X saldır, RB atılma, Start duraklat).

### Kaçınma

Üç yolu var, sırayla açılırlar:

1. **Baştan itibaren:** düşmanın kırmızı yanıp sönen *hazırlık pozunu* gör ve
   menzilden çık. Her saldırının uyarısı vardır; zorluk tepki hızından değil,
   ne zaman geri çekileceğine karar vermekten gelir.
2. **Zıplama:** yerdeki saldırıların çoğu havada ıskalar.
3. **Atılma** (`Shift`) — Act I sonunda açılır. 50 piksel ileri sıçrar ve
   **süresince hasar almazsın** (i-frame). Saldırıyı iptal edip atılabilirsin;
   akıcı savaşın anahtarı budur. 0.42 saniye bekleme süresi var.

## Oynanış

**Silahsız başlarsın.** Act I boyunca tek gerçek saldırın **sırttan vuruş**:
seni fark etmemiş bir düşmana arkadan vurmak üç kat hasar verir ve goblini tek
vuruşta düşürür. Koşarak yaklaşırsan ayak sesin seni ele verir — yavaş git.

**Her düşman saldırmadan önce hazırlanır.** Kırmızı yanıp sönen hazırlık pozunu
görürsün: kaç, vur ya da beklemeyi seç. Zorluk tepki hızından değil, karardan
gelir.

**Essence** hem para hem tecrübe. Düşenler sana doğru çekilir.

## Teknik

- **480×270 sanal çözünürlük**, tam sayı katıyla ölçeklenir → keskin pixel art
- **Sabit 1/60 zaman adımı** → fizik makineden bağımsız ve deterministik
- **Prosedürel sanat**: tüm sprite, tile, efekt ve arka planlar kodla üretilir;
  tek palet, tutarlı stil, sıfır dış asset bağımlılığı
- **Dinamik 2B ışıklandırma**, parçacık sistemi, hitstop, travma tabanlı
  ekran sarsıntısı, Act'e göre renk derecelendirme
- **Veri odaklı bölümler**: ASCII harita + JSON, kodda bölüm mantığı yok

## Geliştirme

```bash
python tools/make_levels.py     # Bölüm tasarla + doğrula
python tools/smoke_test.py      # Uçtan uca başsız test
python tools/combat_test.py     # Savaş sistemleri
python tools/sprite_sheet.py    # Sprite kontakt sayfası
```

Mimari notlar: [CLAUDE.md](CLAUDE.md) · Yol haritası: [docs/ROADMAP.md](docs/ROADMAP.md)

`legacy/` ilk sürümün kaynağıdır; referans olarak duruyor, çalışmıyor.

## Erişilebilirlik

Ayarlar menüsünden ekran sarsıntısı ve flaş şiddeti tamamen kapatılabilir.
Fotosensitivite bir tercih değil, bir gerekliliktir.

## Geliştirici

Arda Güner — <ardaguner2000@gmail.com> · [ardeko.itch.io](https://ardeko.itch.io/legend-of-rey)

Lisans: [LICENSE](LICENSE)
