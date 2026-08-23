@echo off
REM Legend of Rey (LORE) - Ardeko Studios
REM Cift tiklayarak oyunu baslatir.
REM
REM Giris noktasi main.py. Eskiden run.py yaziyordu - o eski prototipin
REM (_prototype/) giris noktasiydi ve kokte yok, yani bu dosya calismiyordu.
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Sanal ortam bulunamadi. Once kurulum:
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install -r requirements.txt
    pause
    exit /b 1
)

REM Argumansiz: intro -^> ana menu. Belli bir sahneye gitmek icin
REM komut satirindan:  oyna.bat bolum1   /   oyna.bat dovus
".venv\Scripts\python.exe" main.py %*
if errorlevel 1 pause
