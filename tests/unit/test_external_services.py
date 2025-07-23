import pytest
from unittest.mock import Mock, patch, AsyncMock
@pytest.mark.unit
class TestExternalServiceMocking:
    @pytest.fixture(autouse=True)
    def agent_imports(self):
        from app.agents.base import BaseAgent

        class MockAgent(BaseAgent):
            """Mock agent for testing external service integration."""
            async def execute(self):
                return "mock execution"
        
        self.MockAgent = MockAgent
    
    @patch('app.agents.base.OpenAI')
    def test_openai_api_mock(self, mock_openai_class, mock_settings):
        """Test OpenAI API mocking."""
        # Setup mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Mocked OpenAI response"

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_client

        # Test the mock
        agent = self.MockAgent(provider="openai")
        result = agent._call_llm("test prompt")

        assert result == "Mocked OpenAI response"
        mock_client.chat.completions.create.assert_called_once()

    @patch('anthropic.Anthropic')
    def test_anthropic_api_mock(self, mock_anthropic_class, mock_settings):
        """Test Anthropic API mocking."""
        # Setup mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Mocked Anthropic response"
        
        mock_client = Mock()
        mock_client.messages.create.return_value = mock_response
        mock_anthropic_class.return_value = mock_client
        
        # Set required setting
        mock_settings.anthropic_api_key = "test-anthropic-key"
        
        # Test the mock
        agent = self.MockAgent(provider="anthropic")
        result = agent._call_llm("test prompt")
        
        assert result == "Mocked Anthropic response"
        mock_client.messages.create.assert_called_once()

    def test_redis_mock(self, mock_redis):
        """Test Redis mocking for caching/session storage."""
        # The mock_redis fixture from conftest.py patches redis.from_url
        # and returns a MagicMock instance.
        import redis
        redis_client = redis.from_url("redis://dummy")

        # Configure the mock's methods
        redis_client.get.return_value = b'cached_value'
        redis_client.set.return_value = True
        
        # Simulate using Redis
        redis_client.set("key", "value")
        result = redis_client.get("key")
        
        assert result == b'cached_value'
        redis_client.set.assert_called_with("key", "value")
        redis_client.get.assert_called_with("key")

    @patch('httpx.AsyncClient')
    async def test_external_http_api_mock(self, mock_httpx_client):
        """Test mocking external HTTP API calls."""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": "test"}
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        
        # Simulate API call
        async with mock_httpx_client() as client:
            response = await client.get("https://api.example.com/data")
            
        assert response.status_code == 200
        assert response.json() == {"status": "success", "data": "test"}

    @patch('playwright.async_api.async_playwright')
    async def test_browser_automation_mock(self, mock_playwright):
        """Test mocking Playwright browser automation."""
        # Setup mock browser and page
        mock_page = AsyncMock()
        mock_page.goto = AsyncMock()
        mock_page.content.return_value = "<html><body>Test content</body></html>"
        
        mock_browser = AsyncMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_context = AsyncMock()
        mock_context.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__aenter__.return_value = mock_context
        
        # Simulate browser automation
        async with mock_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto("https://example.com")
            content = await page.content()
            
        assert content == "<html><body>Test content</body></html>"
        mock_page.goto.assert_called_with("https://example.com")


@pytest.fixture
def mock_external_services():
    """Comprehensive fixture for mocking all external services."""
    with patch.multiple(
        'app.agents.base',
        OpenAI=Mock(),
        Anthropic=Mock()
    ), patch('redis.Redis'), patch('httpx.AsyncClient'), patch('playwright.async_api.async_playwright'):
        yield