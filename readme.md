# Legend of Rey (LORE)

Pygame ile yapılan, yandan görünümlü aksiyon-RPG. **Ardeko Studios.**

Kafasının içindeki sesler yüzünden lanetli sayılan **Rey**, kaçırılan
kardeşi **Cemo**'yu kurtarmak için zindana iner — ve o sesler ona yardım
ederken, aslında onu çağırıyordur.

18 bölüm · ~4 saat · 2 oynanabilir karakter (Rey, Ardo) · PC (klavye +
gamepad).

## Çalıştırma

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install pygame-ce numpy   # Windows
.venv/Scripts/python.exe main.py
```

Linux/macOS'ta `.venv/bin/python`. **Python 3.11+** gerekir.

```bash
.venv/Scripts/python.exe main.py dovus     # dövüş test odası
.venv/Scripts/python.exe main.py bolum3    # doğrudan Bölüm 3
```

## Belgeler

| Dosya | Ne için |
|---|---|
| **`CLAUDE.md`** | Bağlayıcı kurallar — bu repoda çalışan herkes (insan ya da AI) önce bunu okur |
| **`DEVIR.md`** | **Projenin durumu, kalan işler, öğrenilen dersler.** Tek devir belgesi. |
| `docs/` | Tasarım paketi — GDD, dövüş sistemi, bölüm tasarımları, asset planı |

Yeni bir oturuma devrederken: **`CLAUDE.md` → `DEVIR.md`** sırasıyla oku.

## Doğrulama

```bash
for f in tests/test_*.py; do .venv/Scripts/python.exe "$f" || echo "KIRIK: $f"; done
.venv/Scripts/python.exe tools/reachability.py    # her oda geçilebilir mi
.venv/Scripts/python.exe tools/roster.py          # düşman kadro sayfası
```

## Not

`_prototype/` terk edilmiş bir v2.x denemesidir — **referans olarak
bakılabilir, asla import edilmez.** Oradaki hikâye ve isimler (Aethelmoor,
Cael, Echobrand) artık geçerli değil.
