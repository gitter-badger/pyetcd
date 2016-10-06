#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_pyetcd
----------------------------------

Tests for `pyetcd` module.
"""
import mock as mock

import pytest
from requests import ConnectionError, RequestException
from pyetcd import EtcdException
from pyetcd.client import Client, ClientException


@pytest.fixture
def default_etcd():
    return Client()


@pytest.fixture
def payload_read_success():
    return """
        {
            "action": "get",
            "node": {
                "createdIndex": 28,
                "key": "/foo",
                "modifiedIndex": 28,
                "value": "Hello world"
            }
        }
    """


@pytest.fixture
def payload_write_success():
    return """
        {
            "action": "set",
            "node": {
                "createdIndex": 28,
                "key": "/messsage",
                "modifiedIndex": 28,
                "value": "Hello world"
            },
            "prevNode": {
                "createdIndex": 27,
                "key": "/messsage",
                "modifiedIndex": 27,
                "value": "Hello world"
            }
        }
    """


@pytest.fixture
def payload_write_ttl_success():
    return """
        {
            "action": "set",
            "node": {
                "createdIndex": 5,
                "expiration": "2013-12-04T12:01:21.874888581-08:00",
                "key": "/foo",
                "modifiedIndex": 5,
                "ttl": 5,
                "value": "bar"
            }
        }
    """


@pytest.fixture
def payload_delete_success():
    return """
        {
            "action": "delete",
            "node": {
                "createdIndex": 39,
                "key": "/foo",
                "modifiedIndex": 40
            },
            "prevNode": {
                "createdIndex": 39,
                "key": "/foo",
                "modifiedIndex": 39,
                "value": "aaa"
            }
        }
    """


def test_srv_not_implemented(default_etcd):
    with pytest.raises(ClientException):
        Client(srv_domain='foo.bar')

    with pytest.raises(EtcdException):
        default_etcd.write('/foo', 'bar', ttl=10)


def test_client_defaults(default_etcd):
    assert default_etcd._hosts[0][0] == '127.0.0.1'
    assert default_etcd._hosts[0][1] == 2379
    assert default_etcd._protocol == 'http'
    assert default_etcd._srv_domain is None
    assert default_etcd._version_prefix == 'v2'
    assert default_etcd._urls[0] == 'http://127.0.0.1:2379'


def test_client_hosts_str():
    client = Client(host='10.10.10.10', port=1111)
    assert client._hosts[0][0] == '10.10.10.10'
    assert client._hosts[0][1] == 1111
    assert client._urls[0] == 'http://10.10.10.10:1111'


def test_client_hosts_list():
    client = Client(host=['10.10.10.10',
                          '10.10.10.20'])
    assert client._hosts[0][0] == '10.10.10.10'
    assert client._hosts[0][1] == 2379
    assert client._hosts[1][0] == '10.10.10.20'
    assert client._hosts[1][1] == 2379
    assert client._urls == [
        'http://10.10.10.10:2379',
        'http://10.10.10.20:2379',
    ]


def test_client_hosts_tuples():
    client = Client(host=[('10.10.10.10', 1111),
                          ('10.10.10.20', 2222)])
    assert client._hosts[0][0] == "10.10.10.10"
    assert client._hosts[0][1] == 1111
    assert client._hosts[1][0] == "10.10.10.20"
    assert client._hosts[1][1] == 2222
    assert client._urls == [
        'http://10.10.10.10:1111',
        'http://10.10.10.20:2222',
    ]


def test_client_raises_exception_if_unsupported_protocol():
    Client(protocol='http')
    with pytest.raises(ClientException):
        Client(protocol='foo')


@mock.patch('pyetcd.client.requests')
def test_write(mock_requests, default_etcd, payload_write_success):
    mock_requests.put.return_value = mock.Mock(content=payload_write_success)
    response = default_etcd.write('/messsage', 'Hello world')
    assert response.action == 'set'
    assert response.node['value'] == 'Hello world'


@mock.patch('pyetcd.client.requests')
def test_write_ttl(mock_requests, default_etcd, payload_write_ttl_success):
    mock_requests.put.return_value = mock.Mock(content=payload_write_ttl_success)
    response = default_etcd.write('/messsage', 'bar', ttl=5)
    assert response.action == 'set'
    assert response.node['value'] == 'bar'
    assert response.node['ttl'] == 5


@mock.patch('pyetcd.client.requests')
def test_write_raises_exception(mock_requests, default_etcd):
    mock_requests.put.side_effect = ConnectionError
    with pytest.raises(EtcdException):
        default_etcd.write('/messsage', 'Hello world')


@mock.patch('pyetcd.client.requests')
def test_read(mock_requests, default_etcd, payload_read_success):
    mock_response = mock.Mock()
    mock_response.content = payload_read_success
    mock_requests.get.return_value = mock_response
    response = default_etcd.read('/messsage')
    assert response.action == 'get'
    assert response.node['value'] == 'Hello world'


@mock.patch('pyetcd.client.requests.get')
def test_read_wait(mock_get, default_etcd):
    mock_payload = mock.Mock()
    mock_payload.content = """
            {
                "action": "set",
                "node": {
                    "createdIndex": 30,
                    "key": "/messsage",
                    "modifiedIndex": 30,
                    "value": "foo"
                },
                "prevNode": {
                    "createdIndex": 29,
                    "key": "/messsage",
                    "modifiedIndex": 29,
                    "value": "bar"
                }
            }
        """
    mock_get.return_value = mock_payload
    response = default_etcd.read('/messsage', wait=True)
    assert response.action == 'set'
    assert response.node['value'] == 'foo'
    mock_get.assert_called_once_with(
        'http://127.0.0.1:2379/v2/keys/messsage?wait=true')


@mock.patch('pyetcd.client.requests')
def test_read_raises_exception(mock_requests, default_etcd):
    mock_requests.get.side_effect = ConnectionError
    with pytest.raises(EtcdException):
        default_etcd.read('/messsage')


@mock.patch('pyetcd.client.requests')
def test_read_exception_no_key(mock_requests, default_etcd):
    payload = '{"errorCode":100,"message":"Key not found",' \
              '"cause":"/foo","index":38}'
    mock_response = mock.MagicMock()
    mock_response.content = payload
    mock_requests.get.return_value = mock_response
    with pytest.raises(EtcdException):
        default_etcd.read('/foo')


@mock.patch('pyetcd.client.requests')
def test_read_exception_unknown_error(mock_requests, default_etcd):
    payload = '{"errorCode":1000,"message":"Unknown error",' \
              '"cause":"/foo","index":38}'
    mock_response = mock.MagicMock()
    mock_response.content = payload
    mock_requests.get.return_value = mock_response
    with pytest.raises(EtcdException):
        default_etcd.read('/foo')


@mock.patch('pyetcd.client.requests')
def test_delete(mock_requests, default_etcd, payload_delete_success):
    mock_requests.delete.return_value = mock.MagicMock(
        content=payload_delete_success)
    default_etcd.delete('/foo')
    mock_requests.delete.assert_called_once_with('http://127.0.0.1:2379/v2/keys/foo')


@mock.patch('pyetcd.client.requests')
def test_delete_exception(mock_requests, default_etcd):
    payload = """
    {"errorCode":100,"message":"Key not found","cause":"/foo","index":40}
    """
    mock_requests.delete.return_value = mock.MagicMock(content=payload)
    with pytest.raises(EtcdException):
        default_etcd.delete('/foo')


@mock.patch('pyetcd.client.requests')
def test_read_from_second_host(mock_requests, payload_read_success):
    mock_response = [
        RequestException,
        mock.MagicMock(content=payload_read_success),
        mock.MagicMock(content=payload_read_success)
    ]
    mock_requests.get = mock.MagicMock(side_effect=mock_response)
    client = Client(host=[
        '10.0.1.1',
        '10.0.1.2',
        '10.0.1.3'
    ])
    assert client.read('/foo').node['value'] == 'Hello world'


@mock.patch('pyetcd.client.requests')
def test_read_exception_if_all_hosts_dead(mock_requests):
    mock_response = [
        RequestException,
        RequestException,
        RequestException
    ]
    mock_requests.get = mock.MagicMock(side_effect=mock_response)
    client = Client(host=[
        '10.0.1.1',
        '10.0.1.2',
        '10.0.1.3'
    ])
    with pytest.raises(EtcdException):
        client.read('/foo').node['value']


@mock.patch('pyetcd.client.requests')
def test_write_to_second_host(mock_requests, payload_write_success):
    mock_response = [
        RequestException,
        mock.MagicMock(content=payload_write_success),
        mock.MagicMock(content=payload_write_success)
    ]
    mock_requests.put = mock.MagicMock(side_effect=mock_response)
    client = Client(host=[
        '10.0.1.1',
        '10.0.1.2',
        '10.0.1.3'
    ])
    assert client.write('/message', 'Hello world').node['value'] == 'Hello world'


@mock.patch('pyetcd.client.requests')
def test_delete_from_second_host(mock_requests, payload_delete_success):
    mock_response = [
        RequestException,
        mock.MagicMock(content=payload_delete_success),
        mock.MagicMock(content=payload_delete_success)
    ]
    mock_requests.delete = mock.MagicMock(side_effect=mock_response)
    client = Client(host=[
        '10.0.1.1',
        '10.0.1.2',
        '10.0.1.3'
    ])
    client.delete('/message')
    mock_requests.delete.assert_called_with('http://10.0.1.2:2379/v2/keys/message')
    assert mock_requests.delete.call_count == 2


@mock.patch('pyetcd.client.requests')
def test_read_exception_if_host_down(mock_requests, payload_read_success):
    mock_response = [
        RequestException,
        mock.MagicMock(content=payload_read_success),
        mock.MagicMock(content=payload_read_success)
    ]
    mock_requests.get = mock.MagicMock(side_effect=mock_response)
    client = Client(host=[
        '10.0.1.1',
        '10.0.1.2',
        '10.0.1.3'
    ], allow_reconnect=False)
    with pytest.raises(EtcdException):
        assert client.read('/foo').node['value'] == 'Hello world'


@mock.patch('pyetcd.client.requests')
def test_client_version(mock_requests, default_etcd):
    payload = '{"etcdserver":"2.3.7","etcdcluster":"2.3.0"}'
    mock_response = [
        mock.MagicMock(content=payload)
    ]
    mock_requests.get = mock.MagicMock(side_effect=mock_response)
    assert default_etcd.version() == "2.3.7"


@mock.patch('pyetcd.client.requests')
def test_client_version_server(mock_requests, default_etcd):
    payload = '{"etcdserver":"2.3.7","etcdcluster":"2.3.0"}'
    mock_response = [
        mock.MagicMock(content=payload)
    ]
    mock_requests.get = mock.MagicMock(side_effect=mock_response)
    assert default_etcd.version_server() == "2.3.7"


@mock.patch('pyetcd.client.requests')
def test_client_version_cluster(mock_requests, default_etcd):
    payload = '{"etcdserver":"2.3.7","etcdcluster":"2.3.0"}'
    mock_response = [
        mock.MagicMock(content=payload)
    ]
    mock_requests.get = mock.MagicMock(side_effect=mock_response)
    assert default_etcd.version_cluster() == "2.3.0"


@mock.patch.object(Client, '_request_key')
@mock.patch('pyetcd.client.requests.put')
def test_client_mkdir(mock_put, mock_client, default_etcd):
    mock_payload = mock.Mock()
    mock_payload.content = """
    {
        "action": "set",
        "node": {
            "createdIndex": 12,
            "dir": true,
            "key": "/bar",
            "modifiedIndex": 12
        }
    }
    """
    mock_put.return_value = mock_payload
    default_etcd.mkdir('/foo')
    mock_client.assert_called_once_with('/foo', method='put', data={
        'dir': True,
        'prevExist': False
    })


@mock.patch.object(Client, '_request_call')
def test_client_rmdir(mock_client, default_etcd):
    default_etcd.rmdir('/foo')
    mock_client.assert_called_once_with('/v2/keys/foo?dir=true', method='delete')


@mock.patch.object(Client, '_request_call')
def test_client_rmdir_recursive(mock_client, default_etcd):
    default_etcd.rmdir('/foo', recursive=True)
    mock_client.assert_called_once_with('/v2/keys/foo?dir=true&recursive=true', method='delete')