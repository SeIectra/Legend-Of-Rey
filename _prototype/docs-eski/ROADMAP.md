# LORE — Legend of Rey: Echoes
## Geliştirme Yol Haritası

> **Tür:** 2D yandan kaydırmalı aksiyon-platformer / hafif metroidvania
> **İlham:** Samsung tuşlu telefonlardaki *Forgotten Warrior* (2004, J2ME)
> **Motor:** Python 3.13 + pygame-ce
> **Hedef:** 28 bölüm, 5 Act, 6 boss, kilitli 60 FPS

---

## 0. Tasarım Sütunları

Her karar bu dört sütuna hizmet eder. Bir özellik hiçbirine hizmet etmiyorsa yapılmaz.

| # | Sütun | Anlamı |
|---|-------|--------|
| 1 | **Ağırlığı hissettir** | Her vuruşun hitstop'u, geri tepmesi, toz efekti, ekran sarsıntısı var. Zıplama yerçekimiyle konuşur. |
| 2 | **Silahsızdan efsaneye** | Rey yumrukla başlar, kılıcı Act II'de alır, büyüleri sonra. Güç kazanımı hikâyeyle aynı eğride. |
| 3 | **Ekran bir tuzaktır** | Forgotten Warrior'ın "her ekran bir bulmaca" ritmi: oda oda tasarım, her odanın tek bir net fikri var. |
| 4 | **Işık anlatır** | Dinamik 2D ışıklandırma bir grafik özelliği değil, yön bulma aracı. Karanlık tehdit, ışık güvenliktir. |

---

## 1. Hikâye İskeleti

**Dünya:** Aethelmoor. *Bölünme* (The Sundering) sırasında dünyanın Özü (Essence) paramparça oldu. Kırılan anılar "Yankı" (Echo) olarak geride kaldı — bazıları yürüyor, bazıları saldırıyor.

