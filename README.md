# GX Installer Repo

This folder contains all scripts, helpers, and files for the GamerX Linux installer. 

- **gxinstall**: Main installer (Python TUI)
- **gx_disk.py**: Disk helper backend
- **tmp/installer.sh**: Chroot/post-install script
- **profiles/**: Each profile (Gaming, Hacking, Hyprland) has its own install.sh and package list
- **Installer/**: Legacy/extra profile install scripts
- **VERSION**: Current installer version (increment with every update)
- **gxinstall-repo-structure.txt**: Overview of the repo layout

## Update Workflow
- Edit files in this folder, increment VERSION, and push to GitHub.
- On live system, run the update script to fetch the latest installer files.
