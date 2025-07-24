import pytest
from unittest.mock import patch

from app.agents import PlannerAgent, DiscoveryAgent


@pytest.mark.unit
@patch("app.agents.planner.PlannerAgent._parse_json_response")
@patch("app.agents.planner.PlannerAgent._call_llm")
@pytest.mark.asyncio
async def test_planner_execute_parses_llm_result(mock_call, mock_parse):
    mock_call.return_value = '{"summary": "test"}'
    mock_parse.return_value = {"summary": "test"}
    agent = PlannerAgent()
    result = await agent.execute("collect data")
    mock_call.assert_called_once()
    mock_parse.assert_called_once()
    assert result == {"summary": "test"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_discovery_prioritize_urls_limits_and_sorts():
    agent = DiscoveryAgent()
    urls = [
        {"url": "a", "priority": 5},
        {"url": "b", "priority": 1},
        {"url": "a", "priority": 3},
    ]
    plan = {"estimated_urls": 1}
    result = await agent._prioritize_urls(urls, plan)
    assert result == [{"url": "b", "priority": 1}]
