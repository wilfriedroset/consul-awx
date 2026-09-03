import copy
import io
import os
import sys
import tempfile
from contextlib import redirect_stdout
from pprint import pprint as print
from unittest import mock

import consul
import pytest
from consul_awx import ConsulInventory, get_node_meta, get_node_meta_types, main

NODE = {
    "Address": "10.0.0.0",
    "CreateIndex": 7,
    "Datacenter": "dc1",
    "ID": "517ef51b-7ac0-91ff-76f3-8e2ca17e714e",
    "Meta": {"server_type": "postgresql"},
    "ModifyIndex": 12,
    "Node": "node1",
    "TaggedAddresses": {"lan": "10.0.0.0", "wan": "20.0.0.0"},
}

NODE_SERVICES = ("2345", {"Node": {}, "Services": {"a": {"Meta": {}, "Tags": ["aa"]}}})


@mock.patch("consul.base.Consul.Catalog.node")
@mock.patch("consul.base.Consul.Catalog.nodes")
def test_mock(mocked_catalog_nodes, mocked_catalog_node):
    for tagged_address, ip_prefix in [("lan", "10"), ("wan", "20")]:
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
                {
                    "Address": "10.0.0.4",
                    "CreateIndex": 16,
                    "Datacenter": "dc1",
                    "ID": "0f81eddd-3a0f-4168-8493-a06d2b2de2e8",
                    "Meta": {
                        "consul-network-segment": "",
                        "cluster": "1",
                        "server_type": "postgresql",
                    },
                    "ModifyIndex": 17,
                    "Node": "node5",
                    "TaggedAddresses": {"lan": "10.0.0.4", "wan": "20.0.0.4"},
                },
            ],
        )
        mocked_catalog_node.side_effect = [
            ("2345", {"Node": {}, "Services": {"a": {"Meta": {}, "Tags": ["aa"]}}}),
            ("3456", {"Node": {}, "Services": {"b": {"Meta": {}, "Tags": ["bb"]}}}),
            ("4567", {"Node": {}, "Services": {"c": {"Meta": {}, "Tags": ["cc"]}}}),
            ("5678", {"Node": {}, "Services": {"d-d": {"Meta": {}, "Tags": ["dd"]}}}),
            ("6789", {"Node": {}, "Services": {"e": {"Meta": {}, "Tags": ["ee"]}}}),
        ]
        node_meta_types = {"cluster": "str"}
        c = ConsulInventory()
        c.build_full_inventory(
            tagged_address=tagged_address, node_meta_types=node_meta_types
        )
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
                        "cluster": "94",
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
                    "node5": {
                        "ansible_host": "{}.0.0.4".format(ip_prefix),
                        "datacenter": "dc1",
                        "server_type": "postgresql",
                        "cluster": "1",
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
                        "cluster_1",
                        "cluster_94",
                        "cluster_one_two",
                        "d_d",
                        "d_d_dd",
                        "dc1",
                        "e",
                        "e_ee",
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
            "cluster_1": {"children": [], "hosts": ["node5"]},
            "d_d": {"children": ["d_d_dd"], "hosts": ["node4"]},
            "d_d_dd": {"children": [], "hosts": ["node4"]},
            "dc1": {
                "children": [],
                "hosts": ["node1", "node2", "node3", "node4", "node5"],
            },
            "e": {"children": ["e_ee"], "hosts": ["node5"]},
            "e_ee": {"children": [], "hosts": ["node5"]},
            "pseudo_bool": {"children": [], "hosts": ["node2"]},
            "server_type_web_server": {"children": [], "hosts": ["node3"]},
            "server_type_nginx": {"children": [], "hosts": ["node2"]},
            "server_type_postgresql": {
                "children": [],
                "hosts": ["node1", "node4", "node5"],
            },
            "ungrouped": {"children": [], "hosts": []},
        }


