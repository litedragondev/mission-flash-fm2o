@echo off

cd /d "%~dp0"

python -m pip install pyautogui --quiet
python -m pip install keyboard --quiet
python -m pip install pygetwindow --quiet
python -m pip install tkinter --quiet
python -m pip install pyperclip --quiet
python -m pip install pillow --quiet

cls
echo Bienvenue dans Mission Flash
echo  __    __  __  ______  ______  __  ______  __   __       ______  __      ______  ______  __  __
echo /\ "-./  \/\ \/\  ___\/\  ___\/\ \/\  __ \/\ "-.\ \     /\  ___\/\ \    /\  __ \/\  ___\/\ \_\ \
echo \ \ \-./\ \ \ \ \___  \ \___  \ \ \ \ \/\ \ \ \-.  \    \ \  __\\ \ \___\ \  __ \ \___  \ \  __ \
echo .\ \_\ \ \_\ \_\/\_____\/\_____\ \_\ \_____\ \_\\"\_\    \ \_\   \ \_____\ \_\ \_\/\_____\ \_\ \_\
echo ..\/_/  \/_/\/_/\/_____/\/_____/\/_/\/_____/\/_/ \/_/     \/_/    \/_____/\/_/\/_/\/_____/\/_/\/_/

timeout /t 3

REM --- Vérifie l'existence du script Python ---
if not exist "bin\main.pyw" (
    echo ERREUR : Impossible de trouver bin\main.pyw
    pause
    exit /b
)

cd bin

REM --- Lance le script Python sans fenêtre console ---
start "" "pythonw.exe" "main.pyw"

exit
