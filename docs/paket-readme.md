> **NOT (23.08.2026):** `GOREVLER.md` silindi; gorev listesi ve
> proje durumu artik tek yerde: kok dizindeki `DEVIR.md`.
> Bu belge paketin ILK halini anlatiyor, tarihsel referans.

# LEGEND OF REY (LORE) — Tasarım Paketi

Ardeko Studios · Pygame · 18 bölüm · ~4 saat

---

## BU PAKETTE NE VAR

```
lore/
├── CLAUDE.md              ← Claude Code'un her oturumda okuduğu anayasa
├── GOREVLER.md            ← 11 sıralı görev promptu (SEN kullanacaksın, repoda kalabilir)
├── README.md              ← bu dosya
└── docs/                  ← 11 tasarım belgesi (Claude Code hepsini okuyabilir)
    ├── gdd.md                 Ana tasarım belgesi
    ├── yapi.md                18 bölümün akışı
    ├── dovus-sistemi.md       Dövüş, combo, game feel (kare değerleri)
    ├── ekonomi-uretim.md      Altın, zorluk eğrisi, üretim aşamaları
    ├── asset-plani.md         Asset stratejisi ve tutarlılık protokolü
    ├── asset-listesi.md       Kalem kalem asset dökümü
    ├── asset-boru-hatti.md    tools/ araçları — quantize, shade, preview
    ├── bolum-02.md            Dikey dilim — Bölüm 2 oda oda
    ├── bolum-03.md            Bölüm 3 — Meşale Mahzeni, Mor Alev
    ├── menu-ui.md             Intro, menü, geçişler, UX kuralları
    └── derinlestirme.md       Araştırma temelli ekler
```

---

## NASIL BAŞLANIR

**1.** Bu klasörü `lore/` olarak yeni bir yere kopyala
**2.** Ardeko logosunu `assets/logo/` altına koy
**3.** `git init` + ilk commit
**4.** Eski prototipi `_prototype/` altında sakla (referans, üstüne yazma)
**5.** Claude Code'u aç, `GOREVLER.md`'deki **Görev 0**'ı ver

Her görevin başına ekle:
> *"CLAUDE.md'yi oku, sonra docs/ içinden ilgili belgeyi oku."*

---

## GÖREV SIRASI

| # | Görev | Çıktı |
|---|---|---|
| 0 | Temel kurulum | Palet, Türkçe font, boru hattı, sabit adım döngü |
| 1 | Dövüş çekirdeği | Zincir, hitstop, kaçınma — **placeholder kutularla** |
| 2 | Düşman AI | 3 tip + saldırı hakkı sistemi |
| 3 | Yankı sistemi | 3 kademe, soru sorma, kolye pusulası |
| 4 | Bölüm 2 | 8 oda, mini-boss, gizli oda |
| **5** | **ARA DEĞERLENDİRME** | **Sen oynarsın. Kutularla eğlenceli mi?** |
| 6 | Menü ve UI | İşlevsel katman, kayıt, ayarlar |
| 7 | Menü sahnesi | Intro, mor alev, rüzgâr, dikey yolculuk |
| 8 | Bölüm 3 | Meşale ekonomisi, Mum Bekçisi, Mor Alev |
| 9 | Sanat geçişi | Placeholder → gerçek sprite |
| 10 | Ses ve son cila | Dikey katmanlama, erişilebilirlik |
| **11** | **DEĞERLENDİRME** | **3 kişiye oynat. Karar ver.** |

Görev 5 ve 11 Claude Code'a verilmez — senin karar noktaların.

---

## ÜÇ KURAL

**1. Kutularla oyna.** Görev 1-4 boyunca sprite yok, renkli dikdörtgen var. Kutularla eğlenceli değilse sprite eklemek kurtarmaz. Tersi her zaman doğru.

**2. Palet tek kaynaktır.** `tools/palette.json` erken sabitlenir, bir daha dokunulmaz. Kaynağı ne olursa olsun her görsel `quantize.py`'den geçer. Bu tek kural projenin en büyük riskini (tutarsızlık) yapısal olarak çözer.

**3. Dikey dilim geçmeden devam etme.** Görev 11'de "bir bölüm daha oynayayım" hissi yoksa **dur**. 15 bölüm daha yapmak yanlış temeli büyütmek olur.

---

## ERKEN YAPILACAK İKİ ŞEY

**Türkçe font.** Prototipte "Asagi bakma" yazıyor. ğ Ğ ü Ü ş Ş ı I i İ ö Ö ç Ç eksiksiz çalışmalı. Ayrıca Python'un `str.upper()` fonksiyonu Türkçe'de bozuk — `tr_upper()` yazılmalı. Görev 0'da.

**Steam sayfası.** Dikey dilim biter bitmez aç, oyun bitmeden. Next Fest'te kazanılan wishlist, festivale girerken sahip olunanla 0.825 korelasyonda — indie pazarlamada görülmemiş bir güç. Momentum önceden toplanır.

---

## OYUNUN ÖZÜ (tek paragraf)

Kafasının içindeki sesler yüzünden lanetli sayılan Rey, kaçırılan kardeşi Cemo'yu kurtarmak için zindana iner. Sesler ona yol gösterir — ama aslında onu çağırıyorlardır. Yolda Ardo'yla karşılaşır; birbirlerini kurtarırlar, birlikte savaşırlar, aralarında bir şey büyür. Hiçbiri konuşarak anlatılmaz: jestle, mekanikle, sessizlikle anlatılır.
