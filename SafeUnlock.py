
# -*- coding: utf-8 -*-

import os
import sys
import ctypes
import subprocess
import time
import shutil
from pathlib import Path
from datetime import datetime

APP_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)

AUDIO = APP_DIR / "gleb.mp3"

BACKUP = (
    Path.home()
    / "Desktop"
    / "ToolBackups"
    / datetime.now().strftime("%Y%m%d_%H%M%S")
)


# ==========================================
# ADMINISTRATOR
# ==========================================

def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def elevate():
    params = subprocess.list2cmdline(sys.argv)

    result = ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        params,
        str(APP_DIR),
        1
    )

    if result <= 32:
        print("[!] Не удалось получить права администратора.")
        input("Enter...")
        sys.exit(1)

    sys.exit(0)


# ==========================================
# COMMANDS
# ==========================================

def run(args, capture=True):
    try:
        result = subprocess.run(
            args,
            text=True,
            errors="replace",
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.STDOUT if capture else None,
            check=False
        )

        if capture and result.stdout:
            print(result.stdout)

        if result.returncode != 0:
            print(f"[!] Код завершения: {result.returncode}")

        return result.returncode

    except (OSError, ValueError) as error:
        print(f"[!] Ошибка: {error}")
        return -1


def cmd_shell(command):
    return run(["cmd.exe", "/d", "/c", command])


def confirm(message):
    return input(f"{message} (y/n): ").strip().lower() == "y"


def pause():
    input("\nНажми Enter для продолжения...")


# ==========================================
# SOUND
# ==========================================

def play_sound():
    if not AUDIO.is_file():
        print("[!] gleb.mp3 не найден!")
        return

    try:
        import pygame

        pygame.mixer.init()
        pygame.mixer.music.load(str(AUDIO))
        pygame.mixer.music.play()

        print("[OK] Звук запущен.")

    except Exception as error:
        print(f"[!] Ошибка звука: {error}")


# ==========================================
# BACKUPS
# ==========================================

def create_backup():
    BACKUP.mkdir(parents=True, exist_ok=True)


def open_backups():
    folder = BACKUP.parent
    folder.mkdir(parents=True, exist_ok=True)
    os.startfile(str(folder))


# ==========================================
# TASK MANAGER
# ==========================================

def taskmgr():
    print("Снимаю ограничения Диспетчера задач...")

    for hive in ("HKCU", "HKLM"):
        run([
            "reg", "delete",
            fr"{hive}\Software\Microsoft\Windows\CurrentVersion\Policies\System",
            "/v", "DisableTaskMgr", "/f"
        ])

    subprocess.Popen(["taskmgr.exe"])


# ==========================================
# REGISTRY EDITOR
# ==========================================

def regedit():
    print("Снимаю ограничения редактора реестра...")

    for hive in ("HKCU", "HKLM"):
        run([
            "reg", "delete",
            fr"{hive}\Software\Microsoft\Windows\CurrentVersion\Policies\System",
            "/v", "DisableRegistryTools", "/f"
        ])

    subprocess.Popen(["regedit.exe"])


# ==========================================
# SERVICES
# ==========================================

def services():
    subprocess.Popen(["services.msc"])


# ==========================================
# STARTUP
# ==========================================

def startup():
    keys = [
        r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run"
    ]

    for key in keys:
        print(f"\n=== {key} ===")
        run(["reg", "query", key])

    folder = (
        Path(os.environ["APPDATA"])
        / "Microsoft/Windows/Start Menu/Programs/Startup"
    )

    print("\n=== Startup ===")

    if folder.exists():
        for item in folder.iterdir():
            print(item.name)


# ==========================================
# GROUP POLICIES
# ==========================================

def gpupdate():
    print("Обновление групповых политик Windows.")

    if confirm("Продолжить?"):
        run(["gpupdate", "/force"])


# ==========================================
# FILE ASSOCIATIONS
# ==========================================

def associations():
    create_backup()

    for command, filename in [
        ("assoc", "assoc_before.txt"),
        ("ftype", "ftype_before.txt")
    ]:
        result = subprocess.run(
            ["cmd.exe", "/d", "/c", command],
            capture_output=True,
            text=True,
            errors="replace"
        )

        (BACKUP / filename).write_text(
            result.stdout,
            encoding="utf-8"
        )

    print("[OK] Резервные копии созданы.")

    if not confirm("Восстановить ассоциации BAT/CMD/REG/TXT?"):
        return

    associations_map = {
        ".bat": "batfile",
        ".cmd": "cmdfile",
        ".reg": "regfile",
        ".txt": "txtfile"
    }

    for extension, filetype in associations_map.items():
        cmd_shell(f"assoc {extension}={filetype}")

    filetypes = [
        'ftype batfile="%1" %*',
        'ftype cmdfile="%1" %*',
        'ftype regfile=regedit.exe "%1"',
        'ftype txtfile=notepad.exe "%1"'
    ]

    for item in filetypes:
        cmd_shell(item)

    print("[OK] Ассоциации обработаны.")
    print("[!] EXE-ассоциации не изменялись.")


# ==========================================
# UNLOCK FILE / FOLDER
# ==========================================

def unlock():
    raw = input("Путь к файлу или папке: ").strip().strip('"')

    if not raw:
        return

    target = Path(raw)

    if not target.exists():
        print("[!] Объект не найден.")
        return

    username = os.environ.get("USERNAME")

    if not username:
        print("[!] Пользователь не определён.")
        return

    print("[!] Изменение прав доступа может повлиять на других пользователей.")

    if not confirm(f"Изменить права для {target}?"):
        return

    run(["takeown", "/f", str(target), "/r", "/d", "Y"])

    permissions = (
        f"{username}:(OI)(CI)F"
        if target.is_dir()
        else f"{username}:F"
    )

    args = ["icacls", str(target), "/grant", permissions]

    if target.is_dir():
        args.extend(["/t", "/c"])

    run(args)


# ==========================================
# KILL PROCESS
# ==========================================

def kill():
    name = input("Имя процесса (например, notepad.exe): ").strip()

    if not name:
        return

    if Path(name).name != name or "/" in name or "\\" in name:
        print("[!] Введите только имя процесса.")
        return

    if confirm(f"Завершить {name}? Несохранённые данные могут потеряться."):
        run(["taskkill", "/f", "/im", name])


# ==========================================
# RESTART EXPLORER
# ==========================================

def explorer():
    run(["taskkill", "/f", "/im", "explorer.exe"])
    time.sleep(2)
    subprocess.Popen(["explorer.exe"])


# ==========================================
# SCAN LIMITATIONS
# ==========================================

def scan():
    checks = [
        (
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System",
            "DisableTaskMgr",
            "Диспетчер задач"
        ),
        (
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\System",
            "DisableRegistryTools",
            "Редактор реестра"
        ),
        (
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer",
            "NoFolderOptions",
            "Параметры папок"
        ),
        (
            r"HKCU\Software\Microsoft\Windows\CurrentVersion\Policies\Explorer",
            "NoRun",
            "Команда Выполнить"
        )
    ]

    for key, value, label in checks:
        result = subprocess.run(
            ["reg", "query", key, "/v", value],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        print(f"[{'!' if result.returncode == 0 else 'OK'}] {label}")

    print("\n=== Процессы из пользовательских папок ===")

    powershell = (
        "Get-Process | "
        "Where-Object { $_.Path -match '\\\\Temp\\\\|\\\\AppData\\\\|\\\\Public\\\\' } | "
        "Select-Object Name,Path | Format-Table -AutoSize"
    )

    run([
        "powershell.exe",
        "-NoProfile",
        "-Command",
        powershell
    ])


# ==========================================
# NETWORK RESET
# ==========================================

def network():
    if not confirm("Сбросить сетевые настройки?"):
        return

    run(["ipconfig", "/flushdns"])
    run(["ipconfig", "/release"])
    run(["ipconfig", "/renew"])
    run(["netsh", "winsock", "reset"])

    print("[!] Рекомендуется перезагрузка.")


# ==========================================
# HOSTS BACKUP
# ==========================================

def hosts():
    path = (
        Path(os.environ["WINDIR"])
        / "System32/drivers/etc/hosts"
    )

    create_backup()

    if not path.exists():
        print("[!] Hosts не найден.")
        return

    backup_file = BACKUP / "hosts_backup.txt"

    shutil.copy2(path, backup_file)

    print(f"[OK] Резервная копия: {backup_file}")

    if not confirm("Очистить hosts?"):
        return

    run(["attrib", "-r", str(path)])

    path.write_text(
        "# Hosts file reset by SafeUnlock\n",
        encoding="ascii"
    )

    print("[OK] Hosts очищен.")


# ==========================================
# SERVICES CONTROL
# ==========================================

def disable_services():
    print("RemoteRegistry и Telnet.")

    if not confirm("Отключить эти службы?"):
        return

    for service in ("RemoteRegistry", "TlntSvr"):
        run(["sc", "stop", service])
        run(["sc", "config", service, "start=", "disabled"])


# ==========================================
# SHOW HIDDEN FILES
# ==========================================

def hidden():
    key = (
        r"HKCU\Software\Microsoft\Windows\CurrentVersion"
        r"\Explorer\Advanced"
    )

    run([
        "reg", "add", key,
        "/v", "Hidden",
        "/t", "REG_DWORD",
        "/d", "1", "/f"
    ])

    run([
        "reg", "add", key,
        "/v", "ShowSuperHidden",
        "/t", "REG_DWORD",
        "/d", "1", "/f"
    ])

    print("[OK] Скрытые файлы отображаются.")


# ==========================================
# ICON CACHE
# ==========================================

def icons():
    run(["taskkill", "/f", "/im", "explorer.exe"])
    time.sleep(2)

    folder = (
        Path(os.environ["LOCALAPPDATA"])
        / "Microsoft/Windows/Explorer"
    )

    for item in folder.glob("iconcache*"):
        try:
            if item.is_file():
                item.unlink()
        except OSError as error:
            print(f"[!] {error}")

    subprocess.Popen(["explorer.exe"])


# ==========================================
# SYSTEM CHECK
# ==========================================

def system_check():
    if not confirm("Запустить DISM и SFC?"):
        return

    run([
        "DISM",
        "/Online",
        "/Cleanup-Image",
        "/RestoreHealth"
    ], capture=False)

    run(["sfc", "/scannow"], capture=False)


# ==========================================
# TEMP CLEANER
# ==========================================

def temp():
    folder = Path(os.environ.get("TEMP", ""))

    if not folder.is_dir():
        print("[!] TEMP не найден.")
        return

    if not confirm(f"Очистить {folder}?"):
        return

    removed = 0

    for item in folder.iterdir():
        try:
            if item.is_symlink() or item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

            removed += 1

        except OSError:
            print(f"[!] Пропущено: {item.name}")

    print(f"[OK] Обработано объектов: {removed}")


# ==========================================
# OPEN PORTS
# ==========================================

def ports():
    run(["netstat", "-ano"])


# ==========================================
# REBOOT
# ==========================================

def reboot():
    if confirm("Перезагрузить компьютер через 10 секунд?"):
        run([
            "shutdown",
            "/r",
            "/t", "10",
            "/c", "Перезагрузка по запросу пользователя"
        ])


# ==========================================
# MENU
# ==========================================

MENU = {
    "1": ("Диспетчер задач", taskmgr),
    "2": ("Редактор реестра", regedit),
    "3": ("Управление службами", services),
    "4": ("Автозагрузка", startup),
    "5": ("Обновление групповых политик", gpupdate),
    "6": ("Ассоциации файлов", associations),
    "7": ("Разблокировка файла/папки", unlock),
    "8": ("Завершение процесса", kill),
    "9": ("Перезапуск Explorer", explorer),
    "10": ("Скан ограничений", scan),
    "11": ("Сброс сети", network),
    "12": ("Очистка hosts", hosts),
    "13": ("Управление службами", disable_services),
    "14": ("Показать скрытые файлы", hidden),
    "15": ("Сброс кэша иконок", icons),
    "16": ("Проверка Windows", system_check),
    "17": ("Открыть резервные копии", open_backups),
    "18": ("Очистка Temp", temp),
    "19": ("Сетевые подключения и порты", ports),
    "20": ("Перезагрузка ПК", reboot)
}


# ==========================================
# MAIN
# ==========================================

def main():

    if os.name != "nt":
        print("SafeUnlock предназначен только для Windows.")
        return

    if not is_admin():
        print("[*] Запрашиваю права администратора...")
        elevate()

    create_backup()

    # Запуск звука при каждом запуске программы
    play_sound()

    while True:

        os.system("cls")

        print("=" * 60)
        print("          LITE @aqDiamonds — SafeUnlock")
        print("=" * 60)

        for number, (label, _) in MENU.items():
            print(f"{number:>2}. {label}")

        print(" 0. Выход")
        print("=" * 60)

        choice = input("Выбор: ").strip()

        if choice == "0":
            break

        action = MENU.get(choice)

        if action:
            os.system("cls")

            try:
                action[1]()
            except Exception as error:
                print(f"[!] Ошибка: {error}")

            pause()


if __name__ == "__main__":
    main()
