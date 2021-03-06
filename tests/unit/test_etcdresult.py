import mock
import pytest
from pyetcd import EtcdResult, EtcdException, ResponseNode

__author__ = 'aleks'


@pytest.fixture
def payload_self():
    return """
{
    "id": "ce2a822cea30bfca",
    "leaderInfo": {
        "leader": "ce2a822cea30bfca",
        "startTime": "2016-09-19T06:08:51.937661067Z",
        "uptime": "17h5m58.934381551s"
    },
    "name": "default",
    "recvAppendRequestCnt": 0,
    "sendAppendRequestCnt": 0,
    "startTime": "2016-09-19T06:08:51.527241706Z",
    "state": "StateLeader"
}"""


def test_etcd_result_response(payload_self):
    response = mock.Mock()
    response.content = payload_self
    r = EtcdResult(response)
    assert r.__repr__() == payload_self


def test_response_node():
    rn = ResponseNode(key='foo',
                      value='bar',
                      created_index=1,
                      modified_index=2)
    assert rn.key == 'foo'
    assert rn.value == 'bar'
    assert rn.createdIndex == 1
    assert rn.modifiedIndex == 2


@pytest.mark.parametrize('payload', [
    'foo',
    None,
    123
])
def test_exception_invalid_payload(payload):
    with pytest.raises(EtcdException):
        EtcdResult(payload)


@pytest.mark.parametrize('payload,expected', [
    ("""{
    "action": "get",
    "node": {
        "createdIndex": 2,
        "key": "/message",
        "modifiedIndex": 2,
        "value": "Hello world"
    }
}""",
     "get"),
    ("""{
    "node": {
        "createdIndex": 2,
        "key": "/message",
        "modifiedIndex": 2,
        "value": "Hello world"
    }
}""",
     None)
])
def test_action(payload, expected):
    response = mock.Mock()
    response.content = payload
    res = EtcdResult(response)
    assert res.action == expected


@pytest.mark.parametrize('payload,expected', [
    ("""{
    "action": "get",
    "node": {
        "createdIndex": 2,
        "key": "/message",
        "modifiedIndex": 2,
        "value": "Hello world"
    }
}""",
     {
         "createdIndex": 2,
         "key": "/message",
         "modifiedIndex": 2,
         "value": "Hello world"
     })
])
def test_node(payload, expected):
    response = mock.Mock()
    response.content = payload
    res = EtcdResult(response)
    assert res.node == expected


@pytest.mark.parametrize('payload', [
    ("""{
    "cause": "/foo",
    "errorCode": 100,
    "index": 6,
    "message": "Key not found"
}""",
     None)
])
def test_node_exception(payload):
    response = mock.Mock()
    response.content = payload
    with pytest.raises(EtcdException):
        EtcdResult(response)


@pytest.mark.parametrize('payload,expected', [
    ("""{
    "action": "set",
    "node": {
        "createdIndex": 3,
        "key": "/message",
        "modifiedIndex": 3,
        "value": "Hello etcd"
    },
    "prevNode": {
    	"createdIndex": 2,
    	"key": "/message",
    	"value": "Hello world",
    	"modifiedIndex": 2
    }
}""",
     {
         "createdIndex": 2,
         "key": "/message",
         "value": "Hello world",
         "modifiedIndex": 2
     }),
])
def test_prev_node(payload, expected):
    response = mock.Mock()
    response.content = payload
    res = EtcdResult(response)
    assert res.prevNode == expected


def test_version():
    payload = '{"etcdserver":"2.3.7","etcdcluster":"2.3.0"}'
    response = mock.Mock()
    response.content = payload
    res = EtcdResult(response)
    assert res.version_etcdcluster == "2.3.0"
    assert res.version_etcdserver == "2.3.7"


def test_leader():
    payload = """
    {
        "followers": {
            "6e3bd23ae5f1eae0": {
                "counts": {
                    "fail": 0,
                    "success": 745
                },
                "latency": {
                    "average": 0.017039507382550306,
                    "current": 0.000138,
                    "maximum": 1.007649,
                    "minimum": 0,
                    "standardDeviation": 0.05289178277920594
                }
            },
            "a8266ecf031671f3": {
                "counts": {
                    "fail": 0,
                    "success": 735
                },
                "latency": {
                    "average": 0.012124141496598642,
                    "current": 0.000559,
                    "maximum": 0.791547,
                    "minimum": 0,
                    "standardDeviation": 0.04187900156583733
                }
            }
        },
        "leader": "924e2e83e93f2560"
    }
    """
    response = mock.Mock()
    response.content = payload
    res = EtcdResult(response)
    assert res.leader == "924e2e83e93f2560"
    assert res.followers == {
        "6e3bd23ae5f1eae0": {
            "counts": {
                "fail": 0,
                "success": 745
            },
            "latency": {
                "average": 0.017039507382550306,
                "current": 0.000138,
                "maximum": 1.007649,
                "minimum": 0,
                "standardDeviation": 0.05289178277920594
            }
        },
        "a8266ecf031671f3": {
            "counts": {
                "fail": 0,
                "success": 735
            },
            "latency": {
                "average": 0.012124141496598642,
                "current": 0.000559,
                "maximum": 0.791547,
                "minimum": 0,
                "standardDeviation": 0.04187900156583733
            }
        }
    }


def test_selfstats(payload_self):
    response = mock.Mock()
    response.content = payload_self
    res = EtcdResult(response)
    assert res.id == "ce2a822cea30bfca"
    assert res.leaderInfo == {
        "leader": "ce2a822cea30bfca",
        "startTime": "2016-09-19T06:08:51.937661067Z",
        "uptime": "17h5m58.934381551s"
    }
    assert res.name == "default"
    assert res.recvAppendRequestCnt == 0
    assert res.sendAppendRequestCnt == 0
    assert res.startTime == "2016-09-19T06:08:51.527241706Z"
    assert res.state == "StateLeader"

