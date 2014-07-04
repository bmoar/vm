#!/usr/bin/env python

import sh
import sys
import os

class VirtualMachine():
    def __init__(self, host_type="", xml_template_path="", img_src="", mnt_path="/mnt/vm"):
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

        self.hostname = ""
        self.domain = ""

    def copy_vm_disk(self, img_path="", new_img_path=""):
        """
            Creates a COW copy of img_path in new_img_path
        """
        if not os.path.exists(img_path):
            sys.exit("Path to base image does not exist")

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
        pass

    def start(self):
        """
            Create one virtual machine
        """
        self.hostname = self.host_type + str(self.__get_host_count(self.host_type))


if __name__ == "__main__":
    if len(sys.argv) == 5:
        host_type = sys.argv[1]
        xml_template_path = sys.argv[2]
        img_src = sys.argv[3]
        mnt_path = sys.argv[4]

        vm = VirtualMachine(host_type, xml_template_path, img_src, mnt_path)
        vm.start()

    else:
        sys.exit("Usage: %s host_type xml_template_path img_src mnt_path" % (sys.argv[0]))
