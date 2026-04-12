@echo off
echo ====================================================
echo   MONSOON FC - Atualizacao do Site
echo   %date% %time%
echo ====================================================
cd /d "C:\Users\Gamer\OneDrive\Desktop\monsoon-fc-site"
"C:\Users\Gamer\AppData\Local\Programs\Python\Python311\python.exe" scripts\update_and_deploy.py
echo.
echo Pressione qualquer tecla para fechar...
pause >nul
