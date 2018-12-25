import unittest
import subprocess
import re

class TestMountIscsiTarget(object):

    def __init__(self):
        self.iscsi_target = {}
        self.iscsi_client_name = "ceph-client1"
        self.iscsi_disk_dict = {}

    def _get_iscsi_target_count(self):
        count = 1

        return count

    def _install_iscsi(self):
        cmd = 'yum install iscsi-initiator-utils'
        out, err = self._submit_process(cmd)
        return out

    def _discovery_target(self, iscsi_target_dict):
        for key, value in iscsi_target_dict.items():
            cmd = ('iscsiadm -m discovery -t st -p %s; ' % value[0])
            print cmd
            out, err = self._submit_process(cmd)
            if out.find(key) == -1 :
                print out
                print("No specified target found for %s" % key)

    def _login_target(self, iscsi_target_dict):
        for key, value in iscsi_target_dict.items():
            cmd = 'iscsiadm -m node -T %s -p %s -l && ' % (key, value[0])
            cmd += 'sleep 20;'
            print cmd
            out, err = self._submit_process(cmd)

            print out

    def _find_disk_list(self):
        cmd = 'lsblk'
        out, err = self._submit_process(cmd)
        return out

    def _get_iscsi_disk(self, buffer_before, buffer_after):
        pat = '.* disk'
        info = re.findall(pat, buffer_before)
        buffer_before_disk_list = []

        for i in range(len(info)):
            buffer_before_disk_list.append(info[i].split()[0])
        print ("buffer_before_disk_list: %s" % buffer_before_disk_list)

        info = re.findall(pat, buffer_after)
        buffer_after_disk_list = []
        for i in range(len(info)):
            buffer_after_disk_list.append(info[i].split()[0])
        print ("buffer_after_disk_list: %s" % buffer_after_disk_list)

        mount_disk_list = []
        if len(buffer_before_disk_list) == len(buffer_after_disk_list):
            return None
        else:
            for j in range(len(buffer_after_disk_list)):
                if buffer_after_disk_list[j] not in buffer_before_disk_list:
                    mount_disk_list.append(buffer_after_disk_list[j])

        return mount_disk_list

    def _append_iscsi_disk_dict(self, iscsi_name, iscsi_mount_list):
        if iscsi_mount_list:
            for i in range(len(iscsi_mount_list)-1):
                iscsi_mount_list[i] = 'dev/' + str(iscsi_mount_list[i])

            self.iscsi_disk_dict[iscsi_name] = iscsi_mount_list

        return self.iscsi_disk_dict

    def _logout_target(self, iscsi_target_dict):
        for key, value in iscsi_target_dict.items():
            cmd = 'iscsiadm -m node -T %s -p %s -u && ' % (key, value[0])
            cmd += 'sleep 20;'
            out, err = self._submit_process(cmd)

    def _submit_process(self, cmd):
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)
        out, err = p.communicate()

        return out, err

    def test_mount_iscsi_target(self):
        target_info_list = ["192.168.0.9", "192.168.0.14", "192.168.0.15"]
        self.iscsi_target['iqn.2018-10.com.lenovo:target1'] = target_info_list


    def tearDown(self):
        pass

if __name__ == '__main__':
    test = TestMountIscsiTarget()
    before = test._find_disk_list()
    print before

    test.test_mount_iscsi_target()
    test._discovery_target(test.iscsi_target)
    test._login_target(test.iscsi_target)
    after = test._find_disk_list()
    print after

    mount_disk_list = test._get_iscsi_disk(before, after)
    print mount_disk_list
    iscsi_disk_dict = test._append_iscsi_disk_dict(test.iscsi_client_name, mount_disk_list)
    print iscsi_disk_dict

    test._logout_target(test.iscsi_target)






