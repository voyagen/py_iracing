import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from py_iracing.client import iRacingClient

@pytest.mark.asyncio
@patch('py_iracing.client.Header')
@patch('py_iracing.client.mmap.mmap')
@patch('py_iracing.client.asyncio.to_thread')
@patch('py_iracing.client.ctypes.windll.kernel32.OpenEventW')
@patch('py_iracing.client.aiohttp.ClientSession.get')
async def test_startup_success(mock_get, mock_open_event, mock_to_thread, mock_mmap, mock_header):
    # Arrange
    mock_get.return_value.__aenter__.return_value.text.return_value = 'running:1'
    mock_open_event.return_value = 1
    mock_to_thread.return_value = 0
    mock_mmap.return_value = MagicMock()
    mock_header_instance = mock_header.return_value
    mock_header_instance.version = 2
    mock_header_instance.var_buf = [1]
    ir = iRacingClient()

    # Act
    result = await ir.startup()

    # Assert
    assert result is True
    mock_open_event.assert_called_once()
    mock_to_thread.assert_called_once()
    mock_mmap.assert_called_once()
    mock_header.assert_called_once()

@pytest.mark.asyncio
@patch('py_iracing.client.aiohttp.ClientSession.get')
async def test_startup_sim_not_running(mock_get):
    # Arrange
    mock_get.return_value.__aenter__.return_value.text.return_value = 'running:0'
    ir = iRacingClient()

    # Act
    result = await ir.startup()

    # Assert
    assert result is False