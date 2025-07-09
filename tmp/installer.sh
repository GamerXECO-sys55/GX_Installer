#!/bin/bash
set -euo pipefail

# Read username, password, sudo, disk, and profile from config file
envfile="/tmp/userinfo.conf"
if [[ ! -f "$envfile" ]]; then
    echo "ERROR: $envfile not found!"
    exit 1
fi
USERNAME=$(grep '^USERNAME=' "$envfile" | cut -d= -f2-)
USERPASS=$(grep '^USERPASS=' "$envfile" | cut -d= -f2-)
USERSUDO=$(grep '^USERSUDO=' "$envfile" | cut -d= -f2-)
DISK=$(grep '^DISK=' "$envfile" | cut -d= -f2-)
PROFILE=$(grep '^PROFILE=' "$envfile" | cut -d= -f2-)

if [[ -z "$USERNAME" || -z "$USERPASS" ]]; then
    echo "ERROR: USERNAME or USERPASS not set in $envfile"
    exit 1
fi
if [[ -z "$DISK" ]]; then
    DISK="/dev/sda"
    echo "[WARNING] DISK not set in $envfile, defaulting to /dev/sda"
fi
if [[ -z "$PROFILE" ]]; then
    PROFILE="GamerX Hyprland"
    echo "[WARNING] PROFILE not set in $envfile, defaulting to GamerX Hyprland"
fi

# 1. System config (locale, timezone, etc.)
# (Add your system config steps here if needed)

# 2. User creation
if ! id "$USERNAME" &>/dev/null; then
    useradd -m -G wheel -s /bin/bash "$USERNAME"
    echo "$USERNAME:$USERPASS" | chpasswd
    if [[ "$USERSUDO" == "yes" ]]; then
        sed -i 's/^# %wheel ALL=(ALL:ALL) ALL/%wheel ALL=(ALL:ALL) ALL/' /etc/sudoers
    fi
fi

# 3. yay install (as user)
pacman -S --needed --noconfirm git base-devel
cd /tmp && git clone https://aur.archlinux.org/yay.git
chown -R "$USERNAME:$USERNAME" /tmp/yay
su - "$USERNAME" -c "cd /tmp/yay && makepkg -si --noconfirm"

# 4. GRUB and SDDM setup (dynamic for UEFI/BIOS, GPT/MBR)
if [ -d /sys/firmware/efi ]; then
    echo "[INFO] UEFI system detected."
    grub-install --target=x86_64-efi --efi-directory=/boot --bootloader-id=GRUB
else
    echo "[INFO] BIOS/Legacy system detected."
    if parted -s "$DISK" print | grep -q 'gpt'; then
        echo "[INFO] GPT partition table detected."
        grub-install --target=i386-pc --boot-directory=/boot "$DISK"
    else
        echo "[INFO] MBR partition table detected."
        grub-install --target=i386-pc --boot-directory=/boot "$DISK"
    fi
fi
grub-mkconfig -o /boot/grub/grub.cfg
systemctl enable sddm

# 5. HyDE theme install (as user)
su - "$USERNAME" <<'EOF'
set -euo pipefail
cd ~
if [ ! -d "HyDE" ]; then
    git clone https://github.com/GamerXECO-sys55/Hyprland_GX_theme ~/HyDE
fi
if [ -f "HyDE/install.sh" ]; then
    cd HyDE
    chmod +x install.sh
    ./install.sh --non-interactive || echo "HyDE install failed, check logs"
fi
EOF

# 6. Profile installer (run correct script based on PROFILE)
case "$PROFILE" in
    "GamerX Hyprland")
        /usr/local/bin/Installer/install_hyprland.sh
        ;;
    "GamerX Hyprland+Gaming")
        /usr/local/bin/Installer/install_gaming.sh
        ;;
    "GamerX Hyprland+Hacking")
        /usr/local/bin/Installer/install_hacking.sh
        ;;
    *)
        echo "[WARNING] Unknown profile: $PROFILE"
        ;;
esac

# 7. Clean up
rm -rf /tmp/yay
rm -f /tmp/installer.sh /tmp/userinfo.conf

echo "INSTALLATION COMPLETE" 