**Kurulum (Forgotten Warrior'a saygı duruşu):** Rey uyurken **Kül Korosu** (Ashen Choir) kardeşi Ardo'yu kaçırır. Rey'i uyandıran, ona yol boyunca sesiyle rehberlik eden abisi Cael'dir — ama Cael'in kendisinin de bir Yankı olduğu Act III'te ortaya çıkar.

**Dönüm noktaları**
- Act I sonu: Rey silahsızdır; Gaoler'ı kaçarak/tuzaklarla yener.
- Act II başı: Ata kılıcı **Echobrand** bulunur.
- Act III: Cael'in bir yankı olduğu ortaya çıkar; ilk büyü (**Ember**) kazanılır.
- Act IV: Ardo'nun kendi isteğiyle gittiği ortaya çıkar.
- Act V: Son boss **The Forgotten** — Rey'in kendi yankısı. İki final: Yankıyı emmek ya da bırakmak.

---

## 2. Act ve Bölüm Yapısı (28 bölüm)

| Act | Ad | Bölüm | Yeni Mekanik | Boss |
|-----|-----|-------|--------------|------|
| I | **The Waking Hollow** | 5 | Koşu, değişken zıplama, gizlilik, sırttan vuruş | The Gaoler (kovalamaca) |
| II | **Emberfall Woods** | 6 | Echobrand: 3'lü kombo, hava saldırısı, pogo | Thornmaw (2 faz) |
| III | **The Drowned Vault** | 6 | Yüzme, akıntı, **Ember** büyüsü, parry | Tidewrack (3 faz) |
| IV | **The Ashen Spire** | 6 | Duvar sıçraması, çift zıplama, **Blink** | Choirmaster Vex (3 faz) |
| V | **Echo of the Sundering** | 5 | Hepsi + **Quake**, yerçekimi tersleme | The Forgotten (4 faz) |

Her Act: 1 giriş bölümü, 3-4 ana bölüm, 1 boss arenası, 1 gizli oda. Act aralarında **Echo Shrine** hub'ı: dükkân, yetenek ağacı, kayıt.

---

## 3. Mekanik Tasarım

### Hareket (his ayarları)
| Parametre | Değer | Neden |
|-----------|-------|-------|
| Coyote time | 6 kare | Kenardan düşünce "haksızlık" hissini siler |
| Jump buffer | 8 kare | Erken basılan zıplama tuşu yutulmaz |
| Değişken zıplama | Tuş bırakınca yukarı hız × 0.45 | Yükseklik kontrolü |
| Apex hang | Tepe noktasında yerçekimi × 0.55 | Havada kontrol hissi |
| Dash | 0.18 sn, 7 kare i-frame | Kaçış + saldırı aracı |

### Savaş
- **3'lü yer kombosu** (hafif-hafif-savurma), her vuruşta artan hitstop
- **Yüklü ağır saldırı** — zırh kırar
- **Pogo** (aşağı-saldırı) — düşman/dikene basıp zıplama
- **Parry** — 8 karelik pencere, mükemmel parry Essence verir
- **Sırttan vuruş** — uyarısız düşmana ×3 hasar (Act I'in tek saldırı yolu)
- **i-frame** hasar sonrası 45 kare, yanıp sönme

### İlerleme
- **Essence** — hem para hem XP (isim buradan geliyor)
- **Yetenek ağacı**, 3 dal: *Blade* (hasar/kombo), *Ward* (savunma/parry), *Echo* (büyü/kaynak)
- **Kalp Parçaları** — 4 tanesi 1 kalp
- **Tılsımlar (Charms)** — pasif değiştiriciler, sınırlı slot
- **Dükkân** — iksir, büyü, tılsım (Forgotten Warrior'daki altın→büyü/iksir sistemi)

### Düşman Yelpazesi
Grunt · Archer · Ceiling Spider · Skeleton (dirilir) · Shield Brute (parry gerekir) · Wisp (uçar) · Bomber · Assassin (görünmez) · Choir Mage (kalkan verir)

Her düşman gerçek bir **durum makinesi**: `idle → alert → chase → windup → attack → recover → stagger → dead`. Windup fazı her zaman görsel olarak okunur (renk flaşı + poz).

---

## 4. Teknik Mimari

```
lore/
├── core/       app · scene · input · assets · audio · config · save · camera · mathx
├── gfx/        palette · forge (prosedürel sanat) · sprites · tiles · particles
│               lighting · postfx · text · ui
├── world/      tilemap · level · props · parallax
├── entities/   entity · player · enemies · projectile · pickups
├── systems/    physics · combat · progression
├── scenes/     boot · title · play · pause · settings
└── data/       levels/*.json · enemies.json · items.json
```

**Temel kararlar**
- **Sanal çözünürlük 480×270**, tam sayı katlarıyla ölçeklenir → keskin pixel art, her ekranda aynı görüntü
- **Sabit zaman adımı** (1/60) + interpolasyonlu çizim → fizik makineden bağımsız, deterministik
- **Sahne yığını** (scene stack) → pause menüsü oyunu üstüne biner, iç içe event loop yok
- **Aksiyon eşlemesi** → `jump`, `attack` gibi soyut aksiyonlar; klavye/gamepad/yeniden atama ücretsiz gelir
- **Veri odaklı seviyeler** → JSON; yeni bölüm için kod yazılmaz
- **Prosedürel sanat üretimi** → sprite/tile/efektler kodla üretilir, tek palet, tutarlı stil, sürüm kontrolünde metin olarak yaşar

---

## 5. Fazlar

### Faz 0 — Temizlik ✅
Eski modüller `legacy/`'ye taşındı (git geçmişi korundu). Yeni `lore/` paketi kuruldu.

### Faz 1 — Motor Çekirdeği
`app` (sabit zaman adımı, sanal çözünürlük, tam ekran) · `scene` yığını · `input` aksiyon eşlemesi + buffer · `assets` önbellek · `audio` bus'ları · `config`/`save` JSON · `camera` (deadzone, lookahead, trauma-tabanlı sarsıntı) · `mathx`

### Faz 2 — Sanat Forge'u
Palet · prosedürel karakter/düşman/tile/prop üreteci · animasyon kare üretimi · parçacık sistemi · dinamik ışık + yumuşak gölge · post-fx (vignette, kromatik sapma, renk derecelendirme) · bitmap yazı

### Faz 3 — Oynanış Çekirdeği
Tile fiziği (AABB süpürme, tek yönlü platform, eğim) · Player durum makinesi · hitbox/hurtbox savaş sistemi · hitstop · i-frame · geri tepme

### Faz 4 — Dünya
Tilemap + autotile · JSON seviye yükleyici · 5 katmanlı parallax · props (kapı, sandık, meşale, kırılabilir, kaldıraç, checkpoint) · oda geçişleri

### Faz 5 — Düşmanlar ve Bosslar
Düşman AI durum makineleri · yol bulma (kenar algılama + A*) · boss faz sistemi · saldırı desenleri (pattern DSL)

### Faz 6 — Meta Sistemler
Essence · yetenek ağacı · envanter/tılsım · dükkân · diyalog · görev takibi · kayıt slotları

### Faz 7 — İçerik Üretimi
28 bölümün tasarımı, Act Act. Her Act bir sprint.

### Faz 8 — Cila ve Dağıtım
Dinamik müzik katmanları · gamepad titreşimi · başarımlar · seçenekler menüsü (tuş atama, erişilebilirlik) · PyInstaller paketleme · itch.io yayını

---

## 6. Kabul Kriterleri

Bir faz şu koşullar sağlanmadan "bitti" sayılmaz:
1. Oyun hatasız açılıyor ve kapanıyor (kaynak sızıntısı yok)
2. 1920×1080'de sabit 60 FPS
3. ESC her yerde çalışıyor, pencere her zaman kapanıyor
4. Yeni kod eski bir hatayı geri getirmiyor (smoke test yeşil)
5. Her yeni sistem veri odaklı — sabit kodlanmış içerik yok
