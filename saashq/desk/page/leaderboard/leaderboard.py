# Copyright (c) 2023-Present, SaasHQ
# License: MIT. See LICENSE
import saashq


@saashq.whitelist()
def get_leaderboard_config():
	leaderboard_config = saashq._dict()
	leaderboard_hooks = saashq.get_hooks("leaderboards")
	for hook in leaderboard_hooks:
		leaderboard_config.update(saashq.get_attr(hook)())

	return leaderboard_config
