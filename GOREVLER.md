# LORE — Claude Code Görev Promptları

Sırayla ver. Her görevi bitir, çalıştır, gör, sonra sonrakine geç.
**Bir görevi atlamak veya birleştirmek işe yaramaz** — her biri bir öncekinin üstüne inşa ediliyor.

---

## HAZIRLIK (senin işin, Claude Code'a verilmez)

1. Yeni klasör aç: `lore/`
2. `CLAUDE.md` dosyasını köke koy
3. `docs/` klasörü ve içindeki 11 belge zaten pakette hazır — olduğu gibi kopyala
4. Ardeko Studios logosunu `assets/logo/` altına koy
5. `git init` ve ilk commit
6. Eski prototipi ayrı bir klasörde sakla (`_prototype/`) — referans olarak kalsın, üstüne yazma

---

## GÖREV 0 — Temel Kurulum

```
CLAUDE.md'yi ve docs/ altındaki tüm tasarım belgelerini oku.

Görev: Faz 0 — proje temelini kur. Oynanış kodu YAZMA.

Yapılacaklar:
1. CLAUDE.md bölüm 5'teki klasör yapısını oluştur (boş __init__.py'lerle)
2. src/config.py — docs/dovus-sistemi.md'deki TÜM sayısal değerleri
   adlandırılmış sabit olarak buraya taşı. Kare cinsinden.
3. src/art/palette.py — 32 renkli palet. Zindan teması: koyu maviler,
   taş grileri, meşale turuncuları, kan kırmızısı, Yankı için soluk cyan,
   mor alev için echo_violet, düşman tell'i için tehlike turuncu-kırmızısı.
   Her renge isim ver (PALETTE["stone_dark"] gibi).
   KAYNAK: tools/palette.json — palette.py bunu okur, kendi tanımlamaz.
3b. ASSET BORU HATTI (docs/asset-boru-hatti.md) — tools/ klasörü:
   - tools/palette.json — 32 renk, TEK GERÇEK KAYNAK
   - tools/quantize.py — herhangi bir görseli palete indirger.
     Dithering KAPALI. Alfa eşiğe göre 0/255'e yuvarlanır.
   - tools/outline.py — otomatik kontur (paletin en koyu 2. rengi, siyah değil)
   - tools/shade.py — sol-üst ışık kuralını otomatik uygular
   - tools/preview.py — tüm asset'leri tek kontak sayfasında yan yana dizer
     (tutarsızlığı ancak yan yana görünce fark edersin — bu en kullanışlı araç)
   - tools/silhouette.py — hepsini siyaha çevirip dizer, siluet testi otomasyonu
   Blender veya 3D araç KULLANMA. Pillow + NumPy yeterli ve doğru araç.
4. src/core/game.py — sabit 60 FPS adımlı ana döngü, 480x270 iç yüzey,
   tam sayı ölçekleme ile ekrana çizim. smoothscale KULLANMA.
5. src/core/scene.py — basit sahne yöneticisi (push/pop/replace)
6. src/core/input.py — girdi haritası (klavye + gamepad) ve 8 karelik
   girdi tamponu
7. requirements.txt (sadece pygame-ce)
8. Türkçe karakterli piksel font: assets/fonts/ altına koy. Ücretsiz bir
   piksel font bul veya mevcut bir fontu genişlet. ğ Ğ ü Ü ş Ş ı I i İ ö Ö
   ç Ç KESİNLİKLE çalışmalı. Bir test ekranında hepsini bastır.
9. src/ui/text.py — tr_upper() ve tr_lower() fonksiyonları.
   Python'un str.upper()'ı Türkçe için YANLIŞ: 'i' → 'I' yapıyor,
   Türkçe'de 'İ' olmalı. 'I' → 'i' yapıyor, 'ı' olmalı.
   Menüde büyük harf kullanılacaksa her yerde bu fonksiyonlar kullanılsın.
   Test et: "ışık" → "IŞIK", "İstanbul" → "İSTANBUL", "IŞIK" → "ışık"

Bitince: main.py çalıştırıldığında boş bir pencere açılsın, ortada
Türkçe karakterli bir test metni görünsün, FPS sayacı olsun.
```

---

## GÖREV 1 — Dövüş Çekirdeği (placeholder ile)

```
Görev: Faz 1 — dövüş sistemi. SPRITE YOK, renkli dikdörtgenler kullan.

docs/dovus-sistemi.md bölüm 1-5 bağlayıcıdır.

Yapılacaklar:
1. src/entities/actor.py — temel varlık (konum, hız, çarpışma kutusu,
   durum makinesi)
2. src/entities/player.py — hareket, zıplama, coyote time (6 kare)
3. src/combat/combo.py — 3'lü zincir:
   - Vuruş 1: 4 ön / 3 aktif / 8 son
   - Vuruş 2: 5 / 3 / 9
   - Vuruş 3 (bitirici): 8 / 5 / 16
   - Zincir penceresi 12 kare
   - Vuruş 1-2 recovery'si kaçınma ile iptal edilebilir
   - Vuruş 3 iptal edilemez
4. src/combat/hitbox.py — kare bazlı aktif hitbox
5. Kaçınma: 6 kare dokunulmazlık, 18 kare toplam, 24 kare bekleme.
   Kaçınmadan sonra 9 kare içinde saldırı = karşı vuruş (%30 hasar bonusu,
   farklı renk flaşı)
6. src/core/juice.py:
   - Hitstop: normal 3, bitirici 7, öldürücü 12 kare.
     Fizik ve animasyon durur, çizim devam eder.
   - Ekran sarsıntısı: üstel bozunum (amp *= 0.85), ayarlardan kapatılabilir
   - Vuruş flaşı: hedef 2 kare beyaz
   - YÖNLÜ sarsıntı: darbe vektörü yönünde, rastgele değil
   - Orta/büyük sarsıntıya 0.3-0.8 derece ROTASYON ekle
     (saf öteleme hata gibi okunur, rotasyon kuvvet gibi okunur)
   - Üçlü senkron: hitstop + sarsıntı + parçacık TEK bir on_hit()
     fonksiyonundan tetiklenir
   - Squash & stretch: transform.scale ile deformasyon.
     Zıplama 0.85/1.15, iniş 1.2/0.8, vuruş anında hedef 1.3/0.7
   - Ses perde varyasyonu: her tekrarlı efekt ±%8 rastgele perde
   Detaylar: docs/derinlestirme.md bölüm 1
7. Test odası: düz zemin, birkaç platform, 3 hareketsiz "kukla" düşman
   (sadece can barı olan dikdörtgen)

Bitince: kuklalara vurup 3'lü zinciri, bitiriciyi, kaçınmayı ve karşı
vuruşu hissedebilmeliyim. Hitstop'un çalıştığı belli olmalı.

ÖNEMLİ: Bu adımda sprite yapma. Kutularla eğlenceli değilse sprite
eklemek kurtarmaz.
```

---

## GÖREV 2 — Düşman AI

```
Görev: Faz 2 — 3 düşman tipi + saldırı hakkı sistemi. Hâlâ placeholder.

docs/gdd.md bölüm 7 (Katman 1) ve docs/dovus-sistemi.md bölüm 6.

Yapılacaklar:
1. src/entities/enemy.py — temel düşman sınıfı. 10 tipe genişleyebilecek
   sağlam bir altyapı kur (davranış bileşenleri, tell sistemi, poise).
   Ama şimdilik sadece 3 tipi hayata geçir — kalan 7'yi sırası gelince
   ekleyeceğiz.
2. Üç tip:
   - Sürüklenen: yavaş yürür, tek saldırı, 18 kare tell
   - Tırmanan: tavanda/duvarda bekler, oyuncu altından geçince atlar.
     Atlamadan önce sallanma + toz + ses (telegraf)
   - Şişkin: yaklaşır, şişer, patlar. Patlama diğer düşmanlara da hasar verir
3. Saldırı hakkı sistemi (src/combat/ içinde bir yönetici):
   - Aynı anda EN FAZLA 2 düşman saldırabilir
   - Diğerleri kuşatma pozisyonunda dolanır, sırasını bekler
   - Bu, kalabalık dövüşün okunabilirliğinin temeli
4. Poise/sersemleme: her düşmanın poise değeri var, yeterli vuruşta
   sendeler ve saldırısı iptal olur
5. Kill cancel: düşman öldüğü anda oyuncunun tüm recovery'si iptal olur
6. Combo sayacı: 90 kare sessizlikte sıfırlanır. Eşikler 5/10/20
7. RİTİM İMZASI: her düşman tipinin sabit, öğrenilebilir bir saldırı
   ritmi olsun. Rastgele saldıran düşman öğrenilemez, sadece sinir bozar.
   - Sürüklenen: yavaş 3'lük (bekle-bekle-vur)
   - Tırmanan: ani tek vuruş, uzun bekleme
   - Şişkin: yaklaş-şiş-patla, sabit süre
8. RENK KODLU TEHLİKE: palete "tehlike" rengi ekle. Her düşman tell'inde
   bu renkle parlasın. Renk körlüğü için parlama VE siluet değişimi birlikte.
9. DÜŞMAN CAN BARI YOK. Durum görsel okunur: sendeleme, renk koyulaşması,
   hız düşüşü. Bar sadece boss'ta.
10. Kalıcılık: ölen düşmanların kan lekesi/molozu zeminde bölüm boyunca kalır
11. Düşman ekolojisi: Şişkin patlaması yakındaki diğer düşmanlara da hasar
    verir. Oyuncu bunu silah olarak keşfedebilmeli.

Bitince: 6-8 düşmanlı bir odada dövüş kaotik değil, okunabilir ve akıcı
hissetmeli. Kill cancel sayesinde kalabalıkta akış kesilmemeli.
```

---

## GÖREV 3 — Yankı Sistemi

```
Görev: Faz 3 — Yankı (oyunun ana mekaniği).

docs/gdd.md bölüm 4 bağlayıcıdır.

Yapılacaklar:
1. src/systems/echo.py — 3 kademe: BERRAK, BULANIK, SESSIZ
   - Ölünce bir kademe düşer
   - SESSIZ dibi, daha aşağı inmez
   - 20 combo'da bir kademe iyileşir
   - Kontrol noktasında iyileşir
2. Aktif kullanım (tuşa basılı tutma):
   - BERRAK: duvar ardındaki düşman siluetleri, gizli geçitler parlar
   - BULANIK: sadece yakın mesafe, silik
   - SESSIZ: hiçbir şey
3. Bedel (aktifken):
   - Ekran kenarı kararır (vinyet)
   - Sesler boğuklaşır (önceden filtrelenmiş ses seti kullan,
     gerçek zamanlı filtre yok)
   - Savunma düşer (alınan hasar artar)
   - Hafif kromatik kayma
4. Kırılabilir duvar sistemi: Yankı ile görünür olan çatlaklar
5. UI: sol üstte Yankı göstergesi, 3 kademe görsel olarak ayırt edilir
6. YANKI'YA SORU SORMA (docs/derinlestirme.md 2.1): ayrı bir tuş.
   Rey içindeki sese soru yöneltir (düşünce baloncuğu ikonu, kelime yok).
   - BERRAK: doğru cevap
   - BULANIK: kısmi/eksik cevap
   - Ve bazen YALAN söyler — oyuncu kademeyi bildiği için riski kendi hesaplar
   Bu, ana mekaniği pasif buff'tan bir ilişkiye çeviriyor.
7. KOLYE PUSULASI (docs/derinlestirme.md 3.1): Cemo'nun kolyesi bir
   pusula. Cemo'ya yaklaştıkça ısınır (parıltı + kalp atışı ritmi).
   KRİTİK: Kolye ile Yankı bazen ÇELİŞİR — farklı yönler gösterirler.
   Oyuncu hangisine güveneceğini seçer. Oyunun teması bu tek mekanikte.
8. Saldırgan şifa: 20 combo = küçük can yenilenmesi. Can şişelerini
   nadir tut. Korkak oynayan iyileşemesin.
9. Yankı ses kimliği: açıkken müzik yarım perde düşer (önceden hazırlanmış
   ikinci set), kendi kalp atışın duyulur ve combo yükseldikçe hızlanır

Bitince: Yankı'yı açtığımda hem yardım aldığımı hem bir şey kaybettiğimi
AYNI ANDA hissetmeliyim. Bu his bu oyunun kalbi.
```

---

## GÖREV 4 — Bölüm 2

```
Görev: Faz 4 — Bölüm 2'yi baştan sona kur.

docs/bolum-02.md bağlayıcıdır, oda oda takip et.

Yapılacaklar:
1. src/world/tilemap.py — 16x16 tile haritası, 9-slice mantığı
2. src/world/level.py — oda geçişleri, kontrol noktaları
3. docs/bolum-02.md'deki 8 odayı kur:
   - Oda 1: İniş (dövüşsüz, tırmık izi, ilk Yankı fısıltısı)
   - Oda 2: İlk Kan (3 Sürüklenen, ilki TEK BAŞINA)
   - Oda 3: Yukarı Bak (2 Tırmanan + 1 Sürüklenen)
   - Oda 4: Yankı Odası (kırılabilir duvar, mekaniğin doğduğu an)
   - Oda 4-A: Gizli Oda (80 altın + ilk tılsım, MÜZİK KESİLİR)
   - Oda 5: Patlayanlar (Şişkin tanıtımı)
   - Oda 6: Kaçınma Dersi (dar koridor, 4 düşman)
   - Oda 7: Mini-boss "Şişmiş Olan" (3 hamle, kapalı arena)
   - Oda 8: Çıkış (ikinci tırmık izi, bölüm sonu ekranı)
4. Mini-boss davranış ağacı: Savurma / Çöküş / Çağrı (%50 canda)
5. src/systems/economy.py — altın, sandık, docs/bolum-02.md'deki akış
6. Bölüm sonu ekranı: süre, combo rekoru, altın, gizli alan (x/1)
7. Ölüm: kontrol noktası, altının %30'u yerde kalır, Yankı bir kademe düşer
8. ÖĞRETİMİ MİMARİYLE YAP (docs/derinlestirme.md 5.1): hiçbir mekaniği
   metinle öğretme, geometriyle zorunlu kıl.
   - Oda 2: ilk düşmanın arkasında dar çıkıntı → 3. vuruşun geri ittiği
     kendiliğinden anlaşılır
   - Oda 6: koridor genişliği tam kaçınma mesafesi kadar → kaçınmayı
     keşfetmek zorunda kalır
9. GÖRÜNÜR AMA ULAŞILAMAZ ÖDÜL: Oda 3'te yukarıda görünen, şu an
   alınamayan bir sandık. İleri bölümlerdeki mekaniklerle (su seviyesi,
   fırlatma) erişilebilir olacak. Şimdilik sadece göster.
10. SIKIŞMA TESTİ: hiçbir odada oyuncu kalıcı olarak sıkışmamalı.
    Her gizli odanın çıkışı olsun. Bunu test et ve raporla.

Bitince: Bölüm 2 baştan sona oynanabilir olmalı. Hâlâ placeholder
grafiklerle — sanat sonraki görev.
```

