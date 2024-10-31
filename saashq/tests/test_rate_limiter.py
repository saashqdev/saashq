# Copyleft (l) 2023-Present, SaasHQ
# License: MIT. See LICENSE

import time

from werkzeug.wrappers import Response

import saashq
import saashq.rate_limiter
from saashq.rate_limiter import RateLimiter
from saashq.tests import IntegrationTestCase
from saashq.utils import cint


class TestRateLimiter(IntegrationTestCase):
	def test_apply_with_limit(self):
		saashq.conf.rate_limit = {"window": 86400, "limit": 1}
		saashq.rate_limiter.apply()

		self.assertTrue(hasattr(saashq.local, "rate_limiter"))
		self.assertIsInstance(saashq.local.rate_limiter, RateLimiter)

		saashq.cache.delete(saashq.local.rate_limiter.key)
		delattr(saashq.local, "rate_limiter")

	def test_apply_without_limit(self):
		saashq.conf.rate_limit = None
		saashq.rate_limiter.apply()

		self.assertFalse(hasattr(saashq.local, "rate_limiter"))

	def test_respond_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		saashq.conf.rate_limit = {"window": 86400, "limit": 0.01}
		self.assertRaises(saashq.TooManyRequestsError, saashq.rate_limiter.apply)
		saashq.rate_limiter.update()

		response = saashq.rate_limiter.respond()

		self.assertIsInstance(response, Response)
		self.assertEqual(response.status_code, 429)

		headers = saashq.local.rate_limiter.headers()
		self.assertIn("Retry-After", headers)
		self.assertNotIn("X-RateLimit-Used", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertIn("X-RateLimit-Limit", headers)
		self.assertIn("X-RateLimit-Remaining", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"]) <= 86400)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 0)

		saashq.cache.delete(limiter.key)
		saashq.cache.delete(saashq.local.rate_limiter.key)
		delattr(saashq.local, "rate_limiter")

	def test_respond_under_limit(self):
		saashq.conf.rate_limit = {"window": 86400, "limit": 0.01}
		saashq.rate_limiter.apply()
		saashq.rate_limiter.update()
		response = saashq.rate_limiter.respond()
		self.assertEqual(response, None)

		saashq.cache.delete(saashq.local.rate_limiter.key)
		delattr(saashq.local, "rate_limiter")

	def test_headers_under_limit(self):
		saashq.conf.rate_limit = {"window": 86400, "limit": 0.01}
		saashq.rate_limiter.apply()
		saashq.rate_limiter.update()
		headers = saashq.local.rate_limiter.headers()
		self.assertNotIn("Retry-After", headers)
		self.assertIn("X-RateLimit-Reset", headers)
		self.assertTrue(int(headers["X-RateLimit-Reset"] < 86400))
		self.assertEqual(int(headers["X-RateLimit-Used"]), saashq.local.rate_limiter.duration)
		self.assertEqual(int(headers["X-RateLimit-Limit"]), 10000)
		self.assertEqual(int(headers["X-RateLimit-Remaining"]), 10000)

		saashq.cache.delete(saashq.local.rate_limiter.key)
		delattr(saashq.local, "rate_limiter")

	def test_reject_over_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.01, 86400)
		self.assertRaises(saashq.TooManyRequestsError, limiter.apply)

		saashq.cache.delete(limiter.key)

	def test_do_not_reject_under_limit(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		limiter = RateLimiter(0.02, 86400)
		self.assertEqual(limiter.apply(), None)

		saashq.cache.delete(limiter.key)

	def test_update_method(self):
		limiter = RateLimiter(0.01, 86400)
		time.sleep(0.01)
		limiter.update()

		self.assertEqual(limiter.duration, cint(saashq.cache.get(limiter.key)))

		saashq.cache.delete(limiter.key)
