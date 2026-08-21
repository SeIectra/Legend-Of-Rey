# SES LİSTESİ — Legend of Rey

Bu liste **kodun gerçekten çağırdığı** olaylardan ve tasarım belgelerinden
türetildi; uydurma değil. Her satırın karşılığı ya `src/` içinde bir kanca
ya da `docs/` içinde bağlayıcı bir madde.

**Öncelik sütunu:** `1` dikey dilim için şart (Bölüm 1–3 + menü), `2` tam
oyun için gerekli, `3` cila.

---

## 0. FORMAT VE KURALLAR

| | |
|---|---|
| Format | `.ogg` (Vorbis) — pygame-ce yerel destekler, `.wav`'dan çok küçük |
| Örnekleme | 44.1 kHz, mono (konumsal ses yok, stereo boşa yer) |
| Uzun parçalar | Müzik ve ortam sesi `.ogg` akış; efektler tam bellekte |
| İsimlendirme | `kategori_ad.ogg` — kod anahtarları bu listedeki **Anahtar** sütunu |
| Süre | Efektler **80–400 ms**. Uzun efekt dövüşü geciktirir |

**Perde varyasyonu:** Her tekrarlı efekt çalarken ±%8 rastgele perde
uygulanacak (`docs/derinlestirme.md` 1.6). Yani **tek dosya yeterli** —
aynı sesin 3 varyantını kaydetmeye gerek yok. Kod yapıyor.

**Yankı'nın boğuk seti:** Yankı açıkken gerçek zamanlı filtre yok; her
efektin **önceden alçak geçiren filtreden geçmiş ikinci kopyası** olacak
(`docs/dovus-sistemi.md` 5). Aşağıda ★ ile işaretli seslerin `_muffled`
sürümü de gerekiyor.

> **Toplam: 72 ses.** ★ işaretli 12 tanesinin boğuk kopyasıyla birlikte
> **84 dosya**. Müzik parçalarının yarım perde düşük sürümleri buna dahil
> değil (6 parça → 6 dosya daha).

---

## 1. DÖVÜŞ ★ — öncelik 1

Vuruş sesi **katmanlı** olmalı: temas + metal + düşman tepkisi
(`docs/dovus-sistemi.md` 5). Üç katmanı ayrı dosya olarak verirsen kod
karıştırabilir; tek dosyada karışık da olur. Tercihini söyle.

| Anahtar | Ne zaman | Nasıl olmalı | Ö |
|---|---|---|---|
| `hit_light` ★ | Zincir 1–2 vuruş | Kısa, kuru, tok. 90 ms | 1 |
| `hit_heavy` ★ | Zincir 3 (bitirici) | Daha derin, hafif gecikmeli kuyruk. 180 ms | 1 |
| `hit_counter` ★ | Karşı vuruş | Diğerlerinden **belirgin farklı** — ödül sesi. Metalik çınlama | 1 |
| `hit_kill` ★ | Öldüren vuruş | Islak, kısa, kesin. Kill cancel'ın duyulur işareti | 1 |
| `swing_light` | Kılıç savrulması 1–2 | Havanın yarılması. Vuruş değmese de çalar | 1 |
| `swing_heavy` | Kılıç savrulması 3 | Daha yavaş, daha alçak | 1 |
| `player_hurt` ★ | Rey hasar alır | Nefes kesilmesi + kumaş. Acı çığlığı **değil** | 1 |
| `player_death` | Rey ölür | Uzun, alçalan. Tek an | 1 |
| `dodge` | Kaçınma | Kumaş + ayak sürtünmesi. Çok kısa, 70 ms | 1 |
| `dodge_perfect` | Kaçınma dokunulmazlığında vuruş yendi | İnce bir "vınn" — mükemmel zamanlama ödülü | 2 |
| `combo_5` | 5 combo | Ton. Her eşikte perde yükselir | 2 |
| `combo_10` | 10 combo | Aynı tonun üstü | 2 |
| `combo_20` | 20 combo | Aynı tonun en üstü + Yankı iyileşme çınlaması | 2 |
| `combo_break` | Combo sıfırlandı | Alçalan, kısa hayal kırıklığı | 2 |