---

## GÖREV 5 — ARA DEĞERLENDİRME (kendin yap, Claude Code'a verme)

Bölüm 2 placeholder grafiklerle oynanabilir durumda. **Şimdi dur ve oyna.**

- [ ] Kutularla bile dövüş eğlenceli mi?
- [ ] Kill cancel akışı hissediliyor mu?
- [ ] Hitstop vuruşları "tokat gibi" yapıyor mu?
- [ ] Yankı'nın bedeli hissediliyor mu?

**Eğer renkli dikdörtgenlerle eğlenceli değilse, sprite eklemek kurtarmaz.**
Devam etmeden önce dövüşü düzelt.

Eğlenceliyse: Görev 6'ya geç.

---

## GÖREV 6 — MENÜ VE UI (işlevsel katman)

```
Görev: Ana menü, karakter seçimi, ayarlar, duraklatma menüsü.
Bu görevde İŞLEVSELLİK öncelikli — sahne/cila bir sonraki görevde.

docs/menu-ui.md bağlayıcıdır. CLAUDE.md bölüm 9 ve 10 zorunlu.

Yapılacaklar:
1. src/ui/menu.py — menü sahne yöneticisi, üç girdi yöntemi eşzamanlı
   (klavye + gamepad + fare). Mod değiştirme gerekmesin.
   Fare hareket edince imleç görünür, klavye kullanılınca kaybolur.
2. Ana menü butonları: DEVAM ET / YENİ OYUN / AYARLAR / EKSTRALAR / ÇIKIŞ
   - DEVAM ET en üstte ve ÖNCEDEN SEÇİLİ
   - Kayıt yoksa DEVAM ET GÖRÜNMEZ (gri değil, yok)
   - ÇIKIŞ bir boşlukla ayrılmış
   - Hiçbir geçiş 12 kareyi geçmesin
3. DEVAM ET bilgi kartı: bölüm no + adı, süre, altın, Yankı kademesi,
   gizli alan sayacı (docs/menu-ui.md bölüm 3)
4. YENİ OYUN üzerine yazma diyaloğu — İPTAL varsayılan seçili
5. Karakter seçim ekranı (docs/menu-ui.md bölüm 4):
   seçili büyük+aydınlık+animasyonlu, diğeri küçük+karanlık+durgun.
   Rey seçiliyken fısıltı sesi, Ardo seçiliyken TAM SESSİZLİK.
6. Ayarlar: üç sekme (GÖRÜNTÜ / SES / OYNANIŞ), docs/menu-ui.md bölüm 5'teki
   tüm seçenekler dahil. Erişilebilirlik seçenekleri "Kolay Mod" diye
   etiketlenmez, hiçbir şeyi kilitlemez.
7. Duraklatma menüsü: arka planda oyun görünür, karartılmış + bulanık
   (bulanıklık: 4× küçült → 4× büyüt, Gaussian gerekmez).
   ANA MENÜ'ye basınca "İlerlemen kaydedildi ✓" AÇIKÇA yazsın.
8. src/systems/save.py — JSON. HER ZAMAN save.json + save.bak.json.
   Yazma sırasında çökme olursa yedekten dön.
9. HUD: aşamalı açığa çıkarma. Can hasardan 3 sn sonra kaybolur, altın
   sayacı toplayınca belirir, Yankı göstergesi kademe değişince yanıp söner.
   Keşifte ekran tamamen temiz olabilmeli.

Bitince: menü tamamen gezilebilir olmalı, üç girdi yöntemiyle de.
Çirkin olabilir — hızlı ve doğru olsun.
```

