from unittest.mock import MagicMock, patch

from shellsage.store import query_translation


def test_query_translation_hybrid():
    mock_client = MagicMock()

    # Mock client.search to return a semantic result
    mock_search_result = MagicMock()
    mock_search_result.score = 0.9
    mock_search_result.payload = {
        "bash_cmd": "ls -la",
        "translated_cmd": "Get-ChildItem -Force",
        "shell": "powershell",
        "os": "windows",
        "project_type": "python",
    }
    mock_client.search.return_value = [mock_search_result]

    # Mock client.scroll to return a lexical record
    mock_record = MagicMock()
    mock_record.payload = {
        "bash_cmd": "ls -l",
        "translated_cmd": "Get-ChildItem -Force",
        "shell": "powershell",
        "os": "windows",
        "project_type": "python",
    }
    mock_client.scroll.return_value = ([mock_record], None)

    with patch("shellsage.store._client", return_value=mock_client):
        hits = query_translation(
            bash_cmd="ls",
            embedding=[0.1] * 384,
            shell="powershell",
            os_name="windows",
            project_type="python",
        )
        # Verify the RRF fuses both candidates successfully
        assert len(hits) >= 2
        assert hits[0]["bash_cmd"] in ("ls -la", "ls -l")
        assert hits[1]["bash_cmd"] in ("ls -la", "ls -l")