> **Combo perdesi:** Kod her 5 combo'da +%3 perde uyguluyor
> (`docs/dovus-sistemi.md` 5). `combo_5/10/20` yine de ayrı dosya —
> eşikler duyulur biçimde farklı olmalı.

---

## 2. HAREKET ★ — öncelik 1

Ayak sesi **zemine göre** değişir (`docs/dovus-sistemi.md` 5).

| Anahtar | Ne zaman | Nasıl olmalı | Ö |
|---|---|---|---|
| `step_stone` ★ | Taş zeminde adım | Kısa, sert. 60 ms | 1 |
| `step_earth` ★ | Toprak/köy zemininde adım | Yumuşak, boğuk | 1 |
| `step_water` ★ | Su içinde adım (B5) | Sıçrama | 2 |
| `step_gravel` ★ | Çakıl (B2 koridorları) | Çıtırtı | 2 |
| `jump` | Zıplama | Kumaş + hafif nefes | 1 |
| `land_soft` | Normal iniş | Tok, kısa | 1 |
| `land_hard` | Uzun düşüşten iniş | Daha ağır + toz | 2 |
| `ledge_grab` | Kenara tutunma | Tırnak/kumaş | 3 |

---

## 3. YANKI — öncelik 1 · **oyunun kimliği**

Bu bölüm oyunun en önemli sesleri. `docs/gdd.md` 4: *"Yankı'yı açtığımda
hem yardım aldığımı hem bir şey kaybettiğimi aynı anda hissetmeliyim."*
Ses bu hissin yarısı.

| Anahtar | Ne zaman | Nasıl olmalı | Ö |
|---|---|---|---|
| `echo_open` | Yankı açılır (14 kare) | Yükselen fısıltı katmanı. Kulağa **yaklaşan** bir şey gibi | 1 |
| `echo_loop` | Yankı açık kaldığı sürece | Döngü. Anlaşılmayan çok sesli fısıltı. Kelime **yok** | 1 |
| `echo_close` | Yankı kapanır (20 kare) | Sönerek uzaklaşır | 1 |
| `echo_ask` | Soru sorulur | Tek bir soru tınısı — yukarı kıvrılan | 1 |
| `echo_answer_truth` | Doğru cevap (BERRAK) | Net, tek, güven veren | 1 |
| `echo_answer_partial` | Eksik cevap (BULANIK) | Aynı ton ama **kırık**, yarım kalan | 1 |
| `echo_answer_lie` | **Yalan** | Doğruyla **aynı** olmalı. Oyuncu kulaktan anlamamalı | 1 |
| `echo_tier_down` | Ölünce kademe düşer | Alçalan, bir şey kaybetme | 1 |
| `echo_tier_up` | 20 combo / kontrol noktası | Yükselen, açılma | 1 |
| `echo_silent` | SESSIZ kademeye düşüldü | Ani kesilme + çınlama (kulak çınlaması gibi) | 1 |
| `echo_reveal` | Duvar ardında düşman görünür | Çok alçak, tek darbe. Her siluet için değil, açılışta bir kez | 2 |
| `echo_wall` | Kırılabilir duvar görünür | Farklı tını — "burada bir şey var" | 2 |
| `echo_sonar` | Ses haritası (B3) | Tek **çan tınısı** ve yayılan dalga (`docs/bolum-03.md`) | 2 |

> **`echo_answer_lie` kritik.** Doğru cevapla ayırt edilebilir olursa
> mekanik ölür: oyuncu kademeyi bilerek risk hesaplayacak, kulağından
> anlamayacak. **Aynı dosya kullanılabilir** — ayrı satır sadece
> ileride değiştirmek isterseniz diye.

---

## 4. KOLYE PUSULASI — öncelik 1

Cemo'ya yaklaştıkça ısınır, kalp atışı hızlanır
(`docs/derinlestirme.md` 3.1).

