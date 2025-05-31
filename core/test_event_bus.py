import pytest
from core.event_bus import EventBus

@pytest.fixture
def event_bus():
    return EventBus()


def test_send_and_get_state(event_bus):
    event_bus.send_state('test_event', 123)
    assert event_bus.get_state('test_event') == 123

def test_subscribe_and_receive_event(event_bus):
    results = []

    def callback(data):
        results.append(data)

    event_bus.subscribe('event', callback)
    event_bus.send_state('event', 'hello')

    assert results == [None, 'hello']  # None — начальное состояние

# 1 событие 2 колбэка
def test_unsubscribe(event_bus):
    results = []

    def callback(data):
        results.append(data)

    event_bus.subscribe('event', callback)
    event_bus.unsubscribe('event', callback)
    event_bus.send_state('event', 'ignored')

    assert results == [None]  # только вызов при подписке

def test_get_state_for_unknown_event(event_bus):
    # Запрос состояния для несуществующего события возвращает None
    assert event_bus.get_state('unknown_event') is None

# 1 событие 2 колбэка
def test_subscribe_multiple_callbacks(event_bus):
    results1 = []
    results2 = []

    def callback1(data):
        results1.append(data)

    def callback2(data):
        results2.append(data)

    event_bus.subscribe('multi_event', callback1)
    event_bus.subscribe('multi_event', callback2)
    event_bus.send_state('multi_event', 42)

    assert results1 == [None, 42]
    assert results2 == [None, 42]

# отписка несуществующего колбека
def test_unsubscribe_nonexistent_callback(event_bus):
    def dummy_callback(data):
        pass
    event_bus.subscribe('event', dummy_callback)
    event_bus.unsubscribe('event', lambda x: x)
    event_bus.unsubscribe('event', dummy_callback)

def test_subscribe_same_callback_multiple_times(event_bus):
    calls = []

    def cb(data):
        calls.append(data)

    event_bus.subscribe('event', cb)
    event_bus.subscribe('event', cb)  # подписываем дважды

    event_bus.send_state('event', 99)

    assert calls == [None, None, 99, 99]

def test_unsubscribe_removes_only_one_instance(event_bus):
    calls = []

    def cb(data):
        calls.append(data)

    event_bus.subscribe('event', cb)
    event_bus.subscribe('event', cb)  # подписываем дважды
    event_bus.unsubscribe('event', cb)  # отписываем один раз

    event_bus.send_state('event', 'data')

    assert calls == [None, None, 'data']

def test_send_state_with_none_data(event_bus):
    calls = []

    def cb(data):
        calls.append(data)

    event_bus.subscribe('none_event', cb)
    event_bus.send_state('none_event', None)

    assert calls == [None, None]