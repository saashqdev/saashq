import saashq
from saashq.utils import get_fullname


def get_leaderboards():
	return {
		"User": {
			"fields": ["points"],
			"method": "saashq.desk.leaderboard.get_energy_point_leaderboard",
			"company_disabled": 1,
			"icon": "users",
		}
	}


@saashq.whitelist()
def get_energy_point_leaderboard(date_range, company=None, field=None, limit=None):
	users = saashq.get_list(
		"User",
		filters={
			"name": ["not in", ["Administrator", "Guest"]],
			"enabled": 1,
			"user_type": ["!=", "Website User"],
		},
		pluck="name",
	)

	filters = [["type", "!=", "Review"], ["user", "in", users]]
	if date_range:
		date_range = saashq.parse_json(date_range)
		filters.append(["creation", "between", [date_range[0], date_range[1]]])
	energy_point_users = saashq.get_all(
		"Energy Point Log",
		fields=["user as name", "sum(points) as value"],
		filters=filters,
		group_by="user",
		order_by="value desc",
	)

	energy_point_users_list = list(map(lambda x: x["name"], energy_point_users))
	for user in users:
		if user not in energy_point_users_list:
			energy_point_users.append({"name": user, "value": 0})

	for user in energy_point_users:
		user_id = user["name"]
		user["name"] = get_fullname(user["name"])
		user["formatted_name"] = f'<a href="/app/user-profile/{user_id}">{get_fullname(user_id)}</a>'

	return energy_point_users
