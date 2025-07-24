import pytest
from unittest.mock import patch

from app.agents.base import BaseAgent
from app.agents import PlannerAgent, DiscoveryAgent


class DummyAgent(BaseAgent):
    async def execute(self, *args, **kwargs):
        pass


def test_escape_and_validate():
    agent = DummyAgent()
    malicious = "Hello {world}`"
    escaped = agent._sanitize_prompt(malicious)
    assert "\\{" in escaped and "\\}" in escaped and "\\`" in escaped

    with pytest.raises(ValueError):
        agent._sanitize_prompt("bad\x01input")


def test_validate_prompt_too_long():
    agent = DummyAgent()
    long_prompt = "a" * 4001
    with pytest.raises(ValueError):
        agent._validate_prompt(long_prompt)


@patch("app.agents.planner.PlannerAgent._parse_json_response")
@patch("app.agents.planner.PlannerAgent._call_llm")
@pytest.mark.asyncio
async def test_planner_sanitizes_user_input(mock_call, mock_parse):
    mock_call.return_value = '{"summary": "ok"}'
    mock_parse.return_value = {"summary": "ok"}
    agent = PlannerAgent()
    await agent.execute("collect {data}`")
    sent = mock_call.call_args[0][0]
    assert "\\{" in sent and "\\}" in sent


@patch("app.agents.discovery.DiscoveryAgent._parse_json_response")
@patch("app.agents.discovery.DiscoveryAgent._call_llm")
@pytest.mark.asyncio
async def test_discovery_sanitizes_user_input(mock_call, mock_parse):
    mock_call.return_value = "[]"
    mock_parse.return_value = []
    agent = DiscoveryAgent()
    strategy = {"method": "search_engine", "keywords": ["bad{evil}`"]}
    plan = {"target_categories": ["cat"], "summary": "info", "expected_data_types": []}
    await agent._search_engine_discovery(strategy, plan)
    sent = mock_call.call_args[0][0]
    assert "\\{" in sent and "\\}" in sent
