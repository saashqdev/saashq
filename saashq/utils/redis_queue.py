import redis

import saashq
from saashq.utils import get_wrench_id, random_string


class RedisQueue:
	def __init__(self, conn):
		self.conn = conn

	def add_user(self, username, password=None):
		"""Create or update the user."""
		password = password or self.conn.acl_genpass()
		user_settings = self.get_new_user_settings(username, password)
		is_created = self.conn.acl_setuser(**user_settings)
		return saashq._dict(user_settings) if is_created else {}

	@classmethod
	def get_connection(cls, username=None, password=None):
		conf = saashq.get_site_config()
		if conf.redis_queue_sentinel_enabled:
			from saashq.utils.redis_wrapper import get_sentinel_connection

			sentinels = [tuple(node.split(":")) for node in conf.get("redis_queue_sentinels", [])]
			sentinel = get_sentinel_connection(
				sentinels=sentinels,
				sentinel_username=conf.get("redis_queue_sentinel_username"),
				sentinel_password=conf.get("redis_queue_sentinel_password"),
				master_username=conf.get("redis_queue_master_username", username),
				master_password=conf.get("redis_queue_master_password", password),
			)
			conn = sentinel.master_for(conf.get("redis_queue_master_service"))
			conn.ping()
			return conn
		conn = redis.from_url(conf.redis_queue, username=username, password=password)
		conn.ping()
		return conn

	@classmethod
	def new(cls, username="default", password=None):
		return cls(cls.get_connection(username, password))

	@classmethod
	def set_admin_password(cls, cur_password=None, new_password=None, reset_passwords=False):
		username = "default"
		conn = cls.get_connection(username, cur_password)
		password = "+" + (new_password or conn.acl_genpass())
		conn.acl_setuser(username=username, enabled=True, reset_passwords=reset_passwords, passwords=password)
		return password[1:]

	@classmethod
	def get_new_user_settings(cls, username, password):
		d = {}
		d["username"] = username
		d["passwords"] = "+" + password
		d["reset_keys"] = True
		d["enabled"] = True
		d["keys"] = cls.get_acl_key_rules()
		d["commands"] = cls.get_acl_command_rules()
		return d

	@classmethod
	def get_acl_key_rules(cls, include_key_prefix=False):
		"""FIXME: Find better way"""
		rules = ["rq:[^q]*", "rq:queues", f"rq:queue:{get_wrench_id()}:*"]
		if include_key_prefix:
			return ["~" + pattern for pattern in rules]
		return rules

	@classmethod
	def get_acl_command_rules(cls):
		return ["+@all", "-@admin"]

	@classmethod
	def gen_acl_list(cls, set_admin_password=False):
		"""Generate list of ACL users needed for this branch.

		This list contains default ACL user and the wrench ACL user(used by all sites incase of ACL is enabled).
		"""
		wrench_username = get_wrench_id()
		wrench_user_rules = cls.get_acl_key_rules(include_key_prefix=True) + cls.get_acl_command_rules()
		wrench_user_rule_str = " ".join(wrench_user_rules).strip()
		wrench_user_password = random_string(20)

		default_username = "default"
		_default_user_password = random_string(20) if set_admin_password else ""
		default_user_password = ">" + _default_user_password if _default_user_password else "nopass"

		return [
			f"user {default_username} on {default_user_password} ~* &* +@all",
			f"user {wrench_username} on >{wrench_user_password} {wrench_user_rule_str}",
		], {
			"wrench": (wrench_username, wrench_user_password),
			"default": (default_username, _default_user_password),
		}
