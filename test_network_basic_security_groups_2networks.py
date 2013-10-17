#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
__author__ = 'Albert'
__email__ = "albert.vico@midokura.com"



from tempest import config
from tempest.openstack.common import log as logging
from tempest.scenario.midokura.midotools import scenario
from tempest import test


LOG = logging.getLogger(__name__)
CIDR1 = "10.10.10.0/24"
CIDR2 = "10.10.2.0/24"
CONF = config.CONF


class TestNetworkAdvancedSecurityGroups2Networks(scenario.TestScenario):
    """
        Prerequisite:
            - two VMs A and B
            - in same tenant
            - in different subnets SnetA, SnetB
            - In the same and only SG Sg
            - Sg has no ingress or egress rules
            - VMs with net cat
    test1:
        Steps:
            1- send pint A to B
        Expecte results:
            Ping does NOT work
    test2:
        steps:
            1- add custom icmp rule in SG S, for ICMP type 8, code -1, for egress
            2- add custom icmp rule in SG S, for ICMP type 8, code -1, for ingress
            3- send ping A to B

        Expected results:
            ping does work
    """

    @classmethod
    def setUpClass(cls):
        super(TestNetworkAdvancedSecurityGroups2Networks, cls).setUpClass()
        cls.check_preconditions()

    def setUp(self):
        super(TestNetworkAdvancedSecurityGroups2Networks, self).setUp()
        self.rules = list()
        self.security_group = \
            self._create_security_group_neutron(tenant_id=self.tenant_id)
        self._create_empty_security_group(tenant_id=self.tenant_id, name="sg")
        self._create_loginale_security_group(tenant_id=self.tenant_id)
        self._scenario_conf()
        self.custom_scenario(self.scenario)

    def _scenario_conf(self):
        vm1 = {
            'floating_ip': False,
            'sg': ["sg", "ssh"],
        }
        vm2 = {
            'floating_ip': False,
            'sg': ["sg"],
        }
        routerA = {
            "public": False,
            "name": "router_1"
        }
        subnetA = {
            "network_id": None,
            "ip_version": 4,
            "cidr": CIDR1,
            "allocation_pools": None,
            "routers": [routerA],
            "dns": [],
            "routes": [],
        }
        subnetB = {
            "network_id": None,
            "ip_version": 4,
            "cidr": CIDR2,
            "allocation_pools": None,
            "routers": [routerA],
            "dns": [],
            "routes": [],
        }
        networkA = {
            'subnets': [subnetA],
            'servers': [vm1],
        }
        networkB = {
            'subnets': [subnetB],
            'servers': [vm2],
        }
        tenantA = {
            'networks': [networkA, networkB],
            'tenant_id': None,
            'type': 'default',
            'hasgateway': True,
            'MasterKey': True,
        }
        self.scenario = {
            'tenants': [tenantA],
        }

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_advanced_security_group(self):
        rulesets = [
             {
                'direction': 'egress',
                'protocol': 'icmp',
                'port_range_min': 8,
                'port_range_max': None,

            },
            {
                'direction': 'ingress',
                'protocol': 'icmp',
                'port_range_min': 8,
                'port_range_max': None,
            }
        ]
        sg = self._get_security_group("sg")

        self._create_security_group_rule(secgroup=sg,
                                         tenant_id=self.tenant_id,
                                         **rulesets[0])

        self._create_security_group_rule(secgroup=sg,
                                         tenant_id=self.tenant_id,
                                         **rulesets[1])

        vm1_server = self.servers.items()[0][0]
        vm2_server = self.servers.items()[1][0]
        vm1_pk = self.servers[vm1_server].private_key
        vm2_pk = self.servers[vm2_server].private_key
        vm1 = (vm1_server.networks.values()[0][0], vm1_pk)
        vm2 = (vm2_server.networks.values()[0][0], vm2_pk)
        self._ping_through_gateway(vm1, vm2, should_fail=False)

    @test.attr(type='smoke')
    @test.services('compute', 'network')
    def test_network_advanced_security_group_negative(self):
        vm1_server = self.servers.items()[0][0]
        vm2_server = self.servers.items()[1][0]
        vm1_pk = self.servers[vm1_server].private_key
        vm2_pk = self.servers[vm2_server].private_key
        vm1 = (vm1_server.networks.values()[0][0], vm1_pk)
        vm2 = (vm2_server.networks.values()[0][0], vm2_pk)
        self._ping_through_gateway(vm1, vm2, should_fail=True)