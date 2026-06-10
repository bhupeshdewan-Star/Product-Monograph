"""
Test Suite for Global Audit API

Run tests with:
    python -m pytest test_global_audit_api.py -v
    python test_global_audit_api.py
"""

import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from global_audit_api import (
    GlobalAuditAPI,
    AIProviderConfig,
    A11YCheckRequest,
    AuditBuilderRequest,
    AuditRunRequest,
    APIResponse,
    AuditCache,
    RateLimiter,
    create_api,
)


# ============================================================================
# TEST: AIProviderConfig
# ============================================================================

class TestAIProviderConfig(unittest.TestCase):
    """Test AI Provider Configuration"""

    def test_create_anthropic_config(self):
        """Test creating Anthropic provider config"""
        config = AIProviderConfig(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            api_key="sk-ant-test"
        )
        self.assertEqual(config.provider, "anthropic")
        self.assertEqual(config.model, "claude-3-5-sonnet-20241022")
        self.assertEqual(config.api_key, "sk-ant-test")

    def test_config_to_dict(self):
        """Test converting config to dict"""
        config = AIProviderConfig(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            api_key="sk-ant-test",
            temperature=0.5
        )
        config_dict = config.to_dict()
        self.assertEqual(config_dict['provider'], "anthropic")
        self.assertEqual(config_dict['temperature'], 0.5)
        self.assertEqual(config_dict['api_key'], "***")  # Should be masked

    def test_default_values(self):
        """Test default configuration values"""
        config = AIProviderConfig(
            provider="anthropic",
            model="test-model"
        )
        self.assertEqual(config.temperature, 0.7)
        self.assertEqual(config.max_tokens, 4096)


# ============================================================================
# TEST: Request Validation
# ============================================================================

class TestRequestValidation(unittest.TestCase):
    """Test request validation"""

    def test_a11y_check_request_url_required(self):
        """Test that url or html_content is required"""
        request = A11YCheckRequest()
        valid, error = request.validate()
        self.assertFalse(valid)
        self.assertIsNotNone(error)

    def test_a11y_check_request_valid_url(self):
        """Test valid URL request"""
        request = A11YCheckRequest(url="https://example.com")
        valid, error = request.validate()
        self.assertTrue(valid)

    def test_a11y_check_request_valid_html(self):
        """Test valid HTML request"""
        request = A11YCheckRequest(html_content="<html><body>Test</body></html>")
        valid, error = request.validate()
        self.assertTrue(valid)

    def test_a11y_check_request_invalid_wcag_level(self):
        """Test invalid WCAG level"""
        request = A11YCheckRequest(
            url="https://example.com",
            wcag_level="INVALID"
        )
        valid, error = request.validate()
        self.assertFalse(valid)

    def test_audit_builder_request_url_required(self):
        """Test checklist URL required"""
        request = AuditBuilderRequest(checklist_url="")
        valid, error = request.validate()
        self.assertFalse(valid)

    def test_audit_builder_request_valid_url(self):
        """Test valid checklist URL"""
        request = AuditBuilderRequest(checklist_url="https://example.com/checklist")
        valid, error = request.validate()
        self.assertTrue(valid)

    def test_audit_run_request_target_required(self):
        """Test target required"""
        request = AuditRunRequest(target="", agent_schema={})
        valid, error = request.validate()
        self.assertFalse(valid)

    def test_audit_run_request_schema_required(self):
        """Test agent schema required"""
        request = AuditRunRequest(target="https://example.com", agent_schema=None)
        valid, error = request.validate()
        self.assertFalse(valid)


# ============================================================================
# TEST: API Response
# ============================================================================

class TestAPIResponse(unittest.TestCase):
    """Test API response handling"""

    def test_success_response(self):
        """Test successful response"""
        response = APIResponse(
            success=True,
            data={"score": 95},
            message="Test successful"
        )
        self.assertTrue(response.success)
        self.assertIsNone(response.error)

    def test_error_response(self):
        """Test error response"""
        response = APIResponse(
            success=False,
            data=None,
            error="Test error"
        )
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)

    def test_response_to_dict(self):
        """Test converting response to dict"""
        response = APIResponse(
            success=True,
            data={"test": "data"},
            message="Test"
        )
        response_dict = response.to_dict()
        self.assertEqual(response_dict['success'], True)
        self.assertEqual(response_dict['data'], {"test": "data"})

    def test_response_to_json(self):
        """Test converting response to JSON"""
        response = APIResponse(
            success=True,
            data={"test": "data"}
        )
        json_str = response.to_json()
        parsed = json.loads(json_str)
        self.assertTrue(parsed['success'])


