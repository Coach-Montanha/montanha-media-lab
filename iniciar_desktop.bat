@echo off
title Montanha Media Lab - Desktop Edition
chcp 65001 >nul

echo ========================================================
echo    ⛰️  MONTANHA MEDIA LAB - ESTÚDIO DESKTOP
echo ========================================================
echo.
echo [*] Verificando dependencias locais...
cd /d "%~dp0"

echo [*] Iniciando servidor do Montanha Media Lab na porta 4190...
start /b "" python server.py 4190

timeout /t 2 /nobreak >nul

echo [*] Abrindo estúdio no Microsoft Edge em modo Desktop App...
start msedge --app=http://localhost:4190 --window-size=1280,820

echo.
echo [✓] Estúdio Desktop ativo em http://localhost:4190
echo [i] Pressione qualquer tecla para minimizar ou fechar esta janela.
echo ========================================================
pause >nul
