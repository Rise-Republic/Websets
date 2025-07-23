import pytest
import json
from unittest.mock import Mock, patch



@pytest.mark.unit
class TestBaseAgent:
    @pytest.fixture(autouse=True)
    def agent_imports(self):
        from app.agents.base import BaseAgent
        
        class TestAgent(BaseAgent):
            """Concrete implementation for testing."""
            async def execute(self):
                return "test execution"
        
        self.TestAgent = TestAgent
    def test_agent_initialization(self):
        """Test agent initialization."""
        agent = self.TestAgent()
        assert agent.model == "gpt-4"
        assert agent.provider == "openai"
        assert agent._client is None

    def test_agent_initialization_custom(self):
        """Test agent initialization with custom parameters."""
        agent = self.TestAgent(model="gpt-3.5-turbo", provider="anthropic")
        assert agent.model == "gpt-3.5-turbo"
        assert agent.provider == "anthropic"

    @patch('app.agents.base.OpenAI')
    def test_openai_client_creation(self, mock_openai, mock_settings):
        """Test OpenAI client creation."""
        agent = self.TestAgent(provider="openai")
        client = agent.client
        
        mock_openai.assert_called_once_with(api_key="test-openai-key")
        assert client == mock_openai.return_value

    @patch('app.agents.base.Anthropic')
    def test_anthropic_client_creation(self, mock_anthropic, mock_settings):
        """Test Anthropic client creation."""
        agent = self.TestAgent(provider="anthropic")
        client = agent.client
        
        mock_anthropic.assert_called_once_with(api_key="test-anthropic-key-from-fixture")
        assert client == mock_anthropic.return_value

    def test_unsupported_provider_raises_error(self, mock_settings):
        """Test that unsupported provider raises error."""
        agent = self.TestAgent(provider="unsupported")
        
        with pytest.raises(ValueError, match="Unsupported provider: unsupported"):
            _ = agent.client

    def test_parse_json_response_valid(self):
        """Test parsing valid JSON response."""
        agent = self.TestAgent()
        response = '{"key": "value", "number": 42}'
        
        result = agent._parse_json_response(response)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_response_markdown(self):
        """Test parsing JSON from markdown code block."""
        agent = self.TestAgent()
        response = '''Some text before
```json
{"key": "value", "number": 42}
```
Some text after'''
        
        result = agent._parse_json_response(response)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_response_generic_code_block(self):
        """Test parsing JSON from generic code block."""
        agent = self.TestAgent()
        response = '''Some text before
```
{"key": "value", "number": 42}
```
Some text after'''
        
        result = agent._parse_json_response(response)
        assert result == {"key": "value", "number": 42}

    def test_parse_json_response_invalid(self):
        """Test parsing invalid JSON raises error."""
        agent = self.TestAgent()
        response = '{"key": "value", invalid}'
        
        with pytest.raises(ValueError, match="Invalid JSON response from LLM"):
            agent._parse_json_response(response)

    @patch('app.agents.base.OpenAI')
    def test_call_llm_openai_success(self, mock_openai, mock_settings):
        """Test successful OpenAI LLM call."""
        # Setup mock
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        agent = self.TestAgent(provider="openai")
        result = agent._call_llm("Test prompt")

        assert result == "Test response"
        mock_openai.return_value.chat.completions.create.assert_called_once()

    @patch('app.agents.base.Anthropic')
    def test_call_llm_anthropic_success(self, mock_anthropic, mock_settings):
        """Test successful Anthropic LLM call."""
        # Setup mock
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Test response"
        mock_anthropic.return_value.messages.create.return_value = mock_response

        agent = self.TestAgent(provider="anthropic")
        result = agent._call_llm("Test prompt")

        assert result == "Test response"
        mock_anthropic.return_value.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_method(self):
        """Test execute method implementation."""
        agent = self.TestAgent()
        result = await agent.execute()
        assert result == "test execution"