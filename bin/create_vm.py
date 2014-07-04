#!/usr/bin/env python

import sh
import sys
import os

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

    def copy_vm_disk(self, img_path="", new_img_path=""):
        """
            Creates a COW copy of img_path in new_img_path
        """
        if not os.path.exists(img_path):
            sys.exit("Path to base image does not exist")

        with sh.sudo:
            sh.cp('--reflink=auto', "%s" % (img_path), "%s" % (new_img_path))

        if not os.path.exists(new_img_path):
            sys.exit("Should have created a new image")

    def __get_host_count(self, host_type=""):
        """
            Get the current number of VMs running that match
            host_type string
        """
        hosts = 0
        if host_type:
            try:
                hosts = sh.wc(sh.awk(sh.grep(sh.virsh('list', '--all'), '"%s"' % (host_type)), '{print $2}'), '-l')
            except:
                hosts = 0
        else:
            sys.exit("Can't count non-existant host_type")

        return hosts

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

    def create(self):
        """
            Create one virtual machine
        """
        self.hostname = self.host_type + str(self.__get_host_count(self.host_type))

        new_img = os.path.join(self.storage_path, self.hostname + ".img")
        self.copy_vm_disk(self.img_src, new_img)
        self.mount_vm(new_img, self.mnt_path)


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
