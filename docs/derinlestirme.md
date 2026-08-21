# LORE — Derinleştirme Belgesi
**GDD Ek E** · Araştırma temelli ekler · v0.1

Bu belge mevcut tasarımı değiştirmez, üstüne ekler. Her madde "neden" ile birlikte.

---

# BÖLÜM 1 — GAME FEEL: DERİN KATMAN

Mevcut game feel paketimiz iyi ama sektörün bildiği birkaç incelik eksik.

## 1.1 Yönlü Ekran Sarsıntısı ★

Şu an sarsıntımız rastgele. Araştırma net: geliştiriciler basit rastgele kamera titremesinden kaçınıp darbenin gücüyle hizalı yönlü sarsıntı kullanıyor — ağır bir yukarıdan çekiç darbesi kamerayı önce aşağı itmeli, sonra toparlamalı.

**LORE'a uygulaması:**
- Yatay savurma → kamera vuruş yönünde iter
- Bitirici (aşağı doğru) → kamera aşağı iter, sonra yaylanarak döner
- Şişkin patlaması → radyal, patlama merkezinden dışa

## 1.2 Sarsıntıya Rotasyon Ekle ★★

Çok az geliştiricinin yaptığı ama en çok fark yaratan detay: saf öteleme (translation) bir hata gibi okunur; birkaç ondalık derecelik rotasyon ise kuvvet gibi okunur.

**Uygulama:** Orta ve büyük sarsıntılara **0.3–0.8 derece** rotasyon ekle. Küçük sarsıntıda rotasyon yok.
Pygame'de: `pygame.transform.rotate` yerine, iç yüzeyi biraz büyük tutup döndürerek çiz (kenar boşluğu kalmasın).

**Üç büyüklük kuralı:** rutin aksiyon için küçük, gerçek bir olay için büyük. Bizde: normal vuruş (2px, rotasyon yok) / bitirici (5px, 0.4°) / boss-patlama (9px, 0.8°).

## 1.3 Parçacık Yönü ve Renk Eğrisi

Parçacıklar darbenin vektörü boyunca dışa fışkırmalı, bu darbenin yönünü görsel olarak pekiştirir. Başlangıç patlamasında keskin parlak renkler kullanıp hızla daha koyu, yumuşak duman veya moloza dönüştürmek ekranı kalabalıklaştırmadan yüksek etkili görsel geri bildirim sağlar.

**Uygulama:** Her parçacığın ömrü boyunca palet üzerinde bir renk yolu izlemesi: `flash_white → blood_bright → blood_dark → soot`. Palet dosyasında bu yollar tanımlı olsun.

## 1.4 Üçlü Senkron Kuralı

Game feel'in asıl sihri bu üç öğenin senkronizasyonunda: saldırı isabet ettiğinde hitstop aksiyonu dondurur, ekran darbenin ekseninde sarsılır, parçacıklar temas noktasından fışkırır.

**Kod kuralı:** Tek bir `on_hit()` fonksiyonu üçünü birden tetiklesin. Ayrı ayrı çağrılırsa kare kayması olur, his bozulur.

## 1.5 Squash & Stretch (ihmal edilen ucuz kazanç)

Fırlamadan önce çömelen, yükselirken uzayan bir zıplama, 1930'larda el çizimi animatörlerin kullandığı fikirlerin aynısını kullanır.

Pygame'de sprite'ı `pygame.transform.scale` ile hafif deforme etmek yeterli — yeni kare çizmeye gerek yok:
- Zıplama başlangıcı: 0.85 yatay, 1.15 dikey (3 kare)
- İniş: 1.2 yatay, 0.8 dikey (4 kare)
- Vuruş anında düşman: 1.3 yatay, 0.7 dikey (2 kare)

**Bu tek başına animasyon sayısını artırmadan oyunu canlandırır.**

## 1.6 Ses Perde Varyasyonu

Aynı ses üst üste çalınca beyin "tekrar" olarak algılar ve ucuz hisseder. Her vuruş sesini **±%8 rastgele perde** ile çal. Tek satır, devasa fark.

## 1.7 Kalıcılık (Permanence)

Vlambeer'in listesindeki en sevilen madde: öldürülen düşmanların izleri kalır. Kan lekeleri, moloz, kırılan kalkan parçaları zeminde **bölüm boyunca durur**.

**LORE'a özel bağlantı:** Bu, hikâyeye bedava hizmet ediyor — geri döndüğünde savaştığın yeri görürsün. Zindan "senin geçtiğin yer" olur.

