from .linstor_testcase import LinstorTestCase
from linstor.sharedconsts import *


class TestProperties(LinstorTestCase):

    def test_set_properties(self):
        # create all object kinds
        cnode_resp = self.execute_with_single_resp(['node', 'create', 'node1', '192.168.100.1'])
        self.assertTrue(cnode_resp.is_success())

        # create storagepool
        storpool_resps = self.execute_with_resp(['storage-pool', 'create', 'node1', 'storage', 'lvm', 'lvmpool'])
        self.assertTrue(storpool_resps[0].is_warning())
        self.assertEqual(WARN_NOT_CONNECTED | MASK_STOR_POOL | MASK_CRT, storpool_resps[0].ret_code)
        self.assertTrue(storpool_resps[1].is_success())

        # create resource def
        rsc_dfn_resp = self.execute_with_single_resp(['resource-definition', 'create', 'rsc1'])
        self.assertTrue(rsc_dfn_resp.is_success())

        # create volume def
        vlm_dfn_resp = self.execute_with_single_resp(['volume-definition', 'create', 'rsc1', '1Gib'])
        self.assertTrue(vlm_dfn_resp.is_success())

        # create resource on node1
        rsc_resps = self.execute_with_resp(['resource', 'create', '--async', '-s', 'storage', 'node1', 'rsc1'])
        self.assertEqual(3, len(rsc_resps))
        self.assertTrue(rsc_resps[0].is_warning())  # satellite not reachable
        self.assertTrue(rsc_resps[1].is_success())  # resource created
        self.assertTrue(rsc_resps[2].is_success())  # volume created

        # start prop tests
        node_resp = self.execute_with_single_resp(
            ['node', 'set-property', 'node1', '--aux', 'test_prop', 'val']
        )
        self.assertTrue(node_resp.is_success())

        node_props = self.execute_with_machine_output(['node', 'list-properties', 'node1'])
        self.assertEqual(1, len(node_props))
        node_props = node_props[0]
        self.assertEqual(2, len(node_props))
        prop = self.find_prop(node_props, NAMESPC_AUXILIARY + '/test_prop')
        self.check_prop(prop, NAMESPC_AUXILIARY + '/test_prop', 'val')

        node_resp = self.execute_with_single_resp(
            ['node', 'set-property', 'node1', '--aux', 'another_prop', 'value with spaces']
        )
        self.assertTrue(node_resp.is_success())

        node_props = self.execute_with_machine_output(['node', 'list-properties', 'node1'])
        self.assertEqual(1, len(node_props))
        node_props = node_props[0]
        self.assertEqual(3, len(node_props))
        prop = self.find_prop(node_props, NAMESPC_AUXILIARY + '/test_prop')
        self.check_prop(prop, NAMESPC_AUXILIARY + '/test_prop', 'val')

        prop = self.find_prop(node_props, NAMESPC_AUXILIARY + '/another_prop')
        self.check_prop(prop, NAMESPC_AUXILIARY + '/another_prop', 'value with spaces')

        # storage pool definition props
        storage_resp = self.execute_with_single_resp(
            ['storage-pool-definition', 'set-property', 'DfltStorPool', '--aux', 'stor', 'lvmcomplex']
        )
        self.assertTrue(storage_resp.is_success())

        storage_props = self.execute_with_machine_output(['storage-pool-definition', 'list-properties', 'DfltStorPool'])
        self.assertEqual(1, len(storage_props))
        storage_props = storage_props[0]
        self.assertEqual(1, len(storage_props))
        prop = self.find_prop(storage_props, NAMESPC_AUXILIARY + '/stor')
        self.check_prop(prop, NAMESPC_AUXILIARY + '/stor', 'lvmcomplex')

        # storage pool props
        storage_props = self.execute_with_machine_output(['storage-pool', 'list-properties', 'node1', 'storage'])
        self.assertEqual(1, len(storage_props))
        storage_props = storage_props[0]
        self.assertEqual(1, len(storage_props))
        prop = self.find_prop(storage_props, NAMESPC_STORAGE_DRIVER + '/LvmVg')
        self.check_prop(prop, NAMESPC_STORAGE_DRIVER + '/LvmVg', 'lvmpool')

        storage_resp = self.execute_with_resp(
            ['storage-pool', 'set-property', 'node1', 'storage', '--aux', 'stor', 'lvmcomplex']
        )
        self.assertEqual(2, len(storage_resp))
        self.assertTrue(storage_resp[0].is_success())

        storage_props = self.execute_with_machine_output(['storage-pool', 'list-properties', 'node1', 'storage'])
        self.assertEqual(1, len(storage_props))
        storage_props = storage_props[0]
        self.assertEqual(2, len(storage_props))
        prop = self.find_prop(storage_props, NAMESPC_STORAGE_DRIVER + '/LvmVg')
        self.check_prop(prop, NAMESPC_STORAGE_DRIVER + '/LvmVg', 'lvmpool')

        prop = self.find_prop(storage_props, NAMESPC_AUXILIARY + '/stor')
        self.check_prop(prop, NAMESPC_AUXILIARY + '/stor', 'lvmcomplex')

        # resource definition
        resourcedef_resp = self.execute_with_resp(
            ['resource-definition', 'set-property', 'rsc1', '--aux', 'user', 'alexa']
        )
        self.assertEqual(2, len(resourcedef_resp))
        self.assertTrue(resourcedef_resp[0].is_success())

        resourcedef_props = self.execute_with_machine_output(['resource-definition', 'list-properties', 'rsc1'])
        self.assertEqual(1, len(resourcedef_props))
        resourcedef_props = resourcedef_props[0]
        self.assertEqual(1, len(resourcedef_props))
        prop = self.find_prop(resourcedef_props, NAMESPC_AUXILIARY + '/user')
        self.check_prop(prop, NAMESPC_AUXILIARY + '/user', 'alexa')

        # volume definition
        volumedef_resp = self.execute_with_resp(
            ['volume-definition', 'set-property', 'rsc1', '0', '--aux', 'volumespec', 'cascading']
        )
        self.assertEqual(2, len(volumedef_resp))
        self.assertTrue(storage_resp[0].is_success())

        volumedef_props = self.execute_with_machine_output(['volume-definition', 'list-properties', 'rsc1', '0'])
        self.assertEqual(1, len(volumedef_props))
        volumedef_props = volumedef_props[0]
        self.assertEqual(1, len(volumedef_props))
        prop = self.find_prop(volumedef_props, NAMESPC_AUXILIARY + '/volumespec')
        self.check_prop(prop, NAMESPC_AUXILIARY + '/volumespec', 'cascading')

        # resource
        resource_props = self.execute_with_machine_output(['resource', 'list-properties', 'node1', 'rsc1'])
        self.assertEqual(1, len(resource_props))
        resource_props = resource_props[0]
        self.assertEqual(1, len(resource_props))
        prop = self.find_prop(resource_props, KEY_STOR_POOL_NAME)
        self.check_prop(prop, KEY_STOR_POOL_NAME, 'storage')

        storage_resp = self.execute_with_resp(
            ['resource', 'set-property', 'node1', 'rsc1', '--aux', 'NIC', '10.0.0.1']
        )
        self.assertEqual(2, len(storage_resp))
        self.assertTrue(storage_resp[0].is_warning())
        self.assertTrue(storage_resp[1].is_success())

        resource_props = self.execute_with_machine_output(['resource', 'list-properties', 'node1', 'rsc1'])
        self.assertEqual(1, len(resource_props))
        resource_props = resource_props[0]
        self.assertEqual(2, len(resource_props))
        prop = self.find_prop(resource_props, KEY_STOR_POOL_NAME)
        self.check_prop(prop, KEY_STOR_POOL_NAME, 'storage')
        prop = self.find_prop(resource_props, NAMESPC_AUXILIARY + '/NIC')
        self.check_prop(prop, NAMESPC_AUXILIARY + '/NIC', '10.0.0.1')
