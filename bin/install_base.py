#!/usr/bin/env python

import sh
import sys

def install_base_vm(base_domain="", install_media_path="", base_img_path="", base_RAM=512):
    """
        Use virt-install to create a base vm to make clones

        base_domain == domain name according to virsh

        install_media_path == path to .iso, pool, etc

        base_img_path == path to .img file to be created
    """

    if base_domain and install_media_path and base_img_path:
        sh.virt_install('--connect=qemu:///system',
                '-n %s' % (base_domain),
                '-r %s' % (base_RAM),
                '--disk', 'path=%s,size=5,sparse=false' % (base_img_path),
                '-l %s' % (install_media_path),
                '--os-type', 'linux',
                '--hvm',
                '--vnc')

    else:
        sys.exit("Invalid parameters to install_base_vm()")

if __name__ == "__main__":
    if len(sys.argv) == 4:
        base_domain = sys.argv[1]
        install_media_path = sys.argv[2]
        base_img_path = sys.argv[3]

        install_base_vm(base_domain, install_media_path, base_img_path)

    else:
        sys.exit("Usage: %s base_domain install_media_path base_img_path" % (sys.argv[0]))
