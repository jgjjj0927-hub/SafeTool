@echo off
chcp 65001 >nul
title Аварийный Инструмент v2.1
color 0A
setlocal enabledelayedexpansion

:: --- ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Требуются права администратора. Запрос...
    powershell -NoProfile -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: --- ПОДГОТОВКА ПАПКИ БЭКАПОВ ---
for /f %%a in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "DT=%%a"
set "BK=%USERPROFILE%\Desktop\ToolBackups\%DT%"
if not exist "%BK%" mkdir "%BK%"

:menu
cls
echo  ============================================================
echo                 LITE @aqDiamonds
echo  ============================================================
echo   1.  Открыть Диспетчер задач (снять запрет)
echo   2.  Открыть Редактор реестра (снять запрет)
echo   3.  Открыть Управление службами
echo   4.  Показать автозагрузку (Реестр + Папка)
echo   5.  Сбросить групповые политики (gpupdate)
echo   6.  Восстановить ассоциации файлов (.exe, .bat)
echo   7.  Разблокировать файл/папку (takeown + icacls)
echo   8.  Убить процесс по имени
echo   9.  Перезапустить Explorer (оживить панель)
echo  10.  Быстрый скан ограничений и вирусов
echo  11.  Сбросить настройки сети (ipconfig /flushdns)
echo  12.  Очистить hosts-файл (от вирусов)
echo  13.  Отключить подозрительные службы
echo  14.  Показать скрытые файлы (снять запрет)
echo  15.  Сбросить кэш иконок и миниатюр
echo  16.  Проверить систему на вирусы (SFC + DISM)
echo  17.  Открыть папку бэкапов
echo  18.  Очистить временные файлы (Temp)
echo  19.  Показать открытые порты (netstat)
echo  20.  Перезагрузка ПК
echo   0.  Выход
echo  ============================================================
set /p c=Выбор: 

if "%c%"=="0" exit
if "%c%"=="1" goto tsk
if "%c%"=="2" goto regedit
if "%c%"=="3" goto svc
if "%c%"=="4" goto startup
if "%c%"=="5" goto gpupdate
if "%c%"=="6" goto assoc
if "%c%"=="7" goto unlock_file
if "%c%"=="8" goto kill_proc
if "%c%"=="9" goto restart_exp
if "%c%"=="10" goto scan_limits
if "%c%"=="11" goto reset_net
if "%c%"=="12" goto clear_hosts
if "%c%"=="13" goto disable_services
if "%c%"=="14" goto show_hidden
if "%c%"=="15" goto clear_icons
if "%c%"=="16" goto sfc_scan
if "%c%"=="17" (start "" "%USERPROFILE%\Desktop\ToolBackups" & goto menu)
if "%c%"=="18" goto clear_temp
if "%c%"=="19" goto open_ports
if "%c%"=="20" goto reboot
goto menu

:: ============================================================
:: 1. ДИСПЕТЧЕР ЗАДАЧ
:: ============================================================
:tsk
cls
echo  Снимаю запреты с Диспетчера задач...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v DisableTaskMgr /f >nul 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v DisableTaskMgr /f >nul 2>&1
start taskmgr
echo  Готово.
pause
goto menu

:: ============================================================
:: 2. РЕДАКТОР РЕЕСТРА
:: ============================================================
:regedit
cls
echo  Снимаю запреты с Редактора реестра...
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v DisableRegistryTools /f >nul 2>&1
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Policies\System" /v DisableRegistryTools /f >nul 2>&1
start regedit
echo  Готово.
pause
goto menu

:: ============================================================
:: 3. СЛУЖБЫ
:: ============================================================
:svc
start services.msc
goto menu

:: ============================================================
:: 4. АВТОЗАГРУЗКА
:: ============================================================
:startup
cls
echo  === HKCU Run ===
reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" 2>nul
echo.
echo  === HKLM Run ===
reg query "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" 2>nul
echo.
echo  === Папка Startup ===
dir "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup" /b 2>nul
pause
goto menu

:: ============================================================
:: 5. ГРУППОВЫЕ ПОЛИТИКИ
:: ============================================================
:gpupdate
cls
echo  Обновление групповых политик...
gpupdate /force
echo.
echo  [!] ВНИМАНИЕ: сброс локальных политик безопасности (secedit).
set /p confirm=Продолжить? (y/n): 
if /i not "%confirm%"=="y" goto menu
secedit /configure /cfg %windir%\inf\defltbase.inf /db defltbase.sdb /verbose >nul 2>&1
echo  Готово.
pause
goto menu

:: ============================================================
:: 6. АССОЦИАЦИИ ФАЙЛОВ
:: ============================================================
:assoc
cls
echo  Восстановление ассоциаций...
assoc > "%BK%\assoc_before.txt" 2>nul

:: Удаляем UserChoice ТОЛЬКО для .bat, .cmd, .reg, .txt (не для .exe!)
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.bat\UserChoice" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.cmd\UserChoice" /f >nul 2>&1
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.reg\UserChoice" /f >nul 2>&1

:: Восстанавливаем базовые ассоциации
assoc .exe=exefile >nul 2>&1
assoc .bat=batfile >nul 2>&1
assoc .cmd=cmdfile >nul 2>&1
assoc .reg=regfile >nul 2>&1
assoc .txt=txtfile >nul 2>&1

:: Правильный ftype
ftype exefile="%1" %*
ftype batfile="%1" %*
ftype cmdfile="%1" %*
ftype regfile=regedit.exe "%1"
ftype txtfile=notepad.exe "%1"

echo  Готово. Если .exe не работает — перезагрузись.
pause
goto menu

:: ============================================================
:: 7. РАЗБЛОКИРОВКА ФАЙЛА
:: ============================================================
:unlock_file
cls
echo  Перетащи файл/папку сюда или вставь путь.
set /p "target=Путь: "
if "%target%"=="" goto menu
set "target=%target:"=%"
if not exist "%target%" (
    echo [!] Не найдено: %target%
    pause
    goto menu
)
takeown /f "%target%" /r /d y >nul 2>&1
icacls "%target%" /grant "%USERNAME%":F /t /c /q >nul 2>&1
echo  Готово.
pause
goto menu

:: ============================================================
:: 8. УБИТЬ ПРОЦЕСС
:: ============================================================
:kill_proc
cls
set /p pname=Имя процесса (например, notepad.exe): 
if "%pname%"=="" goto menu
taskkill /f /im "%pname%" 2>nul
if errorlevel 1 (echo [!] Не удалось убить.) else (echo [OK] Убит.)
pause
goto menu

:: ============================================================
:: 9. ПЕРЕЗАПУСК EXPLORER
:: ============================================================
:restart_exp
cls
taskkill /f /im explorer.exe >nul 2>&1
timeout /t 2 /nobreak >nul
start explorer.exe
echo  Explorer перезапущен.
pause
goto menu

:: ============================================================
:: 10. СКАН ОГРАНИЧЕНИЙ
:: ============================================================
:scan_limits
cls
echo  === ПРОВЕРКА ОГРАНИЧЕНИЙ ===
call :check_reg "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" "DisableTaskMgr" "Диспетчер запрещён"
call :check_reg "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System" "DisableRegistryTools" "Реестр запрещён"
call :check_reg "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" "NoFolderOptions" "Опции папок скрыты"
call :check_reg "HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer" "NoRun" "«Выполнить» запрещён"

echo.
echo  === ПРОЦЕССЫ ИЗ TEMP/APPDATA ===
powershell -NoProfile -Command "Get-Process | Where-Object { $_.Path -match '\\Temp\\|\\AppData\\|\\Public\\' } | Select-Object Name,Path | Format-List" 2>nul
pause
goto menu

:: ============================================================
:: 11. СБРОС СЕТИ
:: ============================================================
:reset_net
cls
echo  Сброс сетевых настроек...
ipconfig /flushdns
ipconfig /release >nul 2>&1
ipconfig /renew >nul 2>&1
netsh winsock reset >nul 2>&1
echo  Готово. Рекомендуется перезагрузка.
pause
goto menu

