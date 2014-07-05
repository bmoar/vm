#!/usr/bin/env python

import sh
import sys
import os
import xml.etree.ElementTree as ET
import uuid

class VirtualMachine():
    def __init__(self, host_type="", xml_template_path="", img_src="", mnt_path="/mnt/vm", storage_path="/mnt/virt/nix/"):
        """
            Initialize a new VirtualMachine

            host_type == webserver, ssh, etc. Will be used to create the hostname
            xml_template_path == path to the xml template of the base img used to create clone
            img_src == path to the base vm image to clone
            mnt_path == path to mount the new vm machine
        """
        self.host_type = host_type
        self.xml_template_path = xml_template_path
        self.img_src = img_src
        self.mnt_path = mnt_path
        self.storage_path = storage_path

        self.hostname = ""
        self.domain = ""

    def copy_file(self, src="", dest=""):
        """
            Creates a COW copy of src in dest
        """
        if not os.path.exists(src):
            sys.exit("Path to base image does not exist")

        with sh.sudo:
            sh.cp('--reflink=auto', "%s" % (src), "%s" % (dest))

        if not os.path.exists(dest):
            sys.exit("Should have created a new image")

    def __get_host_count(self, host_type=""):
        """
            Get the current number of VMs running that match
            host_type string
        """
        hosts = 0
        if host_type:
            hosts = sh.wc(sh.awk(sh.grep(sh.virsh('list', '--all'), '%s' % host_type), '{print $2}'), '-l')
        else:
            sys.exit("Can't count non-existant host_type")

        return str(hosts).rstrip()

    def rm_file(self, file=""):
        """
            Removes a VM image path
        """

        if not os.path.exists(file):
            sys.exit("Tried to remove a non-existant img")

        if file == "*" or file == "/":
            sys.exit("Tried to remove root or everything")

        sh.rm('%s' % file)

    def create_vm(self, new_xml=""):
        """
            use virsh to start the new vm
        """
        sh.virsh('create', '%s' % (new_xml))

    def mount_vm(self, img_src="", mount_path=""):
        """
            Mount img_src at mount_path with kpartx
        """
        if not os.path.exists(img_src):
            sys.exit("Invalid image to mount: %s" % (img_src))

        if not os.path.exists(mount_path):
            sys.exit("Invalid mount path: %s" % (mount_path))

        with sh.sudo:
            sh.kpartx('-a', img_src)
            mount_device=sh.head(sh.awk(sh.grep(sh.kpartx('-l', img_src), '-v', 'deleted'), '{print $1}'), '-1')
            sh.mount("/dev/mapper/%s" % (mount_device.rstrip()), mount_path)

    def set_vm_hostname(self, hostname="", mount_path=""):
        """
            Changes /etc/hosts and /etc/hostname
            to match the new hostname
        """

        if not os.path.exists(mount_path):
            sys.exit("Invalid mount_path")

        if not hostname:
            sys.exit("Can't set a NULL hostname")

        with sh.sudo:

            # can't os.path.join these paths, join sucks and drops the last
            # abs path
            hostname_path = ""
            hosts_path = ""

            if mnt_path.endswith("/"):
                hostname_path = mnt_path + "etc/hostname"
                hosts_path = mnt_path + "etc/hosts"
            else:
                hostname_path = mnt_path + "/etc/hostname"
                hosts_path = mnt_path + "/etc/hosts"

            with open(hostname_path, 'w') as f:
                f.write(hostname)

            hosts = ""
            with open(hosts_path, 'r') as f:
                for line in f:
                    hosts = hosts + line.replace("base0", hostname)

            with open(hosts_path, 'w') as f:
                f.write(hosts)

    def set_vm_config(self, vm_hostname="", vm_img_path="", config_path=""):
        """
            Modify the vm config file

            <source file="path_to_image"
            <name> == vm_hostname
            <uuid> == new random
            <mac \> == delete
        """
        if not vm_hostname:
            sys.exit("Could not set a NULL vm_hostname")

        if not os.path.exists(vm_img_path):
            sys.exit("Error opening %s" % (vm_img_path))

        if not os.path.exists(config_path):
            sys.exit("Could not open a non-existant config")

        tree = ET.parse(config_path)
        root = tree.getroot()

        for source in root.findall("./devices/disk/source"):
            source.attrib["file"] = vm_img_path

        for name in root.findall("./name"):
            name.text = vm_hostname

        tree.write(config_path)

    def create_vm(self, xml_config_path=""):
        """
            Create the actual VM with virsh with hostname
        """

        if not os.path.exists(xml_config_path):
            sys.exit("Error opening %s" % (xml_config_path))

        with sh.sudo:
            sh.virsh("create", xml_config_path)

    def create(self):
        """
            Create one virtual machine
        """
        self.hostname = self.host_type + str(self.__get_host_count(self.host_type))

        new_img = os.path.join(self.storage_path, self.hostname + ".img")
        self.copy_file(self.img_src, new_img)
        self.mount_vm(new_img, self.mnt_path)
        self.set_vm_hostname(self.hostname, self.mnt_path)

        new_xml = os.path.join("/etc/libvirt/qemu/", self.hostname + ".xml")
        self.copy_file(self.xml_template_path, new_xml)
        self.set_vm_config(self.hostname, new_img, new_xml)
        self.create_vm(new_xml)


if __name__ == "__main__":
    if len(sys.argv) == 5:
        host_type = sys.argv[1]
        xml_template_path = sys.argv[2]
        img_src = sys.argv[3]
        mnt_path = sys.argv[4]

        vm = VirtualMachine(host_type, xml_template_path, img_src, mnt_path)
        vm.create()

    else:
        sys.exit("Usage: %s host_type xml_template_path img_src mnt_path" % (sys.argv[0]))
