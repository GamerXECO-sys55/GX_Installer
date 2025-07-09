#!/usr/bin/env python3
import sys
import os
import glob
import json
import subprocess

FS_TYPES = ["ext4", "btrfs", "f2fs", "xfs"]

def list_disks():
    disks = glob.glob('/dev/sd[a-z]') + glob.glob('/dev/nvme*n1')
    return disks

def list_partitions(disk):
    return [p for p in glob.glob(f"{disk}*") if p != disk]

def get_fs_types():
    return FS_TYPES

def auto_partition(disk, fs_type="ext4", swap_size="2G"):
    try:
        subprocess.run(["wipefs", "-a", disk], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["sgdisk", "-Z", disk], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["sgdisk", "-n", "1:0:+512M", "-t", "1:ef00", disk], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # EFI
        subprocess.run(["sgdisk", "-n", "2:0:0", "-t", "2:8300", disk], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)      # root
        # Format
        subprocess.run(["mkfs.fat", "-F32", f"{disk}1"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if fs_type == "ext4":
            subprocess.run(["mkfs.ext4", f"{disk}2"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif fs_type == "btrfs":
            subprocess.run(["mkfs.btrfs", f"{disk}2"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif fs_type == "f2fs":
            subprocess.run(["mkfs.f2fs", f"{disk}2"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif fs_type == "xfs":
            subprocess.run(["mkfs.xfs", f"{disk}2"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Mount
        subprocess.run(["mount", f"{disk}2", "/mnt"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["mkdir", "-p", "/mnt/boot/efi"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["mount", f"{disk}1", "/mnt/boot/efi"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Swap (optional, simple file)
        if swap_size != "none":
            subprocess.run(["fallocate", "-l", swap_size, "/mnt/swapfile"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["chmod", "600", "/mnt/swapfile"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["mkswap", "/mnt/swapfile"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"status": "success", "message": f"Disk {disk} partitioned and mounted!\nRoot: /mnt ({fs_type})\nEFI: /mnt/boot/efi\nSwap: {swap_size}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def manual_partitions(disk):
    try:
        subprocess.run(["cfdisk", disk], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        parts = list_partitions(disk)
        return {"status": "select", "partitions": parts, "fs_types": FS_TYPES}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def format_and_mount(mounts):
    # mounts: list of dicts: [{"partition": "/dev/sda2", "mountpoint": "/", "fs": "ext4", "format": True}, ...]
    try:
        for m in mounts:
            if m.get("format"):
                if m["fs"] == "ext4":
                    subprocess.run(["mkfs.ext4", m["partition"]], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                elif m["fs"] == "btrfs":
                    subprocess.run(["mkfs.btrfs", m["partition"]], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                elif m["fs"] == "f2fs":
                    subprocess.run(["mkfs.f2fs", m["partition"]], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                elif m["fs"] == "xfs":
                    subprocess.run(["mkfs.xfs", m["partition"]], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                elif m["fs"] == "fat32":
                    subprocess.run(["mkfs.fat", "-F32", m["partition"]], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["mkdir", "-p", f"/mnt{m['mountpoint']}"] , check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            subprocess.run(["mount", m["partition"], f"/mnt{m['mountpoint']}"] , check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return {"status": "success", "message": "All partitions formatted and mounted!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def premounted():
    mounts = []
    if os.path.ismount("/mnt"):
        mounts.append({"mount": "/mnt", "label": "root"})
    if os.path.ismount("/mnt/boot/efi"):
        mounts.append({"mount": "/mnt/boot/efi", "label": "efi"})
    if os.path.ismount("/mnt/boot"):
        mounts.append({"mount": "/mnt/boot", "label": "boot"})
    if mounts:
        return {"status": "success", "mounts": mounts}
    else:
        return {"status": "error", "message": "No pre-mounted partitions found!"}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "No mode specified"}))
        sys.exit(1)
    mode = sys.argv[1]
    try:
        if mode == "list":
            print(json.dumps({"status": "ok", "disks": list_disks()}))
        elif mode == "fs_types":
            print(json.dumps({"status": "ok", "fs_types": get_fs_types()}))
        elif mode == "auto":
            if len(sys.argv) < 3:
                print(json.dumps({"status": "error", "message": "Disk not specified"}))
                sys.exit(1)
            disk = sys.argv[2]
            fs_type = sys.argv[3] if len(sys.argv) > 3 else "ext4"
            swap_size = sys.argv[4] if len(sys.argv) > 4 else "2G"
            print(json.dumps(auto_partition(disk, fs_type, swap_size)))
        elif mode == "manual":
            if len(sys.argv) < 3:
                print(json.dumps({"status": "error", "message": "Disk not specified"}))
                sys.exit(1)
            disk = sys.argv[2]
            print(json.dumps(manual_partitions(disk)))
        elif mode == "format_mount":
            if len(sys.argv) < 3:
                print(json.dumps({"status": "error", "message": "Mount data not specified"}))
                sys.exit(1)
            mounts = json.loads(sys.argv[2])
            print(json.dumps(format_and_mount(mounts)))
        elif mode == "premounted":
            print(json.dumps(premounted()))
        else:
            print(json.dumps({"status": "error", "message": "Unknown mode"}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": f"Backend error: {str(e)}"}))
        sys.exit(1)

if __name__ == "__main__":
    main() 