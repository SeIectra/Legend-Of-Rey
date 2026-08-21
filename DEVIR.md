# DEVİR — Legend of Rey

Bu belge, projeyi devralan Claude Code oturumu içindir.
**Önce `CLAUDE.md`'yi oku** (bağlayıcı anayasa), sonra burayı.

Son güncelleme: 21.08.2026 · Ardeko Studios

---

## 1. NEREDE DURUYORUZ

18 bölümlük yandan görünümlü aksiyon-RPG. Tasarım paketi `docs/` altında,
görev sırası `GOREVLER.md`'de.

| Görev | Durum | Not |
|---|---|---|
| 0 — Temel kurulum | ✅ | Palet, font, döngü, boru hattı |
| 1 — Dövüş çekirdeği | ✅ | Zincir, hitstop, kaçınma, kill cancel |
| 2 — Düşman AI | ⬜ | **Sıradaki mantıklı adım** |
| 3 — Yankı sistemi | ⬜ | |
| 4 — Bölüm 2 | ⬜ | Dikey dilim |
| 5 — Ara değerlendirme | ⬜ | **Arda'nın işi**, Claude'a verilmez |
| 6 — Menü ve UI | ✅ | Sıra dışı yapıldı (Arda istedi) |
| 7 — Menü sahnesi cilası | ⬜ | Mor alev, Ardeko intro, dikey yolculuk |
| 8 — Bölüm 3 | ⬜ | |
| 9 — Sanat geçişi | 🟡 | Sprite sistemi hazır; tileset ve düşmanlar eksik |
| 10 — Ses + son cila | ⬜ | Dikiş hazır, gövde boş |

Toplam ~7.500 satır. Dört test paketi de yeşil.

---

## 2. ARDA'NIN VERDİĞİ KARARLAR — pakete ÜSTÜN

Bunlar `CLAUDE.md` ve `GOREVLER.md`'deki kuralları bilinçli olarak geçersiz
kılar. Kendiliğinden geri alma; Arda'ya sormadan değiştirme.

1. **numpy runtime bağımlılığı onaylandı.** `CLAUDE.md` §4'te not düşüldü.
   Üçüncü bir kütüphane hâlâ izne tabi.

2. **Sprite'lar baştan açık.** Paket "Görev 1-4 boyunca kutularla oyna"
   diyordu; Arda "sprite'lar kalsın" dedi. Yerine `F4` üç kip arasında
   geziyor: `sprite → silhouette → box`. Kutu kipi kuralın ruhunu koruyor.

3. **Menü (Görev 6) sıradan önce yapıldı.** Oyunun gösterilebilir bir yüzü
   olsun diye.