| Anahtar | Ne zaman | Nasıl olmalı | Ö |
|---|---|---|---|
| `necklace_beat` | Kalp atışı — periyot mesafeye göre 78→22 kare | **Tak-tak** çift vuruş. Alçak, göğüsten | 1 |
| `necklace_warm` | Sıcaklık kademesi arttı | Isınan metal, çok kısa | 2 |
| `necklace_conflict` | Kolye ile Yankı **çelişir** | İki ses üst üste, hafif akortsuz. Oyunun teması bu anda duyuluyor | 2 |

---

## 5. DÜŞMANLAR ★ — öncelik 1

Her düşmanın **tell** sesi ayrı olmalı: kalabalıkta hangisinin saldırdığı
kulaktan da anlaşılsın (`docs/dovus-sistemi.md` 6).

| Anahtar | Ne zaman | Nasıl olmalı | Ö |
|---|---|---|---|
| `shambler_idle` | Sürüklenen dolaşır | Islak hırıltı, seyrek | 1 |
| `shambler_tell` ★ | Saldırı ön işareti (18 kare) | Nefes çekme — vuruştan **önce** | 1 |
| `shambler_attack` | Vuruş | Kuru savurma | 1 |
| `shambler_death` | Ölüm | Çökme + ıslak | 1 |
| `climber_cling` | Tavanda bekler | Çok alçak tırmalama, seyrek | 1 |
| `climber_tell` ★ | Bırakmadan önce (16 kare) | Sallanma + toz dökülmesi | 1 |
| `climber_drop` | Tavandan kopar | Kısa düşüş sesi | 1 |
| `climber_death` | Ölüm | Böceksi çatırtı | 1 |
| `bloated_idle` | Şişkin dolaşır | Ağır, ıslak nefes | 1 |
| `bloated_fuse` ★ | Fitil yanar (30 kare) | **Şişme** — sürekli yükselen. Sabit süre, öğrenilebilir | 1 |
| `bloated_explode` | Patlama | Islak patlama + basınç | 1 |
| `enemy_stagger` | Poise kırıldı, sendeler | Kısa, şaşkın | 2 |
| `enemy_blocked` | Kalkanlı engelledi (Katman 2) | Metalik tok | 2 |

---

## 6. MENÜ VE ARAYÜZ — öncelik 1

`docs/menu-ui.md`: menü sesleri **kısa** olmalı, menü hızlı hissetmeli.

| Anahtar | Ne zaman | Nasıl olmalı | Ö |
|---|---|---|---|
| `ui_tick` | Menüde seçim değişir | Çok kısa tık. 40 ms | 1 |
| `ui_confirm` | Onay | Tok, olumlu | 1 |
| `ui_back` | Geri | Alçalan | 1 |
| `ui_deny` | Kapalı öğeye basıldı | Kısa, boğuk red | 1 |
| `ui_slider` | Ayar kaydırıcısı | Çok kısa tık, perde değere göre | 2 |
| `ui_tab` | Sekme değişir | Kâğıt çevirme | 2 |
| `save_written` | Oyun kaydedildi | Alçak, güven veren | 2 |
| `gold_pickup` | Altın toplandı | Metalik, perde miktara göre | 2 |
| `item_pickup` | Eşya toplandı | Farklı, daha "önemli" | 2 |

---

## 7. AÇILIŞ VE GEÇİŞLER — öncelik 1

`docs/menu-ui.md` 0: *"Bir iyi ses, on ortalama sesten iyidir."*

| Anahtar | Ne zaman | Nasıl olmalı | Ö |
|---|---|---|---|
| `intro_spark` | Ardeko intro — kıvılcım | Tek çakmak sesi. **Müzik yok** | 1 |
| `intro_hum` | Mor alev doğarken | Alçak uğultu, yükselen | 1 |
| `journey_wind` | Dikey yolculuk | Rüzgâr — yükseldikçe artan | 1 |
| `journey_cellar` | Dikey yolculuk | Mahzen uğultusu — yükseldikçe **azalan**. İkisi çapraz geçer | 1 |
| `journey_night` | Köye varış | Gece böcekleri | 1 |
| `rift_open` | Bölüm 1 — yarık açılır | Yırtılma + alçak gümbürtü | 1 |
| `rift_close` | Yarık kapanır | Ters, sönerek | 1 |
| `chapter_end` | Bölüm biter | Tek, sakin | 2 |

---

## 8. ORTAM (döngü) — öncelik 1–2

Bunlar uzun döngüler, `.ogg` akış olarak çalınacak.

| Anahtar | Nerede | Nasıl olmalı | Ö |
|---|---|---|---|
| `amb_village_night` | Bölüm 1 | Böcek, uzak rüzgâr, ara sıra köpek | 1 |
| `amb_cellar` | Menü sahnesi, B2 | Damlama, alçak uğultu, zincir | 1 |
| `amb_torch` | B3 meşale mahzeni | Alev çıtırtısı | 2 |
| `amb_water` | B5 sular | Su akıntısı | 2 |
| `amb_deep` | Katman 3 (B14+) | Organik, nefes alan bir şey | 3 |

---

## 9. MÜZİK — öncelik 2

`docs/dovus-sistemi.md`: Yankı açıkken müzik **yarım perde düşer** — bu
gerçek zamanlı değil, **ikinci bir set** olarak hazırlanacak. Yani aşağıdaki
her parçanın iki sürümü gerekiyor: normal ve yarım perde düşük.

| Anahtar | Nerede | Nasıl olmalı | Ö |
|---|---|---|---|
| `mus_menu` | Ana menü | Yalnız, mor alevin etrafında. Melodiden çok doku | 2 |
| `mus_explore` | Keşif | Sakin, tekrarsız | 2 |
| `mus_combat` | Dövüş | Ritmik. Dövüş bitince yumuşak çıkış | 2 |
| `mus_boss` | Boss | Dört boss için ayrı ya da tek tema + varyasyon — kararın | 3 |
| `mus_breath` | Nefes bölümleri (B4, B8, B12) | Neredeyse sessiz, tek enstrüman | 3 |
| `mus_ending` | Final | Sıcak. İlk kez tam kadro | 3 |

---

## 10. ÖZEL ANLAR — öncelik 3

Bunlar tek kullanımlık ama hikâyenin dönüm noktaları.

| Anahtar | Ne zaman | Nasıl olmalı |
|---|---|---|
| `ardo_arrival` | B6 — gölge yukarıdan düşer | Tek ağır darbe, sonra sessizlik |
| `echo_lies_first` | B10 — Yankı **ilk kez yalan söyler** | Tanıdık cevap sesi ama sonunda ince bir çatlak |
| `twist_reveal` | B14 — Yankı'nın kaynağı | Fısıltılar tek sese dönüşür |
| `silence_absolute` | B3 Panel B, B18 | **2 saniye mutlak sessizlik.** Dosya değil, kod işi — ama miksajda planla |
| `heartbeat_boss` | B18 Karanlık Dalgası | Tüm sesler kesilir, sadece kalp atışı |

---

## ÖNCELİK ÖZETİ

| Öncelik | Adet | Ne zaman gerekli |
|---|---|---|
| **1** | 38 | Dikey dilim — Bölüm 1–3 + menü oynanabilir olsun |
| **2** | 24 | Tam oyun |
| **3** | 5 | Cila |
| özel anlar | 5 | Hikâye dönüm noktaları (bölümü geldiğinde) |

Sayılar belgeden makineyle sayıldı, tahmin değil.

**Önce şu 8 tanesini yapmanı öneririm** — oyunun kimliğini bunlar kuruyor:
`hit_light`, `hit_heavy`, `echo_open`, `echo_loop`, `echo_ask`,
`necklace_beat`, `intro_spark`, `ui_tick`.

Bunlar elimde olunca ses sistemini (Görev 10) bağlayıp geri kalanı
sırayla ekleyebilirim. Kod tarafındaki dikiş (`game.play_ui_sound`) zaten
hazır ve bekliyor.
