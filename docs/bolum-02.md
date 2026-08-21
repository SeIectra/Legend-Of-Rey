# BÖLÜM 2 — "İLK İNİŞ"
**Dikey Dilim · Detaylı Tasarım** · GDD Ek D

**Hedef süre:** 9–11 dakika
**Zorluk:** 2/10
**Amaç:** Oyunun *normal* dokusunu tam kalitede kanıtlamak. Bu bölüm iyiyse oyun iyidir.

---

## ÖĞRETİM HEDEFLERİ

Bölüm sonunda oyuncu şunları söylenmeden öğrenmiş olmalı:

1. Üç vuruşluk zincir ve bitiricinin farklı olduğu
2. Kaçınmanın sadece kaçmak değil, karşı vuruş fırsatı olduğu
3. Kill cancel sayesinde kalabalıkta akışın kesilmediği
4. Yankı'nın gizli şeyleri gösterdiği — ama bedeli olduğu
5. Keşfin ödüllendirildiği (gizli sandık)
6. Düşmanların farklı sorular sorduğu (Sürüklenen ≠ Tırmanan ≠ Şişkin)

---

## ODA ODA AKIŞ

### ODA 1 — İniş (60 sn)
Rey yarıktan aşağı düşer, yuvarlanarak iner. Dar bir dehliz.

- **Düşman yok.** Sadece yürüyüş, atmosfer, ses.
- Duvarda **ilk tırmık izi** — Cemo'nun boyunda. Kamera geçerken hafif yavaşlar (0.5 sn), oyuncu fark etsin.
- Yankı fısıldar (ilk ipucu, kelime yok: ses + ekranda hafif dalga).
- Zemin çakıl → ayak sesi farkı burada tanıtılır.

**Amaç:** Nefes. Oyuncu tondan emin olsun.

---

### ODA 2 — İlk Kan (90 sn)
Geniş, tek katlı oda. Meşale ışığı ortada.

- **3 × Sürüklenen**, sırayla gelir (aynı anda değil).
- İlki tek başına → oyuncu 3'lü zinciri rahatça dener.
- İkinci ve üçüncü birlikte → kill cancel'ı ilk kez hisseder.
- **Ödül:** Sandık (ana yol) — 30 altın.

**Tasarım notu:** İlk düşman **kesinlikle tek başına** olmalı. Oyuncunun ilk combo'sunu kesintisiz tamamlaması, bütün dövüş sistemine dair ilk izlenimi belirler.

---

### ODA 3 — Yukarı Bak (2 dk)
Yüksek tavanlı, üç kademeli platform odası.

- **2 × Tırmanan** tavanda. Oyuncu altından geçerken atlar.
- İlk atlayış **telegraflı**: tavanda sallanma + toz düşmesi + ses. Hasar almadan öğrensin.
- Sonra 1 Sürüklenen + 1 Tırmanan birlikte → yer/hava bölünmüş dikkat.
- Platformlarda zıplama pratiği. Coyote time burada sessizce devreye girer.

**Yeni soru:** "Yukarıya da bakmalıyım."

---

### ODA 4 — YANKI ODASI (90 sn) ★ öğretim zirvesi
Çıkmaz gibi görünen oda. Görünür kapı yok.

- Oyuncu takılır. Birkaç saniye sonra Yankı yükselir — *kendiliğinden*, çünkü ilk sefer.
- Yankı açılınca: sağ duvarda **çatlak parlar**. Kırılabilir duvar.
- Kırınca → **gizli oda** (aşağıda).
- Yankı açıkken ekran kenarı kararır, ses boğuklaşır → bedeli aynı anda hissedilir.

**Tasarım notu:** Bu, oyunun ana mekaniğinin doğduğu an. Oyuncu "yardım aldım ama bir şey kaybettim" hissetmeli. İkisi aynı 3 saniyede olmalı.

---

### ODA 4-A — GİZLİ ODA (45 sn)
Küçük, sessiz, müzik kesilir.

- Önceki maceracının iskeleti, yanında sönmüş meşale.
- **Gizli sandık:** 80 altın + **ilk tılsım** ("Kanlı Bileme": 5+ combo'da hasar %15 artar)
- Duvarda kazınmış işaret — Cemo'nun sembolü değil, başka birinin. (B12'de Ardo'nun işaretleriyle bağlanacak tohum.)

**Amaç:** Keşfin karşılığını *hemen* ver. İlk gizli alan cömert olmalı; oyuncu bir daha hep arar.

---

### ODA 5 — Patlayanlar (2 dk)
Dar koridor, sonra genişleyen alan.

- **Şişkin** tanıtılır: yavaş yaklaşır, şişer, patlar.
- İlk Şişkin **tek başına ve geniş alanda** → patlamayı güvenle gözlemler.
- Sonra: 2 Sürüklenen + 1 Şişkin dar alanda → "nerede öldürdüğüm önemli" dersi.
- Şişkin'i düşmanların ortasında patlatmak = zincirleme hasar. Keşfedilirse ödüllendirici.

**Yeni soru:** "Konumlandırma önemli."

---

### ODA 6 — Kaçınma Dersi (90 sn)
Uzun koridor, tavanda sarkıtlar.

- 4 × Sürüklenen, iki yönden.
- Alan dar → sadece vurarak geçilmez, kaçınma zorunlu.
- Kaçınma sonrası karşı vuruş burada doğal olarak keşfedilir (%30 fazla hasar, farklı ses, daha büyük flaş → oyuncu fark eder).

**Tasarım notu:** Karşı vuruşu hiç açıklama. Sesi ve efekti farklı yap, oyuncu kendi bulsun. Kendi keşfettiği mekaniği asla unutmaz.

---

### ODA 7 — MİNİ-BOSS: "Şişmiş Olan" (2–3 dk)
Kapalı arena. Girişte kapı iner.

**Tasarım:** Büyütülmüş Sürüklenen (1.6×), üç hamlesi var:
1. **Savurma** — geniş yatay, 18 kare tell. Kaçınmayla geçilir.
2. **Çöküş** — havaya zıplar, yere iner, şok dalgası. Zıplayarak geçilir.
3. **Çağrı** — 2 Sürüklenen doğurur (canı %50'nin altına inince).

**Arena:** İki yan platform var. Oyuncu yukarı çıkabilir ama boss oraya vurabilir → güvenli alan yok, sadece geçici nefes.

**Öğrettiği:** Öğrendiği her şeyi birleştirmek. Yeni mekanik yok — sınav.

**Ödül:** 55 altın + **ilk silah seçimi**: Hançer (hızlı, kısa) veya Balta (yavaş, zırh deler). Kılıç zaten elinde.

**Neden burada silah seçimi:** Oyuncu artık dövüşü anladı, tercih yapabilecek bilgiye sahip. Daha erken verirsen anlamsız seçim olur.

---

### ODA 8 — Çıkış (45 sn)
Kısa, dövüşsüz.

- Aşağı inen merdiven.
- Duvarda **ikinci tırmık izi** — bu sefer daha derin, daha çaresiz.
- Yankı son kez fısıldar.
- Kararma → bölüm sonu ekranı: süre, combo rekoru, altın, bulunan gizli alan (1/1 ya da 0/1).

**Bölüm sonu ekranı önemli:** "0/1 gizli alan" gören oyuncu bir daha gizli alan arar.

---

## DÜŞMAN DAĞILIMI

| Oda | Sürüklenen | Tırmanan | Şişkin | Toplam |
|---|---|---|---|---|
| 2 | 3 | — | — | 3 |
| 3 | 1 | 2 | — | 3 |
| 5 | 2 | 1 | 2 | 5 |
| 6 | 4 | — | — | 4 |
| 7 | 2 (çağrılan) | — | — | +boss |
| **Toplam** | **12** | **3** | **2** | **17 + boss** |

Katman 1 hedefi 25–35 idi; B2 erken bölüm olduğu için alt sınırın altında — doğru.

---

## ALTIN AKIŞI

| Kaynak | Miktar |
|---|---|
| 17 düşman × ~5 | 85 |
| Sandık (ana yol) | 30 |
| Gizli sandık | 80 |
| Mini-boss | 55 |
| Combo çarpanı (ortalama) | ~%25 bonus |
| **Toplam (her şeyi bulan)** | **~310** |
| **Toplam (dikkatsiz)** | **~145** |

Fark bilerek iki katından fazla. Keşif ödüllendirilmeli.

---

## SES TASARIMI

| An | Ses |
|---|---|
| Oda 1 | Ambient: su damlası, uzak uğultu. Müzik yok. |
| Oda 2 | İlk düşman görününce müzik dövüş katmanı biner |
| Oda 4 | Yankı açılınca **tüm sesler filtrelenir**, kalp atışı eklenir |
| Oda 4-A | Müzik tamamen kesilir. Sadece meşale çıtırtısı. Sessizlik = keşif ödülü hissi |
| Oda 7 | Boss teması, kapı inerken ağır metal sesi |
| Oda 8 | Müzik söner, ambient kalır |

**Oda 4-A'da müziğin kesilmesi** — küçük detay, devasa etki. Oyuncu gizli alana girdiğini kulağıyla anlar.

---

## BAŞARI KRİTERLERİ (dikey dilim geçti mi?)

Bu bölüm bittiğinde şunlar doğruysa devam:

- [ ] Dövüş 30 dakika oynanınca sıkmıyor
- [ ] Kill cancel akışı hissediliyor
- [ ] Hitstop vuruşları "tokat gibi" yapıyor
- [ ] Oyuncu gizli odayı yardımsız bulabiliyor (test et: 3 kişiden 2'si bulmalı)
- [ ] Yankı'nın bedeli hissediliyor ama sinir bozmuyor
- [ ] Mini-boss ilk denemede zor, ikinci-üçüncüde geçilebilir
- [ ] Bölüm sonunda "bir bölüm daha oynayayım" hissi var

**Son madde en önemlisi.** O yoksa diğerleri anlamsız.

---

## ÜRETİM SIRASI (Bölüm 2 için)

1. Oda geometrisi — placeholder dikdörtgenlerle 8 oda
2. Dövüş sistemi + hitstop + kill cancel (asset'siz, kutularla)
3. 3 düşman AI'sı + saldırı hakkı sistemi
4. Yankı mekaniği + kırılabilir duvar
5. Mini-boss davranış ağacı
6. Sprite'ları geçir (placeholder → gerçek)
7. Efektler + ses
8. Denge ve cila

**Adım 1-5 asset'siz yapılır.** Oynanış kutularla eğlenceliyse, sprite'la harika olur. Tersi asla doğru değil.
