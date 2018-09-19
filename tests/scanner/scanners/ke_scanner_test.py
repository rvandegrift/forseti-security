# Copyright 2017 The Forseti Security Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""KE Rule Scanner Tests."""

import unittest
import mock

from tests import unittest_utils
from tests.services.util.db import create_test_engine
from google.cloud.forseti.scanner.scanners import ke_scanner
from google.cloud.forseti.services.dao import ModelManager


SERVER_CONFIG = '''
{
}
'''

FAKE_CLUSTER = '''
{
    "name": "fake-cluster",
    "nodePools": [
        {
            "name": "default-pool",
            "version": "1.7.11-gke.1",
            "config": {
                "imageType": "COS"
            }
        },
        {
            "name": "secondary-pool",
            "version": "1.7.11-gke.1",
            "config": {
                "imageType": "COS"
            }
        }
    ],
    "addonsConfig": {
        "httpLoadBalancing": {},
        "kubernetesDashboard": {
            "disabled": true
        },
        "istioConfig": {
            "auth": "AUTH_MUTUAL_TLS"
        }
    }
}
'''

FAKE_CLUSTERS = {
    'fake-cluster': FAKE_CLUSTER,
}


class FakeServiceConfig(object):

    def __init__(self):
        engine = create_test_engine()
        self.model_manager = ModelManager(engine)


class KeScannerTest(unittest_utils.ForsetiTestCase):

    @classmethod
    def setUpClass(cls):
        cls.service_config = FakeServiceConfig()
        cls.model_name = cls.service_config.model_manager.create(
            name='ke-scanner-test')

        scoped_session, data_access = (
            cls.service_config.model_manager.get(cls.model_name))

        # Add organization and project to model.
        with scoped_session as session:
            organization = data_access.add_resource_by_name(
                session, 'organization/12345', '', True)
            project = data_access.add_resource(session, 'project/fake-project',
                                               organization)

            ke_cluster = data_access.add_resource(
                session,
                'kubernetes_cluster/fake-cluster',
                project,
            )

            ke_cluster.data = FAKE_CLUSTER

            sc = data_access.add_resource(
                session,
                'kubernetes_service_config/fake-cluster',
                ke_cluster,
            )
            sc.data = SERVER_CONFIG

            session.commit()

    def setUp(self):

        self.scanner = ke_scanner.KeScanner(
            {}, {}, self.service_config, self.model_name,
            '', unittest_utils.get_datafile_path(
                __file__, 'ke_scanner_test_data.yaml'))

    @mock.patch.object(
        ke_scanner.KeScanner,
        '_output_results_to_db', autospec=True)
    def test_run_scanner(self, mock_output_results):
        self.scanner.run()
        expected_violations = [
            {'rule_name': 'explicit whitelist, fail', 'resource_data': '{"nodePools": [{"version": "1.7.11-gke.1", "config": {"imageType": "COS"}, "name": "default-pool"}, {"version": "1.7.11-gke.1", "config": {"imageType": "COS"}, "name": "secondary-pool"}], "addonsConfig": {"httpLoadBalancing": {}, "istioConfig": {"auth": "AUTH_MUTUAL_TLS"}, "kubernetesDashboard": {"disabled": true}}, "name": "fake-cluster"}', 'full_name': u'organization/12345/project/fake-project/kubernetes_cluster/fake-cluster/', 'resource_id': u'fake-cluster', 'rule_index': 2, 'violation_type': 'KE_VIOLATION', 'violation_data': {'violation_reason': u"name has value fake-cluster, which is not in the whitelist (['real-cluster'])", 'cluster_name': u'fake-cluster', 'project_id': u'fake-project', 'full_name': u'organization/12345/project/fake-project/kubernetes_cluster/fake-cluster/'}, 'resource_type': 'kubernetes_cluster'},
            {'rule_name': 'explicit blacklist, fail', 'resource_data': '{"nodePools": [{"version": "1.7.11-gke.1", "config": {"imageType": "COS"}, "name": "default-pool"}, {"version": "1.7.11-gke.1", "config": {"imageType": "COS"}, "name": "secondary-pool"}], "addonsConfig": {"httpLoadBalancing": {}, "istioConfig": {"auth": "AUTH_MUTUAL_TLS"}, "kubernetesDashboard": {"disabled": true}}, "name": "fake-cluster"}', 'full_name': u'organization/12345/project/fake-project/kubernetes_cluster/fake-cluster/', 'resource_id': u'fake-cluster', 'rule_index': 4, 'violation_type': 'KE_VIOLATION', 'violation_data': {'violation_reason': u"name has value fake-cluster, which is in the blacklist (['fake-cluster'])", 'cluster_name': u'fake-cluster', 'project_id': u'fake-project', 'full_name': u'organization/12345/project/fake-project/kubernetes_cluster/fake-cluster/'}, 'resource_type': 'kubernetes_cluster'},
            {'rule_name': 'multiple values, fail', 'resource_data': '{"nodePools": [{"version": "1.7.11-gke.1", "config": {"imageType": "COS"}, "name": "default-pool"}, {"version": "1.7.11-gke.1", "config": {"imageType": "COS"}, "name": "secondary-pool"}], "addonsConfig": {"httpLoadBalancing": {}, "istioConfig": {"auth": "AUTH_MUTUAL_TLS"}, "kubernetesDashboard": {"disabled": true}}, "name": "fake-cluster"}', 'full_name': u'organization/12345/project/fake-project/kubernetes_cluster/fake-cluster/', 'resource_id': u'fake-cluster', 'rule_index': 6, 'violation_type': 'KE_VIOLATION', 'violation_data': {'violation_reason': u"name has value fake-cluster, which is not in the whitelist (['real-cluster', 'imaginary-cluster'])", 'cluster_name': u'fake-cluster', 'project_id': u'fake-project', 'full_name': u'organization/12345/project/fake-project/kubernetes_cluster/fake-cluster/'}, 'resource_type': 'kubernetes_cluster'},
            {'rule_name': 'use projection, look for a list, fail', 'resource_data': '{"nodePools": [{"version": "1.7.11-gke.1", "config": {"imageType": "COS"}, "name": "default-pool"}, {"version": "1.7.11-gke.1", "config": {"imageType": "COS"}, "name": "secondary-pool"}], "addonsConfig": {"httpLoadBalancing": {}, "istioConfig": {"auth": "AUTH_MUTUAL_TLS"}, "kubernetesDashboard": {"disabled": true}}, "name": "fake-cluster"}', 'full_name': u'organization/12345/project/fake-project/kubernetes_cluster/fake-cluster/', 'resource_id': u'fake-cluster', 'rule_index': 9, 'violation_type': 'KE_VIOLATION', 'violation_data': {'violation_reason': "nodePools[*].config.imageType has value [u'COS', u'COS'], which is not in the whitelist ([['COS'], ['Ubuntu', 'COS']])", 'cluster_name': u'fake-cluster', 'project_id': u'fake-project', 'full_name': u'organization/12345/project/fake-project/kubernetes_cluster/fake-cluster/'}, 'resource_type': 'kubernetes_cluster'},
        ]

        mock_output_results.assert_called_once_with(mock.ANY,
                                                    expected_violations)


if __name__ == '__main__':
    unittest.main()