:: ============================================================
:: 12. ОЧИСТКА HOSTS
:: ============================================================
:clear_hosts
cls
echo  Бэкап и очистка файла hosts...
copy "%windir%\System32\drivers\etc\hosts" "%BK%\hosts_backup.txt" >nul 2>&1
echo # Cleaned by Tool > "%windir%\System32\drivers\etc\hosts"
echo  Готово.
pause
goto menu

:: ============================================================
:: 13. ОТКЛЮЧИТЬ ПОДОЗРИТЕЛЬНЫЕ СЛУЖБЫ
:: ============================================================
:disable_services
cls
echo  Отключаю службы, которые часто используют вирусы...
sc query RemoteRegistry | find "RUNNING" >nul && (
    sc stop RemoteRegistry >nul 2>&1
    sc config RemoteRegistry start= disabled >nul 2>&1
    echo  RemoteRegistry отключена.
) || (
    sc config RemoteRegistry start= disabled >nul 2>&1
    echo  RemoteRegistry уже остановлена (установлен запрет запуска).
)

sc query TlntSvr | find "RUNNING" >nul && (
    sc stop TlntSvr >nul 2>&1
    sc config TlntSvr start= disabled >nul 2>&1
    echo  Telnet отключена.
) || (
    sc config TlntSvr start= disabled >nul 2>&1
    echo  Telnet уже остановлена (установлен запрет запуска).
)
pause
goto menu

:: ============================================================
:: 14. ПОКАЗАТЬ СКРЫТЫЕ ФАЙЛЫ
:: ============================================================
:show_hidden
cls
echo  Включаю отображение скрытых файлов...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v Hidden /t REG_DWORD /d 1 /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced" /v ShowSuperHidden /t REG_DWORD /d 1 /f >nul 2>&1
echo  Готово. Перезапусти Explorer (пункт 9).
pause
goto menu

:: ============================================================
:: 15. СБРОС КЭША ИКОНОК
:: ============================================================
:clear_icons
cls
echo  Очистка кэша иконок...
taskkill /f /im explorer.exe >nul 2>&1
timeout /t 2 /nobreak >nul
del /f /s /q "%LocalAppData%\IconCache.db" >nul 2>&1
del /f /s /q "%LocalAppData%\Microsoft\Windows\Explorer\iconcache*" >nul 2>&1
start explorer.exe
echo  Готово.
pause
goto menu

:: ============================================================
:: 16. SFC + DISM
:: ============================================================
:sfc_scan
cls
echo  Проверка системных файлов (SFC) и образа (DISM)...
echo  Это может занять 10-20 минут.
sfc /scannow
DISM /Online /Cleanup-Image /RestoreHealth
pause
goto menu

:: ============================================================
:: 17. ОЧИСТКА TEMP
:: ============================================================
:clear_temp
cls
echo  Очистка временных файлов...
if defined TEMP (
    del /q /f /s "%TEMP%\*" >nul 2>&1
    echo  Очищено: %TEMP%
) else (
    echo  [!] Переменная TEMP не задана, пропускаю.
)
if defined windir (
    del /q /f /s "%windir%\Temp\*" >nul 2>&1
    echo  Очищено: %windir%\Temp
) else (
    echo  [!] Переменная windir не задана, пропускаю.
)
pause
goto menu

:: ============================================================
:: 18. ОТКРЫТЫЕ ПОРТЫ
:: ============================================================
:open_ports
cls
echo  Активные подключения и открытые порты...
netstat -ano | findstr "LISTENING"
pause
goto menu

:: ============================================================
:: 19. ПЕРЕЗАГРУЗКА
:: ============================================================
:reboot
cls
set /p confirm=Точно перезагрузить? (y/n): 
if /i "%confirm%"=="y" shutdown /r /t 5 /c "Перезагрузка через 5 сек..."
goto menu

:: ============================================================
:: ФУНКЦИЯ ПРОВЕРКИ РЕЕСТРА
:: ============================================================
:check_reg
reg query "%~1" /v "%~2" >nul 2>&1
if %errorlevel% equ 0 (
    echo [!] %~3
) else (
    echo [OK] %~3 — нет
)
goto :eof
