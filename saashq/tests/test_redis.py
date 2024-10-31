import functools
from unittest.mock import patch

import redis

import saashq
from saashq.tests import IntegrationTestCase
from saashq.utils import get_wrench_id
from saashq.utils.background_jobs import get_redis_conn
from saashq.utils.redis_queue import RedisQueue


def version_tuple(version):
	return tuple(map(int, (version.split("."))))


def skip_if_redis_version_lt(version):
	def decorator(func):
		@functools.wraps(func)
		def wrapper(*args, **kwargs):
			conn = get_redis_conn()
			redis_version = conn.execute_command("info")["redis_version"]
			if version_tuple(redis_version) < version_tuple(version):
				return
			return func(*args, **kwargs)

		return wrapper

	return decorator


class TestRedisAuth(IntegrationTestCase):
	@skip_if_redis_version_lt("6.0")
	@patch.dict(saashq.conf, {"wrench_id": "test_wrench", "use_rq_auth": False})
	def test_rq_gen_acllist(self):
		"""Make sure that ACL list is genrated"""
		acl_list = RedisQueue.gen_acl_list()
		self.assertEqual(acl_list[1]["wrench"][0], get_wrench_id())

	@skip_if_redis_version_lt("6.0")
	@patch.dict(saashq.conf, {"wrench_id": "test_wrench", "use_rq_auth": False})
	def test_adding_redis_user(self):
		acl_list = RedisQueue.gen_acl_list()
		username, password = acl_list[1]["wrench"]
		conn = get_redis_conn()

		conn.acl_deluser(username)
		_ = RedisQueue(conn).add_user(username, password)
		self.assertTrue(conn.acl_getuser(username))
		conn.acl_deluser(username)

	@skip_if_redis_version_lt("6.0")
	@patch.dict(saashq.conf, {"wrench_id": "test_wrench", "use_rq_auth": False})
	def test_rq_namespace(self):
		"""Make sure that user can access only their respective namespace."""
		# Current wrench ID
		wrench_id = saashq.conf.get("wrench_id")
		conn = get_redis_conn()
		conn.set("rq:queue:test_wrench1:abc", "value")
		conn.set(f"rq:queue:{wrench_id}:abc", "value")

		# Create new Redis Queue user
		tmp_wrench_id = "test_wrench1"
		username, password = tmp_wrench_id, "password1"
		conn.acl_deluser(username)
		saashq.conf.update({"wrench_id": tmp_wrench_id})
		_ = RedisQueue(conn).add_user(username, password)
		test_wrench1_conn = RedisQueue.get_connection(username, password)

		self.assertEqual(test_wrench1_conn.get("rq:queue:test_wrench1:abc"), b"value")

		# User should not be able to access queues apart from their wrench queues
		with self.assertRaises(redis.exceptions.NoPermissionError):
			test_wrench1_conn.get(f"rq:queue:{wrench_id}:abc")

		saashq.conf.update({"wrench_id": wrench_id})
		conn.acl_deluser(username)
