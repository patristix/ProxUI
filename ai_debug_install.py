#!/usr/bin/env python3

import os
import pwd
import sys
import time
import subprocess
from pathlib import Path

config = {
    "betterDashboard": False,
    "proxuiBackground": True,
    "autorunDE": True,
    "tosSigned": False
}

tos = """
This software is provided as is and as available, without warranties of any kind, express or implied. To the fullest extent permitted by law, the author(s) and contributors disclaim all warranties, including but not limited to implied warranties of merchantability, fitness for a particular purpose, noninfringement, and security.

By using this software, you acknowledge and agree that:

You are solely responsible for installing, configuring, securing, and operating it on your systems.

You assume all risks associated with its use, including but not limited to data loss, system malfunction, downtime, vulnerabilities, and exposure to attacks.

The author(s) and contributors do not warrant that the software is free from defects, vulnerabilities, or security issues, or that it will prevent, mitigate, or respond to any cyberattack, intrusion, or other harmful event.

In no event shall the author(s) or contributors be liable for any claim, loss, or damage of any kind arising out of or in connection with the software or its use, including but not limited to direct, indirect, incidental, consequential, special, exemplary, or punitive damages, whether in an action of contract, tort, or otherwise, even if advised of the possibility of such damages.

If you do not agree with these terms, do not install or use this software. By interacting at all with any code or viewing the main page, you hereby agree to the terms above, and the developer of ProxUI (@user) is waived of all liability and damage to your device.
"""

autoRunDE = """[Desktop Entry]
Type=Application
Version=1.0
Name=ProxUI
Comment=Open Proxmox at 127.0.0.1:8006
Exec=/usr/bin/epiphany-browser http://127.0.0.1:8006
Icon=web-browser
Terminal=false
Categories=Network;WebBrowser;
"""

PROFILE_AUTORUN_BLOCK = r'''
# ProxUI autorun once per graphical login
if [ -n "$DISPLAY$WAYLAND_DISPLAY" ]; then
    BOOT_ID="$(cat /proc/sys/kernel/random/boot_id 2>/dev/null)"
    SESSION_TAG="${XDG_SESSION_ID:-${DISPLAY:-wayland}}"
    PROXUI_SENTINEL="/tmp/.proxui-autostart-${USER}-${BOOT_ID}-${SESSION_TAG}"

    if [ ! -e "$PROXUI_SENTINEL" ]; then
        : > "$PROXUI_SENTINEL"
        if [ -x "$HOME/Desktop/pmui.desktop" ]; then
            nohup "$HOME/Desktop/pmui.desktop" >/dev/null 2>&1 &
        fi
    fi
fi
'''

def run_cmd(cmd, check=True, fatal=True):
    print(f"[*] Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            text=True,
            capture_output=True
        )

        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print(result.stderr.strip())

        return result

    except subprocess.CalledProcessError as e:
        print(f"[-] Command failed with exit code {e.returncode}: {' '.join(cmd)}")
        if e.stdout:
            print("[stdout]")
            print(e.stdout.strip())
        if e.stderr:
            print("[stderr]")
            print(e.stderr.strip())
        if fatal:
            sys.exit(e.returncode)
        return None

    except FileNotFoundError:
        print(f"[-] Command not found: {cmd[0]}")
        if fatal:
            sys.exit(1)
        return None

    except Exception as e:
        print(f"[-] Unexpected error while running {' '.join(cmd)}: {e}")
        if fatal:
            sys.exit(1)
        return None

def logo():
    print("-Welcome to ProxUI Installer v:0.0.1-\nMade with <3 -user 2026")
    if os.geteuid() != 0:
        input("Be sure to run program with sudo or root. Press Enter to exit...")
        sys.exit(1)

def get_target_user():
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        return sudo_user
    return pwd.getpwuid(os.getuid()).pw_name

def get_home(username: str) -> Path:
    return Path(pwd.getpwnam(username).pw_dir)

def ensure_proxui_dir():
    print("[*] Creating ProxUI folder (/etc/proxui)...")
    os.makedirs("/etc/proxui", exist_ok=True)
    print("[+] ProxUI folder ready (/etc/proxui)!")

def write_tos_signature():
    print("[*] Creating/overwriting current TOS signature file (/etc/proxui/tos.txt)...")
    with open("/etc/proxui/tos.txt", "w", encoding="utf-8") as o:
        o.write(tos + "\n\nsigned=true\n")
    print("[+] Created/overwrote TOS signature file (/etc/proxui/tos.txt)!")

def create_desktop_launcher(username: str):
    home = get_home(username)
    desktop_dir = home / "Desktop"
    desktop_dir.mkdir(parents=True, exist_ok=True)

    desktop_file = desktop_dir / "pmui.desktop"
    desktop_file.write_text(autoRunDE, encoding="utf-8")
    os.chmod(desktop_file, 0o755)

    try:
        user_info = pwd.getpwnam(username)
        os.chown(desktop_file, user_info.pw_uid, user_info.pw_gid)
    except PermissionError:
        pass

    print(f"[+] Created desktop launcher: {desktop_file}")

def ensure_profile_autorun(username: str):
    home = get_home(username)
    profile = home / ".profile"

    existing = profile.read_text(encoding="utf-8") if profile.exists() else ""
    if "PROXUI_SENTINEL" not in existing:
        with profile.open("a", encoding="utf-8") as f:
            f.write("\n" + PROFILE_AUTORUN_BLOCK + "\n")
        print(f"[+] Added ProxUI autorun block to {profile}")
    else:
        print(f"[!] ProxUI autorun block already exists in {profile}, skipping")

    try:
        user_info = pwd.getpwnam(username)
        os.chown(profile, user_info.pw_uid, user_info.pw_gid)
    except PermissionError:
        pass

def main():
    logo()
    time.sleep(1)

    os.system("clear")
    logo()
    print(tos)
    tosSign = input("\nAccept TOS? (Read this page CAREFULLY!) (y/n): ").strip().lower()

    if tosSign == "y":
        config["tosSigned"] = True
        print("[+] TOS signed")
    else:
        input("[-] Invalid entry/rejected TOS. Exiting...")
        sys.exit(1)

    if not config["tosSigned"]:
        input("[-] Invalid entry/rejected TOS. Exiting...")
        sys.exit(1)

    ensure_proxui_dir()
    write_tos_signature()

    os.system("clear")
    logo()

    autoRun = input("Auto-run Desktop Env.? default 'true' (y/n): ").strip().lower()
    if autoRun in ("", "y"):
        config["autorunDE"] = True
    elif autoRun == "n":
        config["autorunDE"] = False
    else:
        print("[!] Invalid input, using default: true")
        config["autorunDE"] = True

    input("Ready for install? Press Enter/Return, if not, Ctrl+C")

    run_cmd(["apt", "update"])
    run_cmd(["apt", "upgrade", "-y"])
    run_cmd([
        "apt", "install", "-y", "--no-install-recommends",
        "xorg", "lxde", "epiphany-browser"
    ])

    if config["autorunDE"]:
        run_cmd(["systemctl", "set-default", "graphical.target"])
        username = get_target_user()
        create_desktop_launcher(username)
        ensure_profile_autorun(username)

    reboot = input("Installation complete. Reboot to make changes? (y/n): ").strip().lower()
    if reboot == "y":
        run_cmd(["reboot", "now"], check=False, fatal=False)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