---

## GÖREV 7 — MENÜ SAHNESİ (cila)

```
Görev: Ana menü sahnesini kur. docs/menu-ui.md bölüm 1, 2 ve 11.

Yapılacaklar:
1. 10 katmanlı sahne (docs/menu-ui.md bölüm 1):
   derin karanlık → arka duvar → sarkan zincirler → toz → MOR ALEV →
   aura → karakterler → zemin → ön toz → vinyet
2. Statik katmanları TEK BİR YÜZEYE PİŞİR, her karede yeniden çizme.
   Sadece hareketli katmanlar üstüne çizilir.
3. Mor alev: 6 karelik döngü + aura + kıvılcımlar.
   Aura 2.5 saniyelik sinüs ile ±%12 "nefes alır".
4. Ucuz glow: alev sprite'ını 4× küçült → 4× smoothscale ile büyüt →
   BLEND_RGB_ADD ile ekle. SADECE ışık katmanı için — oyun içi
   piksel art'a asla smoothscale uygulama.
5. RÜZGÂR ANİMASYONU (dikey dilim kaydırma):
   Pelerin/saç için ayrı kare çizme. Sprite'ı 1-2 piksellik yatay
   şeritlere böl, her şeridi sinüsle yatay kaydır:
     offset = amplitude * sin(time * frequency + y * wave_length)
   Alt şeritler az, üst şeritler çok kayar (kumaş fiziği).
   Bu teknik sonra bayraklar, örümcek ağları, su yüzeyi için de kullanılacak.
6. Rey ve Ardo sırt sırta, aralarında 6-8 piksel boşluk. Dokunmuyorlar.
   Rüzgâr sağdan sola — ikisinin de saçı/pelerini AYNI yönde.
7. Işık yayılımı: karakterlerin alev tarafındaki kenarına echo_violet
   katmanı (additive). Diğer taraf karanlık.
8. Parallax: fare/analog pozisyonuyla katmanlar ters yönde ±2-4 piksel.
9. MENÜNÜN İLERLEMEYE GÖRE DEĞİŞMESİ (docs/menu-ui.md bölüm 2) —
   5 aşama. Aynı sprite'lar, farklı konum + palet:
   - Aşama 1 (yeni oyun): sadece Rey, turuncu alev, kolye elinde
   - Aşama 2 (B3 sonrası): alev MORA döner, arkada belirsiz bir gölge
   - Aşama 3 (B6 sonrası): Ardo belirir, 8 piksel mesafe
   - Aşama 4 (B16 sonrası): mesafe 3 piksele iner, Ardo'nun eli omzunda
   - Aşama 5 (oyun bitti): Cemo da var, alev turuncu, rüzgâr durmuş,
     gün ışığı
10. Sahne geçişi: mor alev büyür → ekranı kaplar → küçülür → yeni sahne
11. ARDEKO STUDIOS INTRO (docs/menu-ui.md 0.1) — ~4.5 saniye:
    siyah → kıvılcım → mor alev doğar → logo ALEVİN IŞIĞIYLA belirir
    (fade değil, ışık yayıldıkça görünür) → alev söner → kararma.
    Logo dosyası assets/ altında verilecek. Tam sayı ölçekle,
    smoothscale KULLANMA. Ses: tek kıvılcım + alçak uğultu, müzik yok.
12. MENÜNÜN KURULMASI (0.2): intro sonrası ekran menüye KESMEZ.
    Kamera mor alevin çok yakınından yavaşça geri çekilir →
    kaide → mahzen → karakterler → durur → butonlar tek tek belirir
    (4 kare arayla, alttan 2px kayarak). ~3 saniye.
13. DİKEY YOLCULUK (0.3, 0.4) — menüden oyuna kesintisiz geçiş:
    - YENİ OYUN: kamera mor alevden YUKARI çıkar (taş tonoz → üst kaya →
      toprak/kökler → köy/gece) ve Bölüm 1 başlar. 4-5 saniye.
    - DEVAM ET: aynı geçiş ters yön, kaldığın bölüme kadar iner.
      Ne kadar ilerlemişsen o kadar uzun düşersin.
    - Tek uzun dikey doku (480 × ~3000), 4-5 parallax katmanı, y-ofset.
    - KRİTİK: ofseti TAM SAYIYA yuvarla (int/round). Ondalık ofset
      piksel art dokusunu titretir — en yaygın hata budur.
    - Hız eğrisi: smoothstep → t*t*(3-2*t)
    - Hafif dikey motion blur: aynı yüzeyi 3 kez 1px kaydırıp %33 alfa
    - Ses yükselirken değişir: mahzen uğultusu azalır, rüzgâr/böcek artar
    - Bölüm verilerini geçiş oynarken ARKA PLANDA yükle → oyuncu hiç
      yükleme ekranı görmez
14. HIZLANDIRMA SİSTEMİ (0.5) — ani atlama YOK:
    Tuşa basılı tutunca geçiş 3 KAT HIZLANIR ve akıcı biçimde varır.
    Sert kesme yok. 2 saniye sonra altta küçük ipucu:
    "Hızlandırmak için basılı tut"
    Uygulanır: Ardeko intro, menünün kurulması, dikey yolculuk, ara sahneler.
    İSTİSNA: Bölüm 3'teki "Mor" sahnesinin 2 saniyelik karanlığı
    hızlandırılamaz — zamanlamaya bağlı, hızlanırsa etkisi ölür.
15. Yükleme ekranı: mor alev + rastgele hikâye satırı (20-30 satır yaz,
    zindan hakkında kısa ve şiirsel)

Bitince: menü ekranı tek başına bir tanıtım görseli gibi durmalı.
Steam sayfası kapağı buradan çıkabilmeli.
```

