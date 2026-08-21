"""Coklu dil destegi - Turkce ve Ingilizce.

Anlatim diyalogsuz tasarlandi (CLAUDE.md 10), bu yuzden ceviri yuku yalnizca
menulerde: ~80 dize. Tek bir diyaloglu RPG sahnesi bundan fazla tutar.

Kullanim:
    from src.ui.i18n import t
    text.draw(surface, t("menu.new_game"), x, y)
    text.draw(surface, t("hud.combo", count=7), x, y)

**Dizeler JSON'da gosterilecek halleriyle durur** - baslikar zaten buyuk
harfli yazilir. Bu bir kolaylik degil, bilincli bir karar: calisma zamaninda
buyuk harfe cevirmek dile bagli bir tuzak. `tr_upper("Continue")` -> "CONTINUE"
degil, noktali I ile "CONTİNUE" verir; Turkce icin dogru olan kural
Ingilizce'de bozar. Metin zaten dogru halde saklanirsa sorun hic dogmaz.
Dinamik metin icin dile duyarli `upper()` / `lower()` asagida.

Eksik anahtar **sessizce gecmez**: kaynak dile duser ve kaydedilir. Font'un
eksik glif davranisinin aynisi - yarim cevrilmis bir menu fark edilmeden
surume giremesin. tests/test_lang.py bunu ayrica dogrular.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ui import text

LANG_DIR = Path(__file__).resolve().parent / "lang"

# Kanonik dil: tasarim belgeleri Turkce, dizeler once burada yazilir.
# Eksik ceviri bu dile duser - bos ekran yerine anlasilir metin gorunur.
SOURCE_LANGUAGE = "tr"
DEFAULT_LANGUAGE = "tr"

_tables: dict[str, dict[str, str]] = {}
_current: str = DEFAULT_LANGUAGE
_missing: set[tuple[str, str]] = set()


class LanguageError(RuntimeError):
    """Dil dosyasi okunamadi ya da bozuk."""


def available() -> tuple[str, ...]:
    """Diskteki dil kodlari. Yeni dil = yeni JSON, kodda degisiklik yok."""
    return tuple(sorted(p.stem for p in LANG_DIR.glob("*.json")))


def table(code: str) -> dict[str, str]:
    """Bir dilin tablosu. Bir kez okunur, sonra bellekte kalir."""
    cached = _tables.get(code)
    if cached is not None:
        return cached

    path = LANG_DIR / f"{code}.json"
    if not path.is_file():
        raise LanguageError(f"dil dosyasi yok: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise LanguageError(f"{path.name} bozuk: {exc}") from exc

    # Ic ice sozluk yazmak kolay okunur; kodda duz anahtar isteriz.
    flat = _flatten(raw)
    _tables[code] = flat
    return flat


def _flatten(node: Any, prefix: str = "") -> dict[str, str]:
    """{"menu": {"quit": "CIKIS"}} -> {"menu.quit": "CIKIS"}"""
    out: dict[str, str] = {}
    for key, value in node.items():
        if key.startswith("_"):          # yorum alanlari
            continue
        full = f"{prefix}{key}"
        if isinstance(value, dict):
            out.update(_flatten(value, f"{full}."))
        else:
            out[full] = str(value)
    return out


def set_language(code: str) -> None:
    """Aktif dili degistirir. Aninda gecerli - yeniden baslatma gerekmez.

    Metin yuzeyleri dizeyle anahtarlaniyor (text.py), dize degisince anahtar
    da degisir; bayat onbellek diye bir sorun olusmuyor.
    """
    global _current
    table(code)                          # Once dogrula, sonra ata
    _current = code


def current() -> str:
    return _current


def t(key: str, /, **kwargs: Any) -> str:
    """Anahtari aktif dilde cozer.

    `key` **konumsal-yalniz** (`/`): aksi halde `{key}` yer tutuculu bir
    dize `t("...", key=...)` diye cagrildiginda "birden fazla deger" hatasi
    veriyor. Bolum 1'in "{key} ile saldir" metni tam bunu tetikledi.

    Eksikse kaynak dile duser ve kaydeder. O da yoksa anahtarin kendisini
    koseli parantez icinde dondurur - ekranda hemen goze batsin.
    """
    value = table(_current).get(key)
    if value is None:
        _missing.add((_current, key))
        value = table(SOURCE_LANGUAGE).get(key)
    if value is None:
        _missing.add((SOURCE_LANGUAGE, key))
        return f"[{key}]"
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            # Cevirmen yer tutucuyu bozmus olabilir; metni ham gosterip
            # devam et - oyun bir ceviri hatasi yuzunden cokmesin.
            _missing.add((_current, f"{key} (bicimlendirme)"))
            return value
    return value


def t_or_raw(value: str) -> str:
    """Anahtarsa cevirir, degilse oldugu gibi doner.

    **Yalnizca eski surumden gelen veri icin.** Kayit dosyalari bir donem
    bolum adini duz metin tutuyordu ("Koy"); o kayitlari acan oyuncu
    "[Koy]" gormemeli. Arayuz metinlerinde kullanma - orada cozulemeyen
    anahtarin goze batmasi **isteniyor**.
    """
    if value in table(_current) or value in table(SOURCE_LANGUAGE):
        return t(value)
    return value


def upper(value: str) -> str:
    """Dile duyarli buyuk harf.

    Turkce'de i -> I degil I; Ingilizce'de i -> I. Ayni fonksiyonu iki dile
    uygulamak birini mutlaka bozar.
    """
    if _current == "tr":
        return text.tr_upper(value)
    return value.upper()


def lower(value: str) -> str:
    if _current == "tr":
        return text.tr_lower(value)
    return value.lower()


def missing() -> tuple[tuple[str, str], ...]:
    """Cozulemeyen anahtarlar - (dil, anahtar)."""
    return tuple(sorted(_missing))


def report_missing() -> None:
    """Eksikleri bir kez yazdirir. Oyun kapanirken cagrilir."""
    if not _missing:
        return
    print(f"[i18n] {len(_missing)} anahtar cozulemedi:")
    for code, key in sorted(_missing):
        print(f"  {code}: {key}")