4. **Hikâye paketten:** kaçırılan **Cemo**, **Ardo** ikinci oynanabilir
   karakter, para **Altın**, 18 bölüm. Rey'in göğsündeki **geyik dövmesi**
   kişisel simgesi olarak korunuyor (Arda'nın isteği, paketle çelişmiyor).

5. **Rey'in görünümü Arda tarafından belirlendi:** esmer, uzun gür düz koyu
   kahve saç, koyu kahve badem gözler, rahat feminen giyim, sağ köprücük
   kemiği altında geyik dövmesi.

6. **`src/scenes/` eklendi** — `CLAUDE.md` §5'teki yapıda yok, mimari serbest
   olduğu için eklendi.

7. **Aseprite:** kurulmadı, şimdilik gerek yok. Hazırlığı yapıldı
   (`tools/aseprite.py` tespit + geri düşüş, `tools/palette_to_gpl.py`,
   `.gitattributes`). Arda lisansı onayladı; elle rötuş gerektiğinde kurulur.

---

## 3. ÇALIŞTIRMA VE DOĞRULAMA

```bash
.venv\Scripts\python.exe main.py          # ana menü
.venv\Scripts\python.exe main.py dovus    # doğrudan dövüş odası
.venv\Scripts\python.exe main.py temel    # Faz 0 doğrulama ekranı
```

Python 3.13.15, pygame-ce 2.5.8, numpy. Sanal ortam `.venv/`.

### Testler — değişiklikten sonra hepsini çalıştır

```bash
python tests/test_foundation.py   # palet 32 renk, Türkçe font, tr_upper
python tests/test_pipeline.py     # quantize → outline → shade → preview
python tests/test_combat.py       # dövüş kare değerleri (BAĞLAYICI)
python tests/test_menu.py         # menü UX + kayıt güvenliği
python tests/test_lang.py         # dil tabloları + kod/tablo örtüşmesi
python -m pyflakes src tools tests main.py
```

`test_combat.py` `docs/dovus-sistemi.md`'deki her sayının kodda tuttuğunu
kanıtlar. Bir değer sessizce değişirse orası kırılır — **bu kasıtlı.**

### Görsel doğrulama

```bash
python tools/shot.py --scene src.ui.menu:MainMenuScene --out build/x.png
python tools/sprite_sheet.py --karakter rey --durum idle,run,attack1
python tools/sprite_sheet.py --siluet          # siluet testi
python tools/measure_jump.py                   # zıplama zarfı
```

Ekran görüntüleri `build/testshots/` altına düşer. **"Çalışıyor" deme,
görüntüyü aç ve bak** — `CLAUDE.md` §13 bunu şart koşuyor.

---

## 4. PAHALIYA ÖĞRENİLENLER

Bunların hepsi gerçek hataydı, testle yakalandı. Tekrarlama.

1. **`convert()` / `convert_alpha()` `display.set_mode()`'dan önce çağrılamaz.**
   `Game.__init__` içinde pencere önce açılır, canvas sonra oluşur.

2. **Kill cancel AKTİF karelerde tetiklenmeli.** Düşman hitbox açıkken ölür;
   yalnızca `RECOVERY`'ye bakmak mekanizmayı pratikte hiç çalıştırmaz.
   `ChainState.skip_recovery` bunun için var.

3. **Sprite ayak hizalaması.** Hücrenin altı ≠ karakterin ayağı.
   `sprite_foot_y` (= `CharSpec.foot_y`) kullanılmazsa karakter havada durur.
   Squash yüksekliği değiştirdiği için taban çizgisi de ölçeklenir.

4. **Gölge zincirleri monoton parlaklaşmalı.** Ters dönen bir zincir
   ışıklandırmayı tersine çevirir; `hair_dark` bir kez bu hataya düştü.

5. **Siluet testi işe yarıyor.** Rey ve Ardo ayırt edilemiyordu; Ardo'ya sivri
   kukulete ve geniş omuz verildi. Yeni karakterde mutlaka çalıştır.

6. **Zıplama zarfı ölçülür, tahmin edilmez.** `PLAYER_JUMP_SPEED` ya da
   `PLAYER_RUN_SPEED` değişirse **önce** `tools/measure_jump.py`, sonra
   `config.py`, sonra bölüm doğrulaması. Prototipte bu atlandığı için bir
   bölümün çıkış kapısına ulaşılamıyordu.

7. **Boşluk genişliği ≠ atlanacak mesafe.** N tile genişliğindeki boşluk,
   kenardaki basılabilir tile'lar arasında N+1 tile yol demek.

8. **Kayıt sırası önemli:** önce yeni kaydı diske yaz, **sonra** eskisini
   yedekle. Tersi, yazma çökerse iki bozuk dosya bırakır.

9. **Panel yükseklikleri içerikle hesaplanmalı.** İki menü panelinde son satır
   çerçeveyi kesiyordu.

10. **`BLEND_RGB_ADD` alfayı yok sayar.** Şiddeti `set_alpha` ile değil,
    renkleri `BLEND_RGB_MULT` ile kısarak ayarla.

11. **Arayüz metni asla koda gömülmez.** `src/ui/lang/*.json` içine dil
    anahtarı olarak yazılır, çizim anında `t()` ile çözülür. Modül
    seviyesinde sabit metin dil değişimini etkisiz bırakır.

12. **Dile bağlı olduğu fark edilmeyen şeyler:** yüzde işaretinin yeri
    (TR `%100`, EN `100%`), süre birimi (`dk`/`m`), ve büyük harf kuralı —
    `tr_upper("Continue")` noktalı İ ile `CONTİNUE` verir.

---

## 5. MİMARİ — HIZLI HARİTA

```
src/
├── config.py          TÜM sayısal değerler, KARE cinsinden. Sihirli sayı yok.
├── core/
│   ├── game.py        Sabit 60 kare döngü, 480×270, tam sayı ölçekleme, hitstop
│   ├── scene.py       Sahne yığını (tek döngü kuralı — ikinci while ASLA)
│   ├── input.py       Aksiyon eşlemesi + 8 karelik tampon
│   ├── camera.py      Takip, ölü bölge, ileri bakış
│   └── juice.py       ★ on_hit() — hitstop+sarsıntı+parçacık TEK çağrıdan
├── art/
│   ├── palette.py     32 renk, tools/palette.json'dan okur. Palet dışı YASAK.
│   ├── forge.py       İndeks tabanlı çizim (renk değil, zincir+basamak)
│   ├── spritegen.py   draw_humanoid — tek iskelet, çok karakter
│   ├── animation.py   Poz üreticileri + karakter kütüphanesi
│   ├── animator.py    Oynatıcı + sprite önbelleği
│   └── particles.py   Sütun tabanlı, üst sınır 200
├── combat/
│   ├── combo.py       3'lü zincir, kaçınma, combo sayacı
│   └── hitbox.py      Kare bazlı hitbox — kimse doğrudan hasar vermez
├── entities/          actor · player · player_render · character_stats · dummy
├── systems/           save (yedekli) · settings
├── ui/                text (tr_upper!) · widgets · menu · character_select
│                      settings_scene · pause · hud · font_data
│   ├── i18n.py        t() — TR/EN, çizim anında çözülür
│   └── lang/          tr.json (kanonik) · en.json
├── world/tilemap.py   16×16 tile, ASCII'den kurulur
└── scenes/            combat_room · foundation_check
```

### Değiştirmeden önce bilinmesi gerekenler

- **Zaman birimi karedir.** `dt` yok. Hız piksel/kare, ivme piksel/kare².
- **Renkle değil, gölge zinciriyle çizilir.** `forge.Canvas` her piksel için
  (zincir, basamak) tutar; `shade()` ve `outline()` bunun üstünde çalışır.
- **Hasar tek yerden geçer.** `hitboxes.spawn(Hitbox(...))` → `HitboxManager`
  çözer → `scene.on_hit()` game feel'i verir. `take_damage` doğrudan çağrılmaz.
- **`smoothscale` yasak** (ışık/bulanıklık katmanı hariç).
- **400 satırı geçen dosya bölünür.** İki kez bölmek gerekti, gerekirse yine böl.
- **Türkçe:** yorumlar Türkçe, tanımlayıcılar İngilizce. Büyük harf için
  **her yerde** `text.tr_upper()` — `str.upper()` Türkçe'de yanlış.

---

## 6. AÇIK KALANLAR

Sıra gelmediği için değil, gözden kaçmasın diye burada:

1. **Ses sistemi yok.** `game.play_ui_sound()` çağrılıyor, gövdesi boş.
   `juice.pitch_variation()` hazır. Görev 10.
2. **Renk körü modu, parlaklık, arayüz ölçeği** ayarlarda görünüyor ama
   uygulanmıyor. Palet tek kaynak olduğu için renk körü ucuz.
   (Dil ayarı artık **çalışıyor** — TR/EN, anında geçiş.)
3. **Ardo'nun oynanışı Rey'in aynısı** — sayılar farklı, İz Sürme mekaniği
   (`docs/derinlestirme.md` 2.4) yok.
4. **Tileset placeholder.** `world/tilemap.py` düz renk çiziyor; 9-slice ve
   varyantlar Görev 9.
5. **EKSTRALAR ve EKİPMAN menüde kapalı** — içerikleri sonraki görevlerde.
6. **`docs/asset-plani.md` güncel değil:** "Türkçe karakter eksik" ve
   "prototipteki sprite kalitesi" maddeleri artık geçersiz.
7. **`_prototype/` içinde işe yarar kod var** — parallax, ışıklandırma,
   post-fx, tile üreteci. Referans olarak bak, **asla import etme.**

---

## 7. GİT DURUMU

Çalışma **`v3-yeniden-yapilandirma`** dalında, 7 commit halinde kayıtlı.
`main` hâlâ v2.1'de (eski motor) — geri dönmek gerekirse orada duruyor.

```
Prototipi _prototype/ altina arsivle
Tasarim paketini koke yerlestir - CLAUDE.md artik anayasa
Gorev 0: temel katman - sabit adim dongu, palet, Turkce font
Gorev 0/9: sanat boru hatti - prosedurel sprite uretimi
Gorev 1: dovus cekirdegi - zincir, kacinma, kill cancel
Gorev 6: menu, ayarlar, kayit - islevsel katman
Testler, devir belgesi ve marka gorselleri
Rey'in sacini koyulastir + golge zinciri testi
Coklu dil destegi - Turkce ve Ingilizce
```

Hiçbir şey push edilmedi. Arda birleştirmek isterse:
`git checkout main && git merge v3-yeniden-yapilandirma`

Commit mesajları **niçin** öyle yapıldığını anlatıyor — bir davranışı
değiştirmeden önce ilgili commit'e bakmakta fayda var.

---

## 8. SIRADAKİ ADIM

Paket sırasına göre **Görev 2 — Düşman AI**:
3 tip (Sürüklenen, Tırmanan, Şişkin) + saldırı hakkı sistemi (aynı anda en
fazla 2 saldıran) + poise/sendeleme + ritim imzaları + renk kodlu tehlike.

`GOREVLER.md`'deki Görev 2 promptunu oku, `docs/gdd.md` §7 ve
`docs/dovus-sistemi.md` §6 bağlayıcı.

Altyapı hazır: `Actor` poise ve stagger tutuyor, `Hitbox` takım maskesi var,
`TrainingDummy` örnek olarak duruyor, `config.py`'de tell süreleri tanımlı.

**Ama önce Arda'ya sor** — sırayı bir kez değiştirdi, yine değiştirebilir.

---

## 9. ÇALIŞMA DÜZENİ (CLAUDE.md §13 özeti)

1. Görevi oku, `docs/` içinden ilgili belgeyi aç
2. Büyük görevde **önce plan sun**, onay al
3. Kodu yaz
4. **Çalıştır ve kanıt göster** — test çıktısı, komut, ekran görüntüsü
5. Ne yaptığını özetle, açık kalanları söyle
6. **Önerilerini listele**
7. **Dur.** Sıradaki göreve kendiliğinden geçme.

Sandbox'ta çalışmayan bir adım varsa görevi "tamamlandı" ilan etme.
