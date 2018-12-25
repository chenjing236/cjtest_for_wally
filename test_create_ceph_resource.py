import unittest
import subprocess
import re
import json
import time
import requests
import httplib
import urllib

class TestCreateCephResource(object):

    def __init__(self):
        self.rbd_list = []



    def _create_pool(self):
        cluster_id = 1
        pool_num = 2
        pool_name = "cj_test_%s" % pool_num
        pg_num = 64
        safe_type = 0
        data_block_num = 3
        code_block_num = 0
        group_id = 1
        vgroup_id = 1
        write_mode = "writeback"

       
        cmd = "cephmgmtclient create-pool -c %s -n %s -P %s -st %s " \
              "--data_block_num %s --code_block_num %s -gid %s -lgid %s  " \
              "-wrm %s" % (cluster_id, pool_name, pg_num, safe_type,
                           data_block_num, code_block_num, group_id,
                           vgroup_id, write_mode)

        out, err = self._submit_process(cmd)

        if err is not None:
            return
        else:
           pool_id =  self._find_pool_id(out)

           return pool_id


    def _find_pool_id(self, text):
        pat = '"pool_id": [0-9]+'
        pool_info = re.findall(pat, text)
        pat = '[0-9]+'
        pool_id = re.findall(pat, pool_info[0])
        print 'pool_id is %s' % pool_id[0]

        return int(pool_id[0])
	

    def _create_rbd(self, count, pool_id):
        cluster_id = 1
        #pool_id = 1
        rbd_num = 1
        rbd_name = "cj_test_%s" % rbd_num
        capacity = 1024 * 1024 * 50
        num = 1
        shared = 3

        while count >= 1:
            cmd = "cephmgmtclient create-rbd --cluster_id=%s --pool_id=%s " \
                  "--name=%s --capacity=%s --num=%s --shared=%s" \
                  % (cluster_id, pool_id, rbd_name, capacity, num, shared)
            out, err = self._submit_process(cmd)
            print out

            if err is not None:
                return
            else:
                self.rbd_list.append(self._find_rbd_id(out))

            count -= 1
            rbd_num += 1

    def _find_rbd_id(self, text):
        pat = '"rbd_id": [0-9]+'
        rbd_info = re.findall(pat, text)
        pat = '[0-9]+'
        rbd_id = re.findall(pat, rbd_info[0])
        print 'rbd_id is %s' % rbd_id[0]

        return int(rbd_id[0])

    def _get_token(self):
        cmd = "keystone token-get"
        out, err = self._submit_process(cmd)
        print out

        pat = " expires   | .*"
        token = re.findall(pat, out)
        token_info = token[len(token)-3].split('|')[1]
        print 'token is %s' % token_info
        return token_info

    def _create_gateway(self):
        token = self._get_token()
        name = "test_gateway1"
        service = "iSCSI"
        public_ip = "192.168.86.3/24"
        id = 3
        interface = "eth0"

        cmd = '''curl -X POST http://localhost:9999/v1/clusters/1/gateway ''' \
              '''-H 'Content-type:application/json' -H 'LOG_USER:admin' ''' \
              '''-H 'x-auth-token:%s' ''' \
              '''-d '{"name":"%s","services":"%s","public_ip":"%s","nodes":[{"id":%s,"interface":"%s"}]}' ''' \
              % (token, name, service, public_ip, id, interface)
        print cmd
        out, err = self._submit_process(cmd)
        print out

        return name

    def _create_gateway_r(self):
        token = self._get_token()
        name = "test_gateway1"
        service = "iSCSI"
        public_ip = "192.168.86.3/24"
        id = 3
        interface = "eth0"
        ip = "localhost"
        port = 9999
        cluster = 1

        data = {'name': name, 'services': service, 'public_ip': public_ip, 'nodes': [{'id':id,'interface':interface}]}
        headers = {"x-auth-token": "%s" % str(token).strip(), "Content-type": "application/json", "LOG_USER": "admin"}
        print 'data is %s' % data
        print 'headers is %s' % headers
        url = 'http://localhost:9999' + '/v1/clusters/%s/gateway' % cluster
        r = requests.post(url, data=data, headers=headers, verify=True)
        #response = r.json()
        print "Post Response is %s" % r

        return name

    def _query_gateway_list(self, gateway_name):
        cluster_id = 1
        token = self._get_token()
        cmd = '''curl -X get 'http://localhost:9999/v1/clusters/%s/gateway?preindex=1&sufindex=0' ''' \
              ''' -H 'Content-type:application/json' -H 'LOG_USER:admin' ''' \
              ''' -H  'x-auth-token:%s'  |python -m json.tool''' % (cluster_id, token)
        print cmd
        out, err = self._submit_process(cmd)
        print out

        if err is not None:
            return
        else:
            self._find_gateway_id(out, 'test_gateway1')

    def _query_gateway_list_r(self, gateway_name):
        cluster_id = 1
        token = self._get_token()
        url = 'http://localhost:9999/v1/clusters/%s/gateway?preindex=1&sufindex=0' % cluster_id
        headers = {"x-auth-token": '%s' % str(token).strip(), "Content-type": "application/json", "LOG_USER": "admin"}
        print "headers is %s" % headers
        r = requests.get(url, headers=headers, verify=True)
        data = r.text
        print data
        response = r.json()
        print "Get Response is %s" % response
        print "Item is %s" % response['items']
        items = response['items']

        for i in items:
            if i.get('name') in gateway_name:
                print 'gateway id is %s' % i.get('id')
                return i.get('id')

    def _find_gateway_id(self, text, gateway_name):
        pat = '"items": (.*)'
        gateway_info = re.findall(pat, text)
        print 'gateway_info is %s' % gateway_info


    def _create_iscsi(self, gateway_id):
        token = self._get_token()
        initiator_ip = "192.168.0.24"
        target_name = "iqn.2018-11.com.lenovo:target1"
        multipath = "1"

        cmd = '''curl -X POST http://localhost:9999/v1/clusters/1/iscsitargets ''' \
              '''-H 'Content-type:application/json' -H 'LOG_USER:admin' '''\
              '''-H 'X-Auth-Token:%s' ''' \
              '''-d '{"entity":{"initiator_ips":"%s","target_name":"%s", "multipath":"%s","gateway_id": %s}}' ''' \
              % (token, initiator_ip, target_name, multipath, gateway_id)
        print "create iscsi cmd is %s" % cmd
        out, err = self._submit_process(cmd)
        print out

        return target_name

    def _query_iscsi_list_r(self, iscsi_name):
        cluster_id = 1
        token = self._get_token()
        url = 'http://localhost:9999/v1/clusters/%s/iscsitargets?preindex=1&sufindex=2' % cluster_id
        headers = {"x-auth-token": '%s' % str(token).strip(), "Content-type": "application/json", "LOG_USER": "admin"}
        r = requests.get(url, headers=headers, verify=True)
        data = r.text
        response = r.json()
        print "Item is %s" % response['items']
        items = response['items']

        for i in items:
            if i.get('target_name') in iscsi_name:
                print 'iscsi id is %s' % i.get('target_id')
                return i.get('target_id')


    def _associate_lun(self):
        cluster_id = 1
        target_id = 1
        pool_id = 1
        for rbd in self.rbd_list:
            cmd = "cephmgmtclient associate-lun -c %s -t %s -r %s -p %s" \
                  % (cluster_id, target_id, rbd, pool_id)

            out, err = self._submit_process(cmd)
            print out

    def _submit_process(self, cmd):
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        out, err = p.communicate()

        return out, err

    def _write_log(self, pool_id, rbd_list):
        with open("create_pool_rbd.log", "wr") as f:
            f.writelines("pool_id:%s\n" % pool_id)
            rbd_id = ','.join(rbd_list)
            f.writelines("rbd_id:%s\n" % rbd_id)

    def _read_log_for_rbds(self):
        pool_dict = {}
        rbd_dict = {}
        with open("create_pool_rbd.log", "r") as f:
            line_index = 1
            for line in f.readlines():
                if line_index == 1:
                    key, value = line.strip().split(':')
                    pool_dict[key] = value
                if line_index == 2:
                    key, value = line.strip().split(':')
                    rbd_dict[key] = value
                line_index += 1

        print "pool_dict is %s" % pool_dict
        print "rbd_dict is %s" % rbd_dict


    def tearDown(self):
        pass

if __name__ == '__main__':
    test = TestCreateCephResource()
    #pool_id = test._create_pool()
    #test._create_rbd(1, pool_id)
    '''test._get_token()
    gateway_name = test._create_gateway()
    time.sleep(30)
    gateway_id = test._query_gateway_list_r(gateway_name)
    iscsi_name = test._create_iscsi(gateway_id)
    time.sleep(30)
    iscsi_id = test._query_iscsi_list_r(iscsi_name)'''

    pool_id = 1
    rbd_list = ['rbd0_0', 'rbd0_1', 'rbd0_2', 'rbd1_0', 'rbd1_1', 'rbd1_2', 'rbd2_0', 'rbd2_1', 'rbd2_2']
    test._write_log(pool_id, rbd_list)
    test._read_log_for_rbds()
    






