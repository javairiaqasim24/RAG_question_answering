import json
from unittest.mock import MagicMock, patch

import httpx

from judge import judge_answer


def _mock_response(content: str):
    response = MagicMock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"message": {"content": content}}
    return response


def test_judge_answer_parses_plain_json():
    payload = {"correctness": 1.0, "faithfulness": 0.8, "reasoning": "ok"}
    with patch("judge.httpx.post", return_value=_mock_response(json.dumps(payload))):
        result = judge_answer("Q", "expected", "context", "generated")
    assert result == payload


def test_judge_answer_strips_markdown_code_fence():
    payload = {"correctness": 1.0, "faithfulness": 1.0, "reasoning": "matches"}
    fenced = f"```json\n{json.dumps(payload)}\n```"
    with patch("judge.httpx.post", return_value=_mock_response(fenced)):
        result = judge_answer("Q", "expected", "context", "generated")
    assert result == payload


def test_judge_answer_returns_none_scores_on_unparsable_output():
    with patch("judge.httpx.post", return_value=_mock_response("not json at all")):
        result = judge_answer("Q", "expected", "context", "generated")
    assert result["correctness"] is None
    assert result["faithfulness"] is None


def test_judge_answer_returns_none_scores_on_timeout_instead_of_raising():
    with patch("judge.httpx.post", side_effect=httpx.TimeoutException("timed out")):
        result = judge_answer("Q", "expected", "context", "generated")
    assert result["correctness"] is None
    assert result["faithfulness"] is None