@mock.patch("consul.base.Consul.Catalog.node")
@mock.patch("consul.base.Consul.Catalog.nodes")
def test_build_full_inventory_starts_from_a_clean_state(
    mocked_catalog_nodes, mocked_catalog_node
):
    mocked_catalog_nodes.return_value = ("2513", [NODE])
    mocked_catalog_node.return_value = NODE_SERVICES

    c = ConsulInventory()
    c.build_full_inventory()
    first_run = copy.deepcopy(c.inventory)
    c.build_full_inventory()

    assert c.inventory == first_run


def run_main(argv):
    with mock.patch.dict(os.environ, {}, clear=True), mock.patch.object(
        sys, "argv", ["consul_awx.py", "--path", "/nonexistent"] + argv
    ), redirect_stdout(io.StringIO()) as stdout:
        main()
    return stdout.getvalue()


@mock.patch("consul_awx.time.sleep")
@mock.patch("consul.base.Consul.Catalog.node")
@mock.patch("consul.base.Consul.Catalog.nodes")
def test_main_retries_on_consul_server_error(
    mocked_catalog_nodes, mocked_catalog_node, mocked_sleep
):
    mocked_catalog_nodes.side_effect = [
        consul.base.ConsulException(
            "500 rpc error getting client: failed to get conn: "
            "write tcp 127.0.0.1:42434->127.0.0.1:8300: write: connection reset by peer"
        ),
        ("2513", [NODE]),
    ]
    mocked_catalog_node.return_value = NODE_SERVICES

    output = run_main(["--list", "--retry-count", "3"])

    assert mocked_catalog_nodes.call_count == 2
    assert '"node1"' in output


@mock.patch("consul_awx.time.sleep")
@mock.patch("consul.base.Consul.Catalog.nodes")
def test_main_exits_when_retries_are_exhausted(mocked_catalog_nodes, mocked_sleep):
    mocked_catalog_nodes.side_effect = consul.base.ConsulException("500 rpc error")

    with pytest.raises(SystemExit):
        run_main(["--list", "--retry-count", "2"])

    assert mocked_catalog_nodes.call_count == 2
    assert mocked_sleep.call_count == 1


@mock.patch("consul_awx.time.sleep")
@mock.patch("consul.base.Consul.Catalog.nodes")
def test_main_does_not_retry_on_consul_client_error(mocked_catalog_nodes, mocked_sleep):
    mocked_catalog_nodes.side_effect = consul.base.ACLPermissionDenied(
        "Permission denied"
    )

    with pytest.raises(consul.base.ACLPermissionDenied):
        run_main(["--list", "--retry-count", "3"])

    assert mocked_catalog_nodes.call_count == 1
    assert mocked_sleep.call_count == 0


def test_get_node_meta_envvar():
    assert get_node_meta() is None
    os.environ["CONSUL_NODE_META"] = '{"foo": "bar"}'
    assert get_node_meta() == {"foo": "bar"}
    for wrong_value in ['{"foo": 1}', '{1: "bar"}', "not a dict"]:
        with pytest.raises(Exception):
            os.environ["CONSUL_NODE_META"] = wrong_value
            get_node_meta()
    del os.environ["CONSUL_NODE_META"]


def test_get_node_meta_types_envvar():
    assert get_node_meta_types() is None
    os.environ["CONSUL_NODE_META_TYPES"] = '{"foo": "int"}'
    assert get_node_meta_types() == {"foo": "int"}
    for wrong_value in ['{"foo": 1}', '{1: "int"}', "not a dict"]:
        with pytest.raises(Exception):
            os.environ["CONSUL_NODE_META_TYPES"] = wrong_value
            get_node_meta_types()
    del os.environ["CONSUL_NODE_META_TYPES"]


def test_get_node_meta_configfile():
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(b"[consul_node_meta]\nk1:v1")
        fp.seek(0)
        path = fp.name
        assert get_node_meta(path) == {"k1": "v1"}


def test_get_node_meta_types_configfile():
    with tempfile.NamedTemporaryFile() as fp:
        fp.write(b"[consul_node_meta_types]\ncluster:str")
        fp.seek(0)
        path = fp.name
        assert get_node_meta_types(path) == {"cluster": "str"}

