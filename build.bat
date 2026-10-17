@echo off
REM Gumagawa ng ECL.exe sa dist\ folder (may sariling icon, walang console window)
python tools\make_icon.py
pyinstaller --noconsole --onefile --name ECL --icon assets\ecl.ico --add-data "assets;assets" --collect-all customtkinter app.py
echo.
echo Tapos na. Nasa dist\ECL.exe ang app.
pause