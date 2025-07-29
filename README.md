# 🛠️ **GamerX Installer**

---

## 🚀 **The Next-Gen Arch Linux Installer**

**GamerX Installer** is a modern, fully-automated, and user-friendly installer for GamerX Linux, built to make Arch-based installations fast, reliable, and effortless for everyone—gamers, hackers, creators, and power users!

---

## ✨ **Key Features**

- **⚡ Fully Automated:**
  - Handles disk partitioning, user creation, locales, kernel, profiles, and more—all from a beautiful TUI.
  - No manual config editing or terminal wizardry required!

- **🖥️ Modern TUI Experience:**
  - Built with [Textual](https://github.com/Textualize/textual) and [Rich](https://github.com/Textualize/rich) for a visually appealing and interactive interface.
  - Easy navigation with keyboard, clear prompts, and real-time feedback.

- **🎮 Profile-Based Installs:**
  - Choose from Gaming, Hacking, Hyprland, or hybrid profiles.
  - Each profile includes curated packages, themes, and post-install scripts.

- **🔄 Rolling Updates:**
  - Always fetches the latest installer version and scripts from the repo.

- **🛡️ Robust Error Handling:**
  - Comprehensive logging, clear error messages, and safe rollback on failure.

- **🔧 Customization:**
  - Select kernel, swap, timezone, user, and more.
  - Advanced users can add extra packages or tweak install scripts.

---

## 🧩 **How It Works**

1. **Launch the Installer**
   - Runs as a Python script (`gxinstall`) on the live ISO.
2. **Interactive Setup**
   - Guides you through disk setup, user, locale, kernel, and profile selection.
3. **Automated Installation**
   - Installs base system and all selected packages.
   - Copies all necessary scripts and profiles into the target system.
   - Generates and runs a post-install chroot script for final tweaks.
4. **Profile Customization**
   - Applies custom themes, settings, and installs GX Apps as needed.
5. **Finish & Reboot**
   - Provides a summary, logs, and easy chroot access for troubleshooting or final tweaks.

---

## 📦 **Repo Structure**

- `gxinstall` — Main Python TUI installer
- `gx_disk.py` — Disk/partition helper backend
- `profiles/` — Profile scripts and package lists (Gaming, Hacking, Hyprland)
- `Installer/` — Profile install scripts for chroot
- `VERSION` — Installer version
- `gxinstall-repo-structure.txt` — Repo layout overview

---

## 📝 **Developer & Contact Info**

- **GitHub:** [GamerXECO-sys55](https://github.com/GamerXECO-sys55)
- **Email:** mangeshchoudhary35@gmail.com
- **Lead Developer:** Mangesh Choudhary

---

## 💡 **Why Use GamerX Installer?**

- No more manual installs—get a fully working system in minutes.
- Beautiful, modern interface with robust automation.
- Designed for both new users and power users.
- Actively maintained and open source!

---

## 🚦 **Getting Started**

1. Boot into the GamerX Linux live ISO.
2. Run `gxinstall` in the terminal.
3. Follow the on-screen prompts and enjoy the ride!

---

## 🤝 **Contributions & Feedback**

Pull requests, bug reports, and feature suggestions are welcome! Help us make the best Linux installer for everyone.