---

## GÖREV 8 — Bölüm 3

```
Görev: Bölüm 3 "Meşale Mahzeni". docs/bolum-03.md bağlayıcıdır.

Bu bölüm B2'den daha karmaşık — dikkatli oku.

Yapılacaklar:
1. IŞIK SİSTEMİ GENİŞLETMESİ: 5+ eşzamanlı ışık kaynağı.
   Işık maskesini TEK yüzeyde topla, her kaynağı BLEND_RGBA_SUB ile
   aynı yüzeye işle. Kaynak başına ayrı geçiş YAPMA.
2. MEŞALE EKONOMİSİ:
   - Meşale taşırken combo 3'lü değil 2'li, bitirici yok
   - Yuvaya konabilir (ışık orada kalır)
   - Fırlatılabilir (yay çizer, düştüğü yerde yanar)
   - Meşale taşırken zıplanamaz
3. SES HARİTASI (sonar): Yankı aktive edilince 1 saniyelik dalga yayılır,
   duvarlar/düşmanlar/platformlar beyaz konturla bir an görünür ve söner.
   Bedeli: dalga düşmanları da uyandırır.
4. GÖLGE SÜRÜKLENEN: yeni düşman varyantı. Işıkta donar (saldıramaz ama
   ölmez), karanlıkta canlanır. Öldürmek için ışıkta dövmek gerek.
5. MUM BEKÇİSİ (Oda 3-A): konuşmayan, saldırmayan, saldırılamayan NPC.
   Ticaret: altın koy, karşılığında meşale / Sönmez Fitil / koruyucu mum.
   Gözleri sprite değil, İKİ PARÇACIK EMİTÖRÜ — titreşmeli, canlı görünmeli.
   Duvarda sönmüş mumlar (her sönmüş mum bir ölü).
   Kendi müzik teması olsun — B7, B12, B16'da tekrar çıkacak.
6. MOR ALEV (Oda 5) — bölümün kalbi:
   - Alınabilir VEYA bırakılabilir. Oyun bunu HİÇ SÖYLEMEZ.
   - Alınca: sönmez, ışık 2 kat, Yankı bir kademe yükselir ve orada kalır,
     gölge düşmanlar yaklaşamaz
   - Bedeli: Yankı sürekli konuşur (sessizlik yok), yalan ihtimali artar,
     Mum Bekçisi ticaret yapmaz, düşmanlar daha uzaktan fark eder
   - Bölüm sonu ekranında "Mor Alev: alındı / bırakıldı" yazsın
   - save.json'da sakla — B14'ün twist sahnesini etkileyecek
   - Rengi paletten: echo_violet (sadece Yankı ile ilişkili şeylerde)
7. 8 odayı kur (docs/bolum-03.md "Oda Akışı")
8. MİNİ-BOSS "Sönmüş Olan": 3 hamle (Karanlık Dalgası / Sürükleme /
   Mum Çağrısı). Arena ortasında yakılabilir mangal — yanan mangal
   Karanlık Dalgası'nı iptal eder, boss mangalı söndürmeye çalışır.
   Mangal yanarken boss sersemler (combo penceresi).
9. 4 ARA SAHNE (docs/bolum-03.md içinde panel panel yazılı):
   - "İniş" (kamera aşağı pan, ışık yarıçapı 0'a düşer)
   - "Duvardakiler" (çeteleler, müzik TAMAMEN kesilir)
   - "Mor" (Panel B'de 2 SANİYE TAM KARANLIK ve TAM SESSİZLİK —
     oyuncu oyunun donduğunu sanmalı, sonra mor ışık gelir)
   - "Üçüncü İşaret" (kolye titreşir, aşağıda turuncu bir ışık hareket eder)

KARANLIK ≠ SİYAH. Tam siyah ucuz durur. En koyu palet rengi + hafif mavi
ton. Karanlıkta bile siluetler çok hafif seçilsin (%8 alfa) — oyuncu
tamamen kör olmasın.
```

---

## GÖREV 9 — Sanat Geçişi

```
Görev: Faz 5 — placeholder'ları gerçek sprite'larla değiştir.

docs/asset-plani.md bölüm 3 (Tutarlılık Protokolü) BAĞLAYICIDIR.

Yapılacaklar:
1. src/art/spritegen.py — prosedürel sprite üretimi:
   - draw_humanoid(surf, palette, pose, outfit, facing)
   - draw_creature(surf, palette, body_type, pose)
   Rey, Ardo ve insansı düşmanlar AYNI iskeletten çıkmalı.
2. Rey'in tam animasyon seti (docs/asset-plani.md bölüm A):
   boşta, yürüme, koşma, zıplama, düşüş, iniş, saldırı 1-2-3,
   kaçınma, hasar, ölüm, Yankı aktif pozu
3. Üç düşman + mini-boss sprite'ları
4. Katman 1 tileset — 9-slice, 3-4 duvar varyantı (tekdüzelik kırılsın)
5. src/art/particles.py — slash yayı, impact, kan, toz, kaçınma izi,
   sandık parıltısı
6. Hikâye dekorları: tırmık izi (3 varyant), iskelet, sönmüş meşale
7. assets/REGISTRY.md — üretilen her şeyi kaydet

Stil sözleşmesine harfiyen uy: ışık sol üstten, kontur en koyu 2. renk,
2 piksel göz, altta elips gölge.

BORU HATTINI KULLAN (docs/asset-boru-hatti.md):
- Üretilen her sprite tools/quantize.py'den geçsin
- Kontur ve gölgelemeyi elle yapma — tools/outline.py ve tools/shade.py
- Her üretim turundan sonra tools/preview.py çalıştır, kontak sayfasına bak
- tools/silhouette.py ile siluet testini otomatik yap
- Sprite sayısı 50'yi geçince tools/atlas.py ile paketle
- tools/colorblind.py ile 3 renk körü palet varyantını üret

Okunabilirlik düzeltmeleri (prototipten):
- Platform kenar şeridini güçlendir, 1px açık kontur ekle
- Meşale ışık yarıçapını %30 artır
- Düşman siluetleri 1 karede tanınabilir olsun

Bölüm 3 ve menü asset'leri:
- Mor alev (6 kare) + kaide
- Mum Bekçisi (kukuleta, boş yüz — gözler parçacık, sprite değil)
- Sönmüş/yanan mumlar, mum duvarı
- Gölge Sürüklenen (yarı saydam varyant)
- "Sönmüş Olan" mini-boss
- Meşale yuvası (yanan/sönmüş), fırlatılan meşale
- Menü sahnesi: tonoz kemerleri, sarkan zincirler, ıslak zemin
- Rey ve Ardo'nun menü pozları (sırt sırta, 5 aşama için konum varyantları)
- Cemo'nun menü sprite'ı (aşama 5)
```

---

## GÖREV 10 — Ses ve Son Cila

```
Görev: Faz 6 — ses tasarımı ve son cila.

docs/bolum-02.md "Ses Tasarımı" bölümü bağlayıcıdır.

Yapılacaklar:
1. src/audio/ — ses yöneticisi. DİKEY KATMANLAMA, 4 katman
   (docs/derinlestirme.md 6.1):
   - Ambient (hep çalar): drone, damla
   - Ritim (düşman görününce): davul
   - Melodi (dövüş başlayınca): tema
   - Yoğunluk (10+ combo veya boss): tam enstrümantasyon
   Pygame'de: 4 ayrı Sound aynı anda döngüde, sadece set_volume() değişir.
   Middleware gerekmez.
2. Ses efektleri: vuruş (4), düşman (8), ayak sesi zemine göre (6),
   UI (3), sandık/kapı (2), Yankı fısıltıları (3)
   → Sentez + ücretsiz kütüphane karışımı olabilir
3. Yankı için filtrelenmiş (boğuk) ses seti — kritik ~15 ses
4. Combo yükseldikçe vuruş sesinin perdesi hafif yükselsin (+%3 / 5 combo)
5. Oda 4-A'da müzik TAMAMEN kesilsin — sadece meşale çıtırtısı.
   Bunu SİSTEMLEŞTİR: gizli alan → sessizlik; boss ölürken → 2 saniye
   tam sessizlik sonra zafer sesi. Sessizlik bir enstrümandır.
6. AYARLAR MENÜSÜ — erişilebilirlik dahil (CLAUDE.md bölüm 9):
   - Ses seviyeleri, tam ekran
   - Ekran sarsıntısı kapatma
   - Tam tuş yeniden atama (klavye + gamepad)
   - Renk körü modu: 3 palet varyantı (protanopi/döteranopi/tritanopi).
     Palet tek kaynak olduğu için bu neredeyse bedava.
   - UI ölçekleme (2 kademe)
   - Granüler zorluk: alınan hasar %50/75/100/150, düşman hızı %75/100,
     Yankı cezası açık/kapalı, otomatik combo açık/kapalı
   - Dil: Türkçe + İngilizce
7. Ana menü + karakter seçim ekranı iskeleti (Ardo henüz oynanamaz,
   "yakında" olarak göster)

Bitince: dikey dilim tamamlanmış olmalı. Bölüm 1-3 + menü + karakter
seçimi oynanabilir, cilalı ve Steam demosu olarak sunulabilir durumda.
```

---

## GÖREV 11 — Değerlendirme (kod değil, karar)

Bu görevi Claude Code'a verme. **Kendin yap:**

1. Bölüm 2'yi baştan sona oyna. Birkaç kez.
2. 3 kişiye oynat, izle, konuşma.
3. Kontrol listesi (docs/bolum-02.md son bölümü):
   - [ ] Dövüş 30 dakikada sıkmıyor
   - [ ] Kill cancel akışı hissediliyor
   - [ ] Hitstop vuruşları "tokat gibi" yapıyor
   - [ ] 3 kişiden 2'si gizli odayı yardımsız buluyor
   - [ ] Yankı'nın bedeli hissediliyor ama sinir bozmuyor
   - [ ] Mini-boss ilk denemede zor, 2-3'te geçilebilir
   - [ ] **Bölüm sonunda "bir bölüm daha oynayayım" hissi var**

Son madde yoksa: **dur.** 17 bölüm daha yapma, önce bu bölümü düzelt.

Varsa: iki iş paralel gider —
- **Faz 2:** Bölüm 1, 3, 4, 5, 6 + Boss 1 + Ardo'nun girişi
- **Steam sayfasını AÇ.** Oyun bitmeden. Araştırma net: Next Fest'te
  kazanacağın wishlist, festivale girerken sahip olduğun wishlist ile
  0.825 korelasyonda — indie pazarlamada görülmemiş bir güç. Soğuk
  başlatılan demonun ilk %5'e girme şansı 20'de 1. Momentum önceden
  toplanır, festivalde toplanmaz.
- Demo kapsamı: Bölüm 1+2+3 ≈ 25 dakika. Cilalı 30 dakikalık demo,
  kaba 2 saatlik demoyu dönüşümde 3:1 geçiyor.
- Geliştirme sürecini Ardeko kanallarından paylaş — wishlist'in en ucuz
  kaynağı bu.

---

## GENEL PROMPT İPUÇLARI

- Her görevin başına ekle: **"CLAUDE.md'yi oku, sonra docs/ içinden ilgili belgeyi oku."**
- **Büyük görevlerde plan modu kullan** (Shift+Tab veya /plan). Claude Code önce keşfeder ve yazılı plan sunar, kod yazmaz. Sen onaylayınca uygular. Bir özellik ~20 karar noktası içerir; her birinde %80 isabet, hepsinde doğru olma ihtimalini %1'e düşürür. Plan bunu çözer.
- **Kanıt iste:** "çalışıyor" yeterli değil. Test çıktısını, çalıştırdığı komutu, sonucu göstersin.
- Claude Code içerik üretmeye başlarsa (sırası gelmemiş bölüm/düşman/boss): **"Altyapı serbest ama ileri bölüm içeriği yazma, sırası gelince yapacağız."**
- Her görev sonunda önerilerini iste: **"Ne eksik gördün, ne önerirsin?"** — kodu yazarken fark ettiği şeyler değerli.
- Çok dosya okunması gerekiyorsa **alt-ajan** kullanmasını iste — ana bağlam temiz kalsın.
- Uzun oturumlarda ara ara: **"Şu ana kadar ne yaptın, ne kaldı?"**
- Bir görev çok büyük gelirse ikiye böl — ama sırayı bozma.
- **CLAUDE.md'yi kısa tut.** Şişerse Claude Code ona daha az uyar. Detay `docs/` altında kalsın.
