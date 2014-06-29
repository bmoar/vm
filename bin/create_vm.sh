#!/bin/bash
set -eu
set -o pipefail

# --------------------------------
# bin
# --------------------------------

VIRSH="/usr/bin/virsh"
CP="/bin/cp"
KPARTX="/sbin/kpartx"
SED="/bin/sed"
SUDO="/usr/bin/sudo"
MOUNT="/bin/mount"
UMOUNT="/bin/umount"

set +eu
hostname=$1
xml_template_path=$2
set -eu

domain="debian_jessie_base"

img_src="/mnt/virt/nix/debian_jessie_base.img"
img_src_escaped="\/mnt\/virt\/nix\/debian_jessie_base\.img"

new_img_src="/mnt/virt/nix/debian_jessie_$hostname.img"
new_img_src_escaped="\/mnt\/virt\/nix\/debian_jessie_$hostname\.img"

vm_mount_path="/mnt/vm"


# --------------------------------
# functions
# --------------------------------

copy_vm_disk() {
    $SUDO $VIRSH suspend "$domain"
    $CP "$img_src" "$new_img_src"
    $SUDO $VIRSH resume "$domain"
}

mount_vm() {
    $KPARTX -a "$new_img_src"
    $MOUNT "/dev/mapper/loop1p1" "$vm_mount_path"
}

unmount_vm() {
    $UMOUNT "$vm_mount_path"
    $KPARTX -d "$new_img_src"
}

set_hostname() {
    echo "Setting hostname to $hostname"
    $SED -i -e "s/base0/$hostname/" "$vm_mount_path/etc/hostname"
    echo "Setting 127.0.0.1 host to $hostname"
    $SED -i -e "s/base0/$hostname/" "$vm_mount_path/etc/hosts"
}

set_xml() {
    # Copies and modifies a template xml file
    #   <source file="path_to_image"
    #   <name>
    #   <uuid>
    #   <mac \>

    new_xml="/etc/libvirt/qemu/debian_jessie_$hostname.xml"
    $CP "$xml_template_path" "$new_xml"

    # Change <source file=>
    $SED -i -e "s/$img_src_escaped/$new_img_src_escaped/" "$new_xml"

    # Change <name>
    $SED -i -e "s/<name\>.*/<name\>$hostname\<\/name\>/" "$new_xml"

    # Change uuid
    $SED -i -e "s/\<uuid\>.*/uuid\>`/usr/bin/uuid`\<\/uuid\>/" "$new_xml"

    # Remove MAC and let it auto-generate
    $SED -i -e "s/<mac address.*//" "$new_xml"
}

make_vm() {
    $VIRSH create "$new_xml"
}

usage() {
    echo "[create_vm.sh vm_hostname path_to_template"
    exit 1
}

if [[ $# -ne 2 ]]; then
    usage
fi

copy_vm_disk 
mount_vm 
set_hostname
set_xml
unmount_vm
make_vm 
