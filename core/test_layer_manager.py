import pytest
from unittest.mock import Mock
from PIL import Image
from core.layer_manager import LayerManager

@pytest.fixture
def mock_event_bus():
    bus = Mock()
    bus.send_state = Mock()
    bus.subscribe = Mock()
    return bus

@pytest.fixture
def manager(mock_event_bus):
    return LayerManager(mock_event_bus)

def test_init_adds_first_layer(manager, mock_event_bus):
    image = Image.new("RGBA", (100, 100), (255, 0, 0, 255))
    manager.init((image, "Test Layer"))

    assert len(manager.layers) == 1
    assert manager.current_index == 0
    assert manager.get_current().name == "Test Layer"
    mock_event_bus.send_state.assert_any_call("layer_added", manager.get_current())

def test_add_creates_empty_layer(manager):
    manager.background = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    manager.add(True)

    assert len(manager.layers) == 1
    assert manager.get_current().name == "Layer 0"

def test_delete_removes_layer(manager):
    manager.background = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    manager.add(True)
    manager.delete(True)

    assert manager.layers == []
    assert manager.current_index is None

def test_move_layer_up_down(manager):
    manager.background = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    manager.add(True)
    manager.add(True)

    first_name = manager.layers[0].name
    second_name = manager.layers[1].name
    manager.current_index = 0
    manager.move(False)  # move down

    assert manager.layers[1].name == first_name
    assert manager.current_index == 1

def test_select_layer_by_name(manager):
    manager.background = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    manager.add(True)
    manager.layers[0].name = "Layer A"

    manager.select("Layer A")
    assert manager.get_current().name == "Layer A"

def test_change_name(manager):
    manager.background = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    manager.add(True)
    manager.change_name("Renamed Layer")

    assert manager.get_current().name == "Renamed Layer"

def test_delete_all_layers(manager):
    manager.background = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    manager.add(True)
    manager.delete_all(True)

    assert manager.layers == []
    assert manager.current_index is None

def test_update_filter_params(manager):
    manager.background = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
    manager.add(True)
    manager.update_filter_params({'blur': 5})

    assert manager.get_current().filter_params['blur'] == 5