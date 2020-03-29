from pprint import pprint as print
from unittest import mock

from consul_awx import ConsulInventory


@mock.patch("consul.base.Consul.Catalog.node")
@mock.patch("consul.base.Consul.Catalog.nodes")
def test_mock(mocked_catalog_nodes, mocked_catalog_node):
    mocked_catalog_nodes.return_value = (
        "2513",
        [
            {
                "Address": "10.0.0.0",
                "CreateIndex": 7,
                "Datacenter": "dc1",
                "ID": "517ef51b-7ac0-91ff-76f3-8e2ca17e714e",
                "Meta": {
                    "consul-network-segment": "",
                    "cluster": "94",
                    "server_type": "postgresql",
                },
                "ModifyIndex": 12,
                "Node": "node1",
                "TaggedAddresses": {"lan": "10.0.0.0", "wan": "10.0.0.0"},
            },
            {
                "Address": "10.0.0.1",
                "CreateIndex": 9,
                "Datacenter": "dc1",
                "ID": "465baa62-8aec-8148-b7fc-2e5c942c9f26",
                "Meta": {
                    "consul-network-segment": "",
                    "pseudo_bool": "true",
                    "server_type": "nginx",
                },
                "ModifyIndex": 11,
                "Node": "node2",
                "TaggedAddresses": {"lan": "10.0.0.1", "wan": "10.0.0.1"},
            },
            {
                "Address": "10.0.0.2",
                "CreateIndex": 8,
                "Datacenter": "dc1",
                "ID": "eb71d55b-a688-cd45-321b-565a318e2600",
                "Meta": {
                    "consul-network-segment": "",
                    "pseudo_bool": "false",
                    "server_type": "api",
                },
                "ModifyIndex": 10,
                "Node": "node3",
                "TaggedAddresses": {"lan": "10.0.0.2", "wan": "10.0.0.2"},
            },
        ],
    )
    mocked_catalog_node.side_effect = [
        ("2345", {"Node": {}, "Services": {"a": {"Meta": {}, "Tags": ["aa"]}}}),
        ("3456", {"Node": {}, "Services": {"b": {"Meta": {}, "Tags": ["bb"]}}}),
        ("4567", {"Node": {}, "Services": {"c": {"Meta": {}, "Tags": ["cc"]}}}),
    ]
    c = ConsulInventory()
    c.build_full_inventory()
    print(c.inventory)

    mocked_catalog_nodes.call_count == 1
    mocked_catalog_node.call_count == 3
    assert c.inventory == {
        "_meta": {
            "hostvars": {
                "node1": {
                    "ansible_host": "10.0.0.0",
                    "datacenter": "dc1",
                    "server_type": "postgresql",
                    "cluster": 94,
                },
                "node2": {
                    "ansible_host": "10.0.0.1",
                    "datacenter": "dc1",
                    "server_type": "nginx",
                    "pseudo_bool": True,
                },
                "node3": {
                    "ansible_host": "10.0.0.2",
                    "datacenter": "dc1",
                    "server_type": "api",
                    "pseudo_bool": False,
                },
            }
        },
        "a": {"children": ["a_aa"], "hosts": ["node1"]},
        "a_aa": {"children": [], "hosts": ["node1"]},
        "all": {
            "children": [
                "a",
                "a_aa",
                "b",
                "b_bb",
                "c",
                "c_cc",
                "cluster_94",
                "pseudo_bool",
                "server_type_api",
                "server_type_nginx",
                "server_type_postgresql",
                "ungrouped",
            ],
            "hosts": [],
        },
        "b": {"children": ["b_bb"], "hosts": ["node2"]},
        "b_bb": {"children": [], "hosts": ["node2"]},
        "c": {"children": ["c_cc"], "hosts": ["node3"]},
        "c_cc": {"children": [], "hosts": ["node3"]},
        "cluster_94": {"children": [], "hosts": ["node1"]},
        "pseudo_bool": {"children": [], "hosts": ["node2"]},
        "server_type_api": {"children": [], "hosts": ["node3"]},
        "server_type_nginx": {"children": [], "hosts": ["node2"]},
        "server_type_postgresql": {"children": [], "hosts": ["node1"]},
        "ungrouped": {"children": [], "hosts": []},
    }