---

# BÖLÜM 2 — YANKI'YI DERİNLEŞTİRME ★★★

Ana mekaniğimiz iyi ama daha ileri gidebilir. İşte oyunu "ilginç"ten "unutulmaz"a taşıyacak fikirler.

## 2.1 Yankı Bir Kaynak Değil, Bir Diyalog Olsun

Şu an Yankı pasif bilgi veriyor. Ya **soru sorabilseydin?**

**Mekanik:** Yankı'ya "sor" tuşu. Basınca Rey içindeki sese bir soru yöneltir (kelime yok — bir düşünce baloncuğu ikonu). Ses cevap verir:
- Berrak kademede: doğru cevap
- Bulanık kademede: kısmi/eksik cevap
- Ve **bazen yalan söyler** — ama hangi kademede olduğunu bilirsin, yani riski sen hesaplarsın

**Neden güçlü:** Oyuncu ana mekanikle *pazarlık* eder. Pasif buff değil, ilişki olur.

## 2.2 Yankı Sadakati (gizli sayaç)

Oyuncunun Yankı'ya ne kadar güvendiğini takip eden görünmez bir değer.

- Yankı'nın gösterdiği yoldan gidersen: sadakat artar
- Yankı'yı görmezden gelip kendi yolunu bulursan: sadakat azalır

**Etkisi:** Bölüm 14'teki twist sahnesi, sadakat değerine göre farklı oynanır. Çok güvendiysen ihanet daha acı; hiç güvenmediysen "biliyordum" anı. Aynı sahne, iki farklı duygu.

**Ucuz mu?** Evet — tek bir int, iki farklı ara sahne varyantı. Getirisi devasa.

## 2.3 Yankı Yankılanır: Ses Bulmacaları

Rezonans mekaniğini genişlet — sesin **fiziksel** olduğu odalar:
- Bağırdığın yerden ses yansır, duvarın ardındaki boşluğu haritalar (ekranda geçici bir "ses haritası")
- Belirli frekanslar belirli malzemeleri titretir (cam kırılır, taş sağlam kalır)
- Sessiz odalarda Yankı çok güçlü, gürültülü odalarda (şelale, rüzgâr) işe yaramaz

**Yeni bulmaca türü:** Gürültü kaynağını sustur ki Yankı'yı kullanabilesin.

## 2.4 Ardo'nun Karşı Mekaniği: İZ SÜRME ★★

Şu an Ardo'nun oynanışı "Yankı yok" — yani bir eksiklikle tanımlı. Bu zayıf tasarım. Ona **kendi güçlü mekaniğini** ver.

**İZ SÜRME:** Ardo geçmişi okur. Bir yere baktığında orada olan şeyin izini görür:
- Yerdeki ayak izleri kimin, ne zaman geçtiğini gösterir
- Duvardaki kan lekesi kısa bir hayalet-tekrar oynatır
- Cemo'nun geçtiği yolu Rey sesle bulur, Ardo izle bulur

**Neden mükemmel:** Rey **geleceği/gizliyi** duyar (ses = uzamsal), Ardo **geçmişi** görür (iz = zamansal). İkisi aynı zindanı iki farklı boyuttan okur. Aynı bölüm, iki farklı oyun.

Ve tematik olarak: Rey'in laneti onu çağıran şeyle bağlı, Ardo'nunki ise ölülerle. İkisi de yalnız — farklı şekillerde.

---

# BÖLÜM 3 — YENİLİKÇİ MEKANİK FİKİRLERİ

En iyi benzersiz mekanikler anlaşılması kolay ama şaşırtıcı derinlik sunanlardır — oyuncular temeli hızla kavrar, sonra oynadıkça katman katman karmaşıklık keşfeder. Aşağıdakiler bu ölçüte göre seçildi.

## 3.1 KOLYE — Cemo'nun Sesi ★★★

Kolye şu an sadece görsel bağlaç. Ona mekanik ver:

**Kolye bir pusuladır.** Cemo'ya yaklaştıkça ısınır (görsel: hafif parıltı; ses: kalp atışı gibi ritim). Zindanda kaybolduğunda yön verir — ama **Yankı ile çelişebilir**. Yankı bir yolu, kolye başka bir yolu gösterir.

**Kimin dediğini dinleyeceksin?** Bu, oyunun bütün temasını tek bir mekanik seçime indirger: sesler mi, kan bağı mı?

Bölüm 14'ün twist'i bunu doğrular — kolye hep doğruydu.

## 3.2 YARA SİSTEMİ (can barı yerine) ★★

Klasik can barı yerine: her ciddi hasar **kalıcı bir yara** bırakır, bölüm sonuna kadar.
- Kol yarası: combo penceresi 2 kare daralır
- Bacak yarası: hareket hızı %10 düşer
- Baş yarası: **Yankı bulanıklaşır**

Yaralar nefes bölümlerinde (ateş başı) sarılır. Ve **Ardo yaranı sarabilir** — romantik yayı mekaniğe bağlayan en güçlü an.

**Neden güçlü:** Hasar sayısal değil, hissedilir. Ve iyileşmek bir insana muhtaç olmayı gerektirir.

**Risk:** Ölüm sarmalı yapabilir. Çözüm: en fazla 3 yara, dördüncüde ölüm.

## 3.3 SESSİZ DİYALOG SİSTEMİ ★

Ardo ile iletişim: konuşma yok ama **jest seçimi** var. Bir anda üç ikon çıkar (elini uzat / başını salla / geri çekil). Seçimin ilişkiyi şekillendirir.

- Kelime yok → çeviri sıfır maliyet
- Seçim var → oyuncu ilişkiye sahip olur
- 3-4 kritik anda kullanılır, her sahnede değil

**B7 (el tutma), B8 (yara sarma), B16 (kurtarma), B18 (final)** — dört an yeter.

## 3.4 ZİNDAN HATIRLIYOR

Öldüğün yerde **kendi hayaletin** kalır. Yankı açıkken görünür, son anlarını tekrar oynar.
- Hollow Knight'ın Shade'i gibi ama dövüşmüyor — sadece izliyorsun
- Öldüğün altını oradan alırsın
- Ve psikolojik olarak: kendi hatanı seyredersin

Ardo'nun İz Sürme mekaniğiyle mükemmel örtüşür — o zaten geçmişi görüyor.

## 3.5 MEŞALE EKONOMİSİ

Meşale sadece B3'te değil, oyun boyunca bir kaynak olsun:
- Yanan meşale: görüş + Şişkin'i uzaktan patlatma
- Ama iki elin doluysa combo yapamazsın
- Meşaleyi fırlatabilirsin — ışık orada kalır, sen karanlıkta savaşırsın

**Karar anı:** Görmek mi, dövüşmek mi?

## 3.6 DÜŞMAN EKOLOJİSİ (küçük detay, büyük dünya hissi)

Düşmanlar birbirine de tepki verir:
- Şişkin patlarsa yakındaki Sürüklenenler ölür → oyuncu bunu silah olarak kullanır
- Muhafızlar Çürüyenlerden **kaçar** (katman geçişinde görülür) → dünya kendi kurallarına sahip
- Yankı'nın Çocukları diğer düşmanları da avlar → derinlerde ekosistem çöküyor

Kod maliyeti düşük (düşmanlar arası hasar zaten var), dünya hissi çok yüksek.

---

# BÖLÜM 4 — DÜŞMAN TASARIMI (Hollow Knight dersleri)

## 4.1 Renk Kodlu Tehlike ★

Hollow Knight ortamları karanlık olduğu için parlak renkler öne çıkar; deneyimli oyuncular turuncu parlayan bir düşman görürse hemen kaçması gerektiğini bilir.

**LORE'a uygulaması:** Zindanımız zaten karanlık. Palete **tehlike rengi** ekle (turuncu-kırmızı). Her düşman saldırı tell'inde bu renkle parlasın. Renk körlüğü için: parlama + siluet değişimi birlikte.

## 4.2 Her Düşmanın Bir Ritmi Var

Her düşmanın bir ritmi var; keskin kaçınmalar ve zamanlanmış vuruşlarla etraflarında dans etmeyi öğrenmek bir şifreyi çözmek gibi hissettiriyor.

**Tasarım kuralı:** Her düşman tipine bir **ritim imzası** ver — saldırı aralıkları sabit ve öğrenilebilir olsun. Rastgele saldıran düşman öğrenilemez, sadece sinir bozar.

| Düşman | Ritim |
|---|---|
| Sürüklenen | Yavaş 3'lük (bekle-bekle-vur) |
| Tırmanan | Ani, tek vuruş, uzun bekleme |
| Kalkanlı | Çift vuruş, sonra açık pencere |
| Mızraklı | Uzun tell, hızlı geri çekilme |

## 4.3 Saldırgan Şifa (Hollow Knight'ın Soul sistemi)

İster daha fazla hasar vermek ister iyileşmek isteyin, saldırıya geçmek zorundasınız — bu, statik kalamayacağınız güçlü bir geri bildirim döngüsü yaratır ve sizi hareket etmeye, incelemeye, denemeye zorlar.

**LORE'a uygulaması:** Can şişesi yerine (ya da yanında): **20 combo = küçük iyileşme**. Zaten planımızda vardı — ama bunu ana şifa yolu yap, şişeleri nadir kıl.

**Sonuç:** Korkak oynayan iyileşemez. Hızlı-akıcı dövüş kimliğimizle tam uyum.

## 4.4 Düşman Sağlık Barı Gösterme

Hollow Knight düşman canını göstermez. Oyuncu **tepkiden** okur — sendeleme, renk değişimi, hız düşüşü. Bu hem UI temizliği hem de düşmanı "sayı" olmaktan çıkarıyor.

**Öneri:** Normal düşmanlarda can barı yok, sadece görsel durum. Boss'larda var.

---

# BÖLÜM 5 — SEVİYE TASARIMI DERSLERİ

## 5.1 Öğretimi Mimariyle Yap

İkinci düşmanın yakınında zeminde bir çukur var ve bu tesadüf değil — oyuncu henüz zıplamayı çözmediyse, bu küçük çukur onu ilerlemek için zıplamaya zorluyor.

**Kural:** Hiçbir mekaniği metinle öğretme. Oyuncuyu o mekaniği kullanmak zorunda bırakan bir geometri kur.

**B2'ye uygulama:**
- Oda 2'de ilk düşmanın arkasında dar bir çıkıntı → oyuncu zincirin 3. vuruşunun geri ittiğini fark eder
- Oda 6'da koridor genişliği tam olarak kaçınma mesafesi kadar → kaçınmayı keşfetmek zorunda

## 5.2 Erken Ödülü Görünür Ama Ulaşılmaz Yap

Oyuncular nesnelerin, düşmanların ve tehlikelerin üzerinde zıplayabildiklerini öğrenir öğrenmez bir ampul anı yaşayıp buraya geri dönecekler — bu, dikkatli oyuncuyu ödüllendirir ve açılış bölgesine değer katar.

**B2'ye ekleme:** Oda 3'te yukarıda görünen ama şu an ulaşılamayan bir sandık. Bölüm 5'te (su seviyesi) veya B9'da (fırlatma) geri gelince alınabilir.

**Doğrusal yapıda bile bu çalışır** — "geri dön" değil, "sonraki oynayışta al" olur.

## 5.3 Sıkışma Korkusu

Çıkamayacağın bir odaya düşme riski her zaman vardır — ya da düşmanların çok güçlü olduğu bir gizli yere erişmek.

**Kural:** Hiçbir odada oyuncu kalıcı olarak sıkışmasın. Her gizli oda çıkışı olsun. Test listesine ekle.

---

# BÖLÜM 6 — SES SİSTEMİ DERİNLEŞTİRME

## 6.1 Dikey Katmanlama (bizim yaklaşımımız doğru)

Tüm stem katmanları aynı anda çalar, ama hangi katmanların duyulacağını oyun motoru kontrol eder; gerilim arttıkça katmanları açarsın, azaldıkça geri çekersin.

Hollow Knight her iki tekniği de kullandı: yatay yeniden sıralama bölge temalarını yönetirken, dikey katmanlama dövüş sırasında yoğunluğu ayarladı.

**LORE için 4 katman:**
1. **Ambient** (hep çalar) — drone, damla
2. **Ritim** (düşman görününce) — davul
3. **Melodi** (dövüş başlayınca) — tema
4. **Yoğunluk** (10+ combo veya boss) — tam enstrümantasyon

Pygame'de: 4 ayrı `Sound` nesnesi aynı anda döngüde, sadece `set_volume()` değişir. Middleware gerekmez.

## 6.2 Yankı'nın Ses Kimliği

Yankı açıkken sadece boğuklaşma değil:
- Müzik **yarım perde düşsün** (önceden hazırlanmış ikinci set)
- Kendi kalp atışın duyulsun, combo yükseldikçe hızlansın
- Yankı fısıltıları stereo'da sağdan sola gezinsin (Pygame stereo panning destekler)

## 6.3 Sessizliği Silah Olarak Kullan

Oda 4-A'da müziği kesme kararımız doğru. Bunu **sistemleştir**:
- Gizli alan → müzik kesilir
- Boss ölürken → 2 saniye tam sessizlik, sonra zafer sesi
- Bölüm 15 (Sessizlik) → sadece ayak sesi ve nefes

**Sessizlik, müzikten daha güçlü bir enstrümandır.**

---

# BÖLÜM 7 — ERİŞİLEBİLİRLİK

Erişilebilir tasarımın faydaları engelli oyuncuların çok ötesine geçer: altyazılar gürültülü ortamdakilere yardım eder, renk körü modları karmaşık sahnelerde herkes için görünürlüğü artırır.

## 7.1 Zorunlu Minimum (ucuz, yüksek getiri)

- **Ekran sarsıntısı kapatma** (zaten planda)
- **Tuş yeniden atama** — tam remapping
- **Renk körü modu** — 3 palet varyantı (protanopi, döteranopi, tritanopi). Palet dosyamız tek kaynak olduğu için bu **neredeyse bedava**
- **Tehlike göstergesi renk + şekil** — sadece renkle anlatma
- **UI ölçekleme** — 2 kademe

## 7.2 Dead Cells Modeli (granüler zorluk)

Zorluk ön ayarları yerine oyun tek tek mekanikleri ayarlamana izin veriyor: ne kadar hasar aldığın, düşmanların ne kadar hızlı hareket ettiği, tuzakların aktif olup olmadığı. "Kolay"ı seçmiyorsun — mücadelenin hangi parçalarını tutacağını seçiyorsun.

**LORE'a uygulaması** — Ayarlarda:
- Alınan hasar: %50 / %75 / %100 / %150
- Düşman hızı: %75 / %100
- Yankı ceza sistemi: açık / kapalı
- Otomatik combo: kapalı / açık (tek tuşla zincir)

**Neden önemli:** Hızlı-akıcı dövüş yüksek beceri istiyor. Bu ayarlar oyunu daha çok insana açar, tasarım niyetini bozmadan.

## 7.3 Türkçe + İngilizce

Diyalogsuz anlatım seçtiğimiz için **çeviri maliyeti neredeyse sıfır** — sadece menüler ve birkaç UI metni. İngilizce desteğini baştan ekle, Steam'e çıkacaksan zorunlu.

---

# BÖLÜM 8 — TEKNİK: PYGAME PERFORMANS

## 8.1 Yüzey Dönüşümü (en yaygın hata)

Yüzey dönüşümünü (surface conversion) hız için kullanın. Yüklenen her görselde `.convert()` veya `.convert_alpha()` çağır. Unutulursa oyun 3-5 kat yavaşlar.

## 8.2 Çarpışma İçin Alt-Dikdörtgen

Çoğu oyun için 'alt-dikdörtgen çarpışması' daha iyidir — her sprite için gerçek görüntüden biraz daha küçük bir dikdörtgen oluşturun ve çarpışma için onu kullanın. Çok daha hızlı olur ve çoğu durumda oyuncu belirsizliği fark etmez.

**Bizim için:** Piksel-mükemmel çarpışma yapma. Hitbox'lar sprite'tan küçük olsun — hem hızlı hem oyuncu lehine (affedici).

## 8.3 Tek Spritesheet

Yükleme süresini azaltmak için 100 ayrı .png yerine tüm görüntüleri tek bir büyük görüntüde tutun — 100 dosya yerine tek dosya yüklersiniz.

Prosedürel üretim yaptığımız için: sprite'ları başlangıçta bir kez üretip **tek bir atlas yüzeyinde** sakla, her karede yeniden üretme.

## 8.4 Kaydırmalı Oyunda Dirty Rect

Tüm pencerenin her karede güncellendiği durumlarda bu teknik işe yaramaz — yumuşak kaydırmalı bir motor düşünün.

Bizim oyunumuz kaydırmalı → dirty rect işe yaramaz. Bunun yerine:
- Sadece görünür tile'ları çiz (kamera + 2 tile marj)
- Parçacık sayısına üst sınır (ekranda max 200)
- `pygame.Surface.blits()` ile toplu çizim

## 8.5 Işıklandırma Yaklaşımı

Meşale ışığı zaten çalışıyor. Ölçeklenebilir hale getirmek için:
- Işık maskesi tek bir karartma yüzeyi, `BLEND_RGBA_SUB` ile ışık delikleri açılır
- Işık yüzeyi **480×270**, ekrandan küçük — ucuz
- Yankı vinyeti aynı yüzeyi kullansın, ikinci geçiş yapma

---

# BÖLÜM 9 — YAYIN STRATEJİSİ (erken düşünülmeli)

## 9.1 Steam Sayfası Erken Açılmalı ★★★

Araştırmadaki en net bulgu: bir oyunun festival öncesi istek listesi sayısı ile etkinlik sırasında kazandığı istek listeleri arasındaki ilişki, verideki en güçlü korelasyondu (Spearman 0.825); karşılaştırma için çoğu indie pazarlama korelasyonu 0.2–0.4 arasında.

Yani: festival, yanında getirdiğin momentumu ödüllendiriyor. Takipçi tabanı olmayan soğuk başlatılmış bir demonun ilk %5'e girme şansı kabaca 20'de 1.

**Karar:** Steam sayfasını **dikey dilim biter bitmez** aç. Oyun bitmeden. Wishlist toplamaya erken başla.

## 9.2 Demo Kapsamı

25-45 dakikalık içerik hedefleyin: kancalamaya yetecek kadar uzun, tek oturumda bitirilecek kadar kısa. Cilalı 30 dakikalık bir demonun istek listesi dönüşüm oranı, kaba 2 saatlik bir demoyu çoğu orta seviye indie kategorisinde kabaca 3:1 geçiyor.

**LORE demosu:** Bölüm 1 + 2 + 3 = ~25 dakika. Ardo'nun girişiyle (B6) bitirmek daha güçlü olur ama daha uzun.

## 9.3 Next Fest Zamanlaması

Bir oyun sadece bir kez Next Fest'e katılabilir, dolayısıyla çıkış pencerene uyan sürümü seç. Demo kapsamını festival son teslim tarihinden 3-4 hafta değil, 10-12 hafta önce planlayın.

## 9.4 Türk Indie Sahnesi

Türkçe geliştirilen, Türkçe hikâye anlatan bir oyun olarak yerel toplulukta doğal avantajın var. Ardeko Studios'un mevcut kanallarını (site, sosyal medya) devkanal olarak kullan — geliştirme sürecini paylaşmak wishlist'in en ucuz kaynağı.

---

# BÖLÜM 10 — ÖNCELİKLENDİRME

Hepsini yapamazsın. Getiri/maliyet oranına göre sıralama:

## Hemen yap (ucuz + yüksek etki)
1. Ses perde varyasyonu (±%8) — 1 satır
2. Sarsıntıya rotasyon — 5 satır
3. Yönlü sarsıntı — 15 satır
4. Squash & stretch — 20 satır
5. Parçacık renk yolu — palet dosyasına ekleme
6. Kalıcılık (kan lekeleri kalır) — 30 satır
7. Renk kodlu tehlike tell'i — palet + 1 kural
8. Düşman can barını kaldır — silme işi
9. `.convert()` her yerde — performans
10. Erişilebilirlik minimumu — palet zaten tek kaynak

## Dikey dilimde dene (orta maliyet, oyunu tanımlar)
11. **Kolye pusulası** ★ — temayı mekaniğe çeviriyor
12. **Yankı'ya soru sorma** ★ — ana mekaniği diyaloğa çeviriyor
13. Saldırgan şifa (combo = can)
14. Öğretimi mimariyle yapma (B2 geometrisi)
15. Dikey ses katmanlama (4 katman)

## Sonraki fazda (yüksek maliyet, yüksek getiri)
16. **Ardo'nun İz Sürme mekaniği** ★★ — ikinci oynayışı gerçekten farklı yapar
17. **Yara sistemi** — riskli ama unutulmaz
18. Yankı sadakati + iki farklı twist sahnesi
19. Sessiz jest diyalog sistemi
20. Zindan hatırlıyor (hayalet)

## Değerlendir, zorunlu değil
21. Meşale ekonomisi
22. Ses bulmacaları (rezonans genişletmesi)
23. Düşman ekolojisi
24. Dead Cells tarzı granüler zorluk

---

# EK: KAYNAKÇA NOTU

Bu belgedeki teknikler şu kaynaklardan derlendi: Vlambeer'in "The Art of Screenshake" (2013) sunumu, Jonasson & Purho'nun "Juice It or Lose It" (2012) sunumu, Steve Swink'in game feel modeli, Hollow Knight tasarım analizleri, Pygame resmi optimizasyon dokümantasyonu, ve 2026 Steam Next Fest veri analizleri.