# ============================================================================
# TEST: Cache Layer
# ============================================================================

class TestAuditCache(unittest.TestCase):
    """Test cache layer"""

    def setUp(self):
        self.cache = AuditCache(ttl_seconds=10)

    def test_cache_set_and_get(self):
        """Test caching data"""
        self.cache.set("test_key", {"data": "value"})
        result = self.cache.get("test_key")
        self.assertIsNotNone(result)
        self.assertEqual(result["data"], "value")

    def test_cache_miss(self):
        """Test cache miss"""
        result = self.cache.get("nonexistent")
        self.assertIsNone(result)

    def test_cache_delete(self):
        """Test deleting from cache"""
        self.cache.set("test_key", {"data": "value"})
        self.cache.delete("test_key")
        result = self.cache.get("test_key")
        self.assertIsNone(result)

    def test_cache_clear(self):
        """Test clearing cache"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.clear()
        self.assertIsNone(self.cache.get("key1"))
        self.assertIsNone(self.cache.get("key2"))

    def test_cache_stats(self):
        """Test cache statistics"""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        stats = self.cache.get_stats()
        self.assertEqual(stats['total_entries'], 2)
        self.assertEqual(stats['valid_entries'], 2)


# ============================================================================
# TEST: Rate Limiter
# ============================================================================

class TestRateLimiter(unittest.TestCase):
    """Test rate limiting"""

    def setUp(self):
        self.limiter = RateLimiter(max_requests=5, window_seconds=60)

    def test_rate_limit_allowed(self):
        """Test allowing requests under limit"""
        for i in range(5):
            allowed = self.limiter.is_allowed("client1")
            self.assertTrue(allowed)

    def test_rate_limit_exceeded(self):
        """Test exceeding rate limit"""
        for i in range(5):
            self.limiter.is_allowed("client1")

        # 6th request should be denied
        allowed = self.limiter.is_allowed("client1")
        self.assertFalse(allowed)

    def test_rate_limit_per_client(self):
        """Test rate limiting is per client"""
        for i in range(5):
            self.limiter.is_allowed("client1")

        # client2 should be allowed
        allowed = self.limiter.is_allowed("client2")
        self.assertTrue(allowed)

    def test_rate_limit_status(self):
        """Test getting rate limit status"""
        self.limiter.is_allowed("client1")
        self.limiter.is_allowed("client1")

        status = self.limiter.get_status("client1")
        self.assertEqual(status['requests_used'], 2)
        self.assertEqual(status['requests_limit'], 5)
        self.assertEqual(status['requests_remaining'], 3)


# ============================================================================
# TEST: Global Audit API
# ============================================================================

class TestGlobalAuditAPI(unittest.TestCase):
    """Test Global Audit API"""

    def setUp(self):
        # Create temporary directories
        self.temp_dir = tempfile.TemporaryDirectory()
        self.agents_dir = Path(self.temp_dir.name) / "agents"
        self.cache_dir = Path(self.temp_dir.name) / "cache"
        self.agents_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

        self.api = GlobalAuditAPI(
            agents_dir=str(self.agents_dir),
            cache_dir=str(self.cache_dir),
            enable_cache=True,
            cache_ttl=3600,
            rate_limit_requests=100,
            rate_limit_window=60,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_api_initialization(self):
        """Test API initialization"""
        self.assertIsNotNone(self.api)
        self.assertTrue(self.agents_dir.exists())
        self.assertTrue(self.cache_dir.exists())

    def test_list_agents_empty(self):
        """Test listing agents when empty"""
        response = self.api.list_agents()
        self.assertTrue(response.success)
        self.assertEqual(response.data['total_count'], 0)

    def test_save_and_get_agent(self):
        """Test saving and retrieving agent"""
        agent_schema = {
            "name": "test_agent",
            "version": "1.0.0",
            "checks": []
        }

        # Save agent
        save_response = self.api.save_agent(
            name="test_agent",
            schema=agent_schema
        )
        self.assertTrue(save_response.success)

        # Get agent
        get_response = self.api.get_agent("test_agent")
        self.assertTrue(get_response.success)
        self.assertEqual(get_response.data['name'], "test_agent")

    def test_delete_agent(self):
        """Test deleting agent"""
        agent_schema = {
            "name": "test_agent",
            "version": "1.0.0"
        }

        # Save agent
        self.api.save_agent("test_agent", agent_schema)

        # Delete agent
        delete_response = self.api.delete_agent("test_agent")
        self.assertTrue(delete_response.success)

        # Verify deleted
        get_response = self.api.get_agent("test_agent")
        self.assertFalse(get_response.success)

    def test_get_nonexistent_agent(self):
        """Test getting non-existent agent"""
        response = self.api.get_agent("nonexistent")
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)

    def test_cache_stats(self):
        """Test getting cache stats"""
        response = self.api.get_cache_stats()
        self.assertTrue(response.success)
        self.assertIn('total_entries', response.data)

    def test_clear_cache(self):
        """Test clearing cache"""
        response = self.api.clear_cache()
        self.assertTrue(response.success)

    def test_rate_limit_status(self):
        """Test getting rate limit status"""
        response = self.api.get_rate_limit_status("test_client")
        self.assertTrue(response.success)
        self.assertIn('requests_remaining', response.data)

    @patch('global_audit_api.A11YChecker')
    def test_check_url_not_available(self, mock_checker):
        """Test check_url when checker not available"""
        api = GlobalAuditAPI(enable_cache=False)
        api.a11y_checker = None

        response = api.check_url("https://example.com")
        self.assertFalse(response.success)
        self.assertIn("not available", response.error.lower())


# ============================================================================
# TEST: Factory Functions
# ============================================================================

class TestFactoryFunctions(unittest.TestCase):
    """Test factory functions"""

    def test_create_api(self):
        """Test create_api factory"""
        api = create_api()
        self.assertIsNotNone(api)
        self.assertIsInstance(api, GlobalAuditAPI)

    def test_create_api_with_options(self):
        """Test create_api with custom options"""
        with tempfile.TemporaryDirectory() as temp_dir:
            api = create_api(
                agents_dir=f"{temp_dir}/agents",
                cache_dir=f"{temp_dir}/cache",
                enable_cache=True,
                cache_ttl=1800,
                rate_limit_requests=50,
                rate_limit_window=30
            )
            self.assertIsNotNone(api)


# ============================================================================
# TEST: Integration Tests
# ============================================================================

class TestIntegration(unittest.TestCase):
    """Integration tests"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.api = GlobalAuditAPI(
            agents_dir=f"{self.temp_dir.name}/agents",
            cache_dir=f"{self.temp_dir.name}/cache",
            enable_cache=True,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_agent_workflow(self):
        """Test complete agent workflow"""
        agent_schema = {
            "name": "integration_test_agent",
            "version": "1.0.0",
            "checks": [
                {
                    "id": "check_001",
                    "name": "Test Check",
                    "severity": "high"
                }
            ]
        }

        # Create agent
        save_resp = self.api.save_agent("integration_agent", agent_schema)
        self.assertTrue(save_resp.success)

        # List agents
        list_resp = self.api.list_agents()
        self.assertTrue(list_resp.success)
        self.assertEqual(list_resp.data['total_count'], 1)

        # Get agent
        get_resp = self.api.get_agent("integration_agent")
        self.assertTrue(get_resp.success)

        # Delete agent
        del_resp = self.api.delete_agent("integration_agent")
        self.assertTrue(del_resp.success)

        # Verify deleted
        list_resp = self.api.list_agents()
        self.assertEqual(list_resp.data['total_count'], 0)


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestAIProviderConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestRequestValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIResponse))
    suite.addTests(loader.loadTestsFromTestCase(TestAuditCache))
    suite.addTests(loader.loadTestsFromTestCase(TestRateLimiter))
    suite.addTests(loader.loadTestsFromTestCase(TestGlobalAuditAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestFactoryFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
