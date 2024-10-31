import saashq
from saashq import _
from saashq.database.schema import DBTable, get_definition
from saashq.utils import cint, flt
from saashq.utils.defaults import get_not_null_defaults


class PostgresTable(DBTable):
	def create(self):
		varchar_len = saashq.db.VARCHAR_LEN
		name_column = f"name varchar({varchar_len}) primary key"

		additional_definitions = ""
		# columns
		column_defs = self.get_column_definitions()
		if column_defs:
			additional_definitions += ",\n".join(column_defs)

		# child table columns
		if self.meta.get("istable", default=0):
			if column_defs:
				additional_definitions += ",\n"

			additional_definitions += ",\n".join(
				(
					f"parent varchar({varchar_len})",
					f"parentfield varchar({varchar_len})",
					f"parenttype varchar({varchar_len})",
				)
			)

		# creating sequence(s)
		if not self.meta.issingle and self.meta.autoname == "autoincrement":
			saashq.db.create_sequence(self.doctype, check_not_exists=True)
			name_column = "name bigint primary key"

		elif not self.meta.issingle and self.meta.autoname == "UUID":
			name_column = "name uuid primary key"

		# TODO: set docstatus length
		# create table
		saashq.db.sql(
			f"""create table `{self.table_name}` (
			{name_column},
			creation timestamp(6),
			modified timestamp(6),
			modified_by varchar({varchar_len}),
			owner varchar({varchar_len}),
			docstatus smallint not null default '0',
			idx bigint not null default '0',
			{additional_definitions}
			)""",
		)

		self.create_indexes()
		saashq.db.commit()

	def create_indexes(self):
		create_index_query = ""
		for col in self.columns.values():
			if (
				col.set_index
				and col.fieldtype in saashq.db.type_map
				and saashq.db.type_map.get(col.fieldtype)[0] not in ("text", "longtext")
			):
				create_index_query += (
					f'CREATE INDEX IF NOT EXISTS "{col.fieldname}" ON `{self.table_name}`(`{col.fieldname}`);'
				)
		if create_index_query:
			# nosemgrep
			saashq.db.sql(create_index_query)

	def alter(self):
		for col in self.columns.values():
			col.build_for_alter_table(self.current_columns.get(col.fieldname.lower()))

		query = [f"ADD COLUMN `{col.fieldname}` {col.get_definition()}" for col in self.add_column]

		for col in self.change_type:
			using_clause = ""
			if col.fieldtype in ("Datetime"):
				# The USING option of SET DATA TYPE can actually specify any expression
				# involving the old values of the row
				# read more https://www.postgresql.org/docs/9.1/sql-altertable.html
				using_clause = f"USING {col.fieldname}::timestamp without time zone"
			elif col.fieldtype == "Check":
				using_clause = f"USING {col.fieldname}::smallint"

			query.append(
				"ALTER COLUMN `{}` TYPE {} {}".format(
					col.fieldname,
					get_definition(col.fieldtype, precision=col.precision, length=col.length),
					using_clause,
				)
			)

		if alter_pk := self.alter_primary_key():
			query.append(alter_pk)

		for col in self.set_default:
			if col.fieldname == "name":
				continue

			if col.fieldtype in ("Check", "Int"):
				col_default = cint(col.default)

			elif col.fieldtype in ("Currency", "Float", "Percent"):
				col_default = flt(col.default)

			elif not col.default:
				col_default = "NULL"

			else:
				col_default = f"{saashq.db.escape(col.default)}"

			query.append(f"ALTER COLUMN `{col.fieldname}` SET DEFAULT {col_default}")

		create_contraint_query = ""
		for col in self.add_index:
			# if index key not exists
			create_contraint_query += (
				f'CREATE INDEX IF NOT EXISTS "{col.fieldname}" ON `{self.table_name}`(`{col.fieldname}`);'
			)

		for col in self.add_unique:
			# if index key not exists
			create_contraint_query += 'CREATE UNIQUE INDEX IF NOT EXISTS "unique_{index_name}" ON `{table_name}`(`{field}`);'.format(
				index_name=col.fieldname, table_name=self.table_name, field=col.fieldname
			)

		drop_contraint_query = ""
		for col in self.drop_index:
			# primary key
			if col.fieldname != "name":
				# if index key exists
				drop_contraint_query += f'DROP INDEX IF EXISTS "{col.fieldname}" ;'

		for col in self.drop_unique:
			# primary key
			if col.fieldname != "name":
				# if index key exists
				drop_contraint_query += f'DROP INDEX IF EXISTS "unique_{col.fieldname}" ;'

		change_nullability = []
		for col in self.change_nullability:
			default = col.default or get_not_null_defaults(col.fieldtype)
			if isinstance(default, str):
				default = saashq.db.escape(default)
			change_nullability.append(
				f"ALTER COLUMN \"{col.fieldname}\" {'SET' if col.not_nullable else 'DROP'} NOT NULL"
			)
			change_nullability.append(f'ALTER COLUMN "{col.fieldname}" SET DEFAULT {default}')

			if col.not_nullable:
				try:
					table = saashq.qb.DocType(self.doctype)
					saashq.qb.update(table).set(
						col.fieldname, col.default or get_not_null_defaults(col.fieldtype)
					).where(table[col.fieldname].isnull()).run()
				except Exception:
					print(f"Failed to update data in {self.table_name} for {col.fieldname}")
					raise
		try:
			if query:
				final_alter_query = "ALTER TABLE `{}` {}".format(self.table_name, ", ".join(query))
				# nosemgrep
				saashq.db.sql(final_alter_query)
			if change_nullability:
				# nosemgrep
				saashq.db.sql(f"ALTER TABLE `{self.table_name}` {','.join(change_nullability)}")
			if create_contraint_query:
				# nosemgrep
				saashq.db.sql(create_contraint_query)
			if drop_contraint_query:
				# nosemgrep
				saashq.db.sql(drop_contraint_query)
		except Exception as e:
			# sanitize
			if saashq.db.is_duplicate_fieldname(e):
				saashq.throw(str(e))
			elif saashq.db.is_duplicate_entry(e):
				fieldname = str(e).split("'")[-2]
				saashq.throw(
					_(
						"{0} field cannot be set as unique in {1}, as there are non-unique existing values"
					).format(fieldname, self.table_name)
				)
			else:
				raise e

	def alter_primary_key(self) -> str | None:
		# If there are no values in table allow migrating to UUID from varchar
		autoname = self.meta.autoname
		if autoname == "UUID" and saashq.db.get_column_type(self.doctype, "name") != "uuid":
			if not saashq.db.get_value(self.doctype, {}, order_by=None):
				return "alter column `name` TYPE uuid USING name::uuid"
			else:
				saashq.throw(
					_("Primary key of doctype {0} can not be changed as there are existing values.").format(
						self.doctype
					)
				)

		# Reverting from UUID to VARCHAR
		if autoname != "UUID" and saashq.db.get_column_type(self.doctype, "name") == "uuid":
			return f"alter column `name` TYPE varchar({saashq.db.VARCHAR_LEN})"
