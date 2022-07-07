import os
import tempfile
from pprint import pprint as print
from unittest import mock

import pytest
from consul_awx import ConsulInventory, get_node_meta


@mock.patch("consul.base.Consul.Catalog.node")
@mock.patch("consul.base.Consul.Catalog.nodes")
def test_mock(mocked_catalog_nodes, mocked_catalog_node):
    for tagged_address, ip_prefix in [('lan', '10'), ('wan', '20')]:
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
                    "TaggedAddresses": {"lan": "10.0.0.0", "wan": "20.0.0.0"},
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
                    "TaggedAddresses": {"lan": "10.0.0.1", "wan": "20.0.0.1"},
                },
                {
                    "Address": "10.0.0.2",
                    "CreateIndex": 8,
                    "Datacenter": "dc1",
                    "ID": "eb71d55b-a688-cd45-321b-565a318e2600",
                    "Meta": {
                        "consul-network-segment": "",
                        "pseudo_bool": "false",
                        "server_type": "web-server",
                    },
                    "ModifyIndex": 10,
                    "Node": "node3",
                    "TaggedAddresses": {"lan": "10.0.0.2", "wan": "20.0.0.2"},
                },
                {
                    "Address": "10.0.0.3",
                    "CreateIndex": 14,
                    "Datacenter": "dc1",
                    "ID": "97649a1d-281d-4455-a215-020e7d77eedb",
                    "Meta": {
                        "consul-network-segment": "",
                        "cluster": "one-two",
                        "server_type": "postgresql",
                    },
                    "ModifyIndex": 15,
                    "Node": "node4",
                    "TaggedAddresses": {"lan": "10.0.0.3", "wan": "20.0.0.3"},
                },
            ],
        )
        mocked_catalog_node.side_effect = [
            ("2345", {"Node": {}, "Services": {"a": {"Meta": {}, "Tags": ["aa"]}}}),
            ("3456", {"Node": {}, "Services": {"b": {"Meta": {}, "Tags": ["bb"]}}}),
            ("4567", {"Node": {}, "Services": {"c": {"Meta": {}, "Tags": ["cc"]}}}),
            ("5678", {"Node": {}, "Services": {"d-d": {"Meta": {}, "Tags": ["dd"]}}}),
    ]
        c = ConsulInventory()
        c.build_full_inventory(tagged_address=tagged_address)
        print(c.inventory)

        mocked_catalog_nodes.call_count == 1
        mocked_catalog_node.call_count == 3
        assert c.inventory == {
            "_meta": {
                "hostvars": {
                    "node1": {
                        "ansible_host": "{}.0.0.0".format(ip_prefix),
                        "datacenter": "dc1",
                        "server_type": "postgresql",
                        "cluster": 94,
                    },
                    "node2": {
                        "ansible_host": "{}.0.0.1".format(ip_prefix),
                        "datacenter": "dc1",
                        "server_type": "nginx",
                        "pseudo_bool": True,
                    },
                    "node3": {
                        "ansible_host": "{}.0.0.2".format(ip_prefix),
                        "datacenter": "dc1",
                        "server_type": "web-server",
                        "pseudo_bool": False,
                    },
                    "node4": {
                        "ansible_host": "{}.0.0.3".format(ip_prefix),
                        "datacenter": "dc1",
                        "server_type": "postgresql",
                        "cluster": "one-two",
                    },
                }
            },
            "a": {"children": ["a_aa"], "hosts": ["node1"]},
            "a_aa": {"children": [], "hosts": ["node1"]},
            "all": {
                "children": sorted(
                    [
                        "a",
                        "a_aa",
                        "b",
                        "b_bb",
                        "c",
                        "c_cc",
                        "cluster_94",
                        "cluster_one_two",
                        "d_d",
                        "d_d_dd",
                        "dc1",
                        "pseudo_bool",
                        "server_type_nginx",
                        "server_type_postgresql",
                        "server_type_web_server",
                        "ungrouped",
                    ]
                ),
                "hosts": [],
            },
            "b": {"children": ["b_bb"], "hosts": ["node2"]},
            "b_bb": {"children": [], "hosts": ["node2"]},
            "c": {"children": ["c_cc"], "hosts": ["node3"]},
            "c_cc": {"children": [], "hosts": ["node3"]},
            "cluster_94": {"children": [], "hosts": ["node1"]},
            "cluster_one_two": {"children": [], "hosts": ["node4"]},
            "d_d": {"children": ["d_d_dd"], "hosts": ["node4"]},
            "d_d_dd": {"children": [], "hosts": ["node4"]},
            "dc1": {"children": [], "hosts": ["node1", "node2", "node3", "node4"]},
            "pseudo_bool": {"children": [], "hosts": ["node2"]},
            "server_type_web_server": {"children": [], "hosts": ["node3"]},
            "server_type_nginx": {"children": [], "hosts": ["node2"]},
            "server_type_postgresql": {"children": [], "hosts": ["node1", "node4"]},
            "ungrouped": {"children": [], "hosts": []},
        }


def test_get_node_meta_envvar():
    assert get_node_meta() is None
    os.environ["CONSUL_NODE_META"] = '{"foo": "bar"}'
    assert get_node_meta() == {"foo": "bar"}
    for wrong_value in ['{"foo": 1}', '{1: "bar"}', "not a dict"]:
        with pytest.raises(Exception):
            os.environ["CONSUL_NODE_META"] = wrong_value
            get_node_meta()
    del os.environ["CONSUL_NODE_META"]


def test_get_node_meta_configfile():
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(b"[consul_node_meta]\nk1:v1")
        fp.seek(0)
        print(dir(fp))
        print(fp.name)
        path = fp.name
        assert get_node_meta(path) == {"k1": "v1"}
