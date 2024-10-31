-- Core Elements to install WNFramework
-- To be called from install.py


--
-- Table structure for table `tabDocField`
--

DROP TABLE IF EXISTS `tabDocField`;
CREATE TABLE `tabDocField` (
  `name` varchar(255) NOT NULL,
  `creation` datetime(6) DEFAULT NULL,
  `modified` datetime(6) DEFAULT NULL,
  `modified_by` varchar(255) DEFAULT NULL,
  `owner` varchar(255) DEFAULT NULL,
  `docstatus` tinyint NOT NULL DEFAULT 0,
  `parent` varchar(255) DEFAULT NULL,
  `parentfield` varchar(255) DEFAULT NULL,
  `parenttype` varchar(255) DEFAULT NULL,
  `idx` int NOT NULL DEFAULT 0,
  `fieldname` varchar(255) DEFAULT NULL,
  `label` varchar(255) DEFAULT NULL,
  `oldfieldname` varchar(255) DEFAULT NULL,
  `fieldtype` varchar(255) DEFAULT NULL,
  `oldfieldtype` varchar(255) DEFAULT NULL,
  `options` text,
  `search_index` tinyint NOT NULL DEFAULT 0,
  `show_dashboard` tinyint NOT NULL DEFAULT 0,
  `hidden` tinyint NOT NULL DEFAULT 0,
  `set_only_once` tinyint NOT NULL DEFAULT 0,
  `allow_in_quick_entry` tinyint NOT NULL DEFAULT 0,
  `print_hide` tinyint NOT NULL DEFAULT 0,
  `report_hide` tinyint NOT NULL DEFAULT 0,
  `reqd` tinyint NOT NULL DEFAULT 0,
  `bold` tinyint NOT NULL DEFAULT 0,
  `in_global_search` tinyint NOT NULL DEFAULT 0,
  `collapsible` tinyint NOT NULL DEFAULT 0,
  `unique` tinyint NOT NULL DEFAULT 0,
  `no_copy` tinyint NOT NULL DEFAULT 0,
  `allow_on_submit` tinyint NOT NULL DEFAULT 0,
  `show_preview_popup` tinyint NOT NULL DEFAULT 0,
  `trigger` varchar(255) DEFAULT NULL,
  `collapsible_depends_on` text,
  `mandatory_depends_on` text,
  `read_only_depends_on` text,
  `depends_on` text,
  `permlevel` int NOT NULL DEFAULT 0,
  `ignore_user_permissions` tinyint NOT NULL DEFAULT 0,
  `width` varchar(255) DEFAULT NULL,
  `print_width` varchar(255) DEFAULT NULL,
  `columns` int NOT NULL DEFAULT 0,
  `default` text,
  `description` text,
  `in_list_view` tinyint NOT NULL DEFAULT 0,
  `fetch_if_empty` tinyint NOT NULL DEFAULT 0,
  `in_filter` tinyint NOT NULL DEFAULT 0,
  `remember_last_selected_value` tinyint NOT NULL DEFAULT 0,
  `ignore_xss_filter` tinyint NOT NULL DEFAULT 0,
  `print_hide_if_no_value` tinyint NOT NULL DEFAULT 0,
  `allow_bulk_edit` tinyint NOT NULL DEFAULT 0,
  `in_standard_filter` tinyint NOT NULL DEFAULT 0,
  `in_preview` tinyint NOT NULL DEFAULT 0,
  `read_only` tinyint NOT NULL DEFAULT 0,
  `precision` varchar(255) DEFAULT NULL,
  `max_height` varchar(10) DEFAULT NULL,
  `length` int NOT NULL DEFAULT 0,
  `translatable` tinyint NOT NULL DEFAULT 0,
  `hide_border` tinyint NOT NULL DEFAULT 0,
  `hide_days` tinyint NOT NULL DEFAULT 0,
  `hide_seconds` tinyint NOT NULL DEFAULT 0,
  PRIMARY KEY (`name`),
  KEY `parent` (`parent`),
  KEY `label` (`label`),
  KEY `fieldtype` (`fieldtype`),
  KEY `fieldname` (`fieldname`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Table structure for table `tabDocPerm`
--

DROP TABLE IF EXISTS `tabDocPerm`;
CREATE TABLE `tabDocPerm` (
  `name` varchar(255) NOT NULL,
  `creation` datetime(6) DEFAULT NULL,
  `modified` datetime(6) DEFAULT NULL,
  `modified_by` varchar(255) DEFAULT NULL,
  `owner` varchar(255) DEFAULT NULL,
  `docstatus` tinyint NOT NULL DEFAULT 0,
  `parent` varchar(255) DEFAULT NULL,
  `parentfield` varchar(255) DEFAULT NULL,
  `parenttype` varchar(255) DEFAULT NULL,
  `idx` int NOT NULL DEFAULT 0,
  `permlevel` int DEFAULT '0',
  `role` varchar(255) DEFAULT NULL,
  `match` varchar(255) DEFAULT NULL,
  `read` tinyint NOT NULL DEFAULT 1,
  `write` tinyint NOT NULL DEFAULT 1,
  `create` tinyint NOT NULL DEFAULT 1,
  `submit` tinyint NOT NULL DEFAULT 0,
  `cancel` tinyint NOT NULL DEFAULT 0,
  `delete` tinyint NOT NULL DEFAULT 1,
  `amend` tinyint NOT NULL DEFAULT 0,
  `report` tinyint NOT NULL DEFAULT 1,
  `export` tinyint NOT NULL DEFAULT 1,
  `import` tinyint NOT NULL DEFAULT 0,
  `share` tinyint NOT NULL DEFAULT 1,
  `print` tinyint NOT NULL DEFAULT 1,
  `email` tinyint NOT NULL DEFAULT 1,
  PRIMARY KEY (`name`),
  KEY `parent` (`parent`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `tabDocType Action`
--

DROP TABLE IF EXISTS `tabDocType Action`;
CREATE TABLE `tabDocType Action` (
  `name` varchar(140) COLLATE utf8mb4_unicode_ci NOT NULL,
  `creation` datetime(6) DEFAULT NULL,
  `modified` datetime(6) DEFAULT NULL,
  `modified_by` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `owner` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `docstatus` tinyint NOT NULL DEFAULT 0,
  `parent` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parentfield` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parenttype` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `idx` int NOT NULL DEFAULT 0,
  `label` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `group` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `action_type` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `action` text COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`name`),
  KEY `parent` (`parent`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

--
-- Table structure for table `tabDocType Link`
--

DROP TABLE IF EXISTS `tabDocType Link`;
CREATE TABLE `tabDocType Link` (
  `name` varchar(140) COLLATE utf8mb4_unicode_ci NOT NULL,
  `creation` datetime(6) DEFAULT NULL,
  `modified` datetime(6) DEFAULT NULL,
  `modified_by` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `owner` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `docstatus` tinyint NOT NULL DEFAULT 0,
  `parent` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parentfield` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `parenttype` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `idx` int NOT NULL DEFAULT 0,
  `group` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `link_doctype` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `link_fieldname` varchar(140) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`name`),
  KEY `parent` (`parent`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci ROW_FORMAT=DYNAMIC;

--
-- Table structure for table `tabDocType`
--

DROP TABLE IF EXISTS `tabDocType`;
CREATE TABLE `tabDocType` (
  `name` varchar(255) NOT NULL,
  `creation` datetime(6) DEFAULT NULL,
  `modified` datetime(6) DEFAULT NULL,
  `modified_by` varchar(255) DEFAULT NULL,
  `owner` varchar(255) DEFAULT NULL,
  `docstatus` tinyint NOT NULL DEFAULT 0,
  `idx` int NOT NULL DEFAULT 0,
  `search_fields` varchar(255) DEFAULT NULL,
  `issingle` tinyint NOT NULL DEFAULT 0,
  `is_virtual` tinyint NOT NULL DEFAULT 0,
  `is_tree` tinyint NOT NULL DEFAULT 0,
  `istable` tinyint NOT NULL DEFAULT 0,
  `editable_grid` tinyint NOT NULL DEFAULT 1,
  `track_changes` tinyint NOT NULL DEFAULT 0,
  `module` varchar(255) DEFAULT NULL,
  `restrict_to_domain` varchar(255) DEFAULT NULL,
  `app` varchar(255) DEFAULT NULL,
  `autoname` varchar(255) DEFAULT NULL,
  `naming_rule` varchar(40) DEFAULT NULL,
  `title_field` varchar(255) DEFAULT NULL,
  `image_field` varchar(255) DEFAULT NULL,
  `timeline_field` varchar(255) DEFAULT NULL,
  `sort_field` varchar(255) DEFAULT NULL,
  `sort_order` varchar(255) DEFAULT NULL,
  `description` text,
  `colour` varchar(255) DEFAULT NULL,
  `read_only` tinyint NOT NULL DEFAULT 0,
  `in_create` tinyint NOT NULL DEFAULT 0,
  `menu_index` int DEFAULT NULL,
  `parent_node` varchar(255) DEFAULT NULL,
  `smallicon` varchar(255) DEFAULT NULL,
  `allow_copy` tinyint NOT NULL DEFAULT 0,
  `allow_rename` tinyint NOT NULL DEFAULT 0,
  `allow_import` tinyint NOT NULL DEFAULT 0,
  `hide_toolbar` tinyint NOT NULL DEFAULT 0,
  `track_seen` tinyint NOT NULL DEFAULT 0,
  `max_attachments` int NOT NULL DEFAULT 0,
  `print_outline` varchar(255) DEFAULT NULL,
  `document_type` varchar(255) DEFAULT NULL,
  `icon` varchar(255) DEFAULT NULL,
  `color` varchar(255) DEFAULT NULL,
  `tag_fields` varchar(255) DEFAULT NULL,
  `subject` varchar(255) DEFAULT NULL,
  `_last_update` varchar(32) DEFAULT NULL,
  `engine` varchar(20) DEFAULT 'InnoDB',
  `default_print_format` varchar(255) DEFAULT NULL,
  `is_submittable` tinyint NOT NULL DEFAULT 0,
  `show_name_in_global_search` tinyint NOT NULL DEFAULT 0,
  `_user_tags` varchar(255) DEFAULT NULL,
  `custom` tinyint NOT NULL DEFAULT 0,
  `beta` tinyint NOT NULL DEFAULT 0,
  `has_web_view` tinyint NOT NULL DEFAULT 0,
  `allow_guest_to_view` tinyint NOT NULL DEFAULT 0,
  `route` varchar(255) DEFAULT NULL,
  `is_published_field` varchar(255) DEFAULT NULL,
  `website_search_field` varchar(255) DEFAULT NULL,
  `email_append_to` tinyint NOT NULL DEFAULT 0,
  `subject_field` varchar(255) DEFAULT NULL,
  `sender_field` varchar(255) DEFAULT NULL,
  `show_title_field_in_link` tinyint NOT NULL DEFAULT 0,
  `migration_hash` varchar(255) DEFAULT NULL,
  `translated_doctype` tinyint NOT NULL DEFAULT 0,
  PRIMARY KEY (`name`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `tabSeries`
--

DROP TABLE IF EXISTS `tabSeries`;
CREATE TABLE `tabSeries` (
  `name` varchar(100),
  `current` int NOT NULL DEFAULT 0,
  PRIMARY KEY(`name`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Table structure for table `tabSessions`
--

DROP TABLE IF EXISTS `tabSessions`;
CREATE TABLE `tabSessions` (
  `user` varchar(255) DEFAULT NULL,
  `sid` varchar(255) DEFAULT NULL,
  `sessiondata` longtext,
  `ipaddress` varchar(16) DEFAULT NULL,
  `lastupdate` datetime(6) DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  KEY `sid` (`sid`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


--
-- Table structure for table `tabSingles`
--

DROP TABLE IF EXISTS `tabSingles`;
CREATE TABLE `tabSingles` (
  `doctype` varchar(255) DEFAULT NULL,
  `field` varchar(255) DEFAULT NULL,
  `value` longtext,
  KEY `singles_doctype_field_index` (`doctype`, `field`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `__Auth`
--

DROP TABLE IF EXISTS `__Auth`;
CREATE TABLE `__Auth` (
	`doctype` VARCHAR(140) NOT NULL,
	`name` VARCHAR(255) NOT NULL,
	`fieldname` VARCHAR(140) NOT NULL,
	`password` TEXT NOT NULL,
	`encrypted` tinyint NOT NULL DEFAULT 0,
	PRIMARY KEY (`doctype`, `name`, `fieldname`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `tabFile`
--

DROP TABLE IF EXISTS `tabFile`;
CREATE TABLE `tabFile` (
  `name` varchar(255) NOT NULL,
  `creation` datetime(6) DEFAULT NULL,
  `modified` datetime(6) DEFAULT NULL,
  `modified_by` varchar(255) DEFAULT NULL,
  `owner` varchar(255) DEFAULT NULL,
  `docstatus` tinyint NOT NULL DEFAULT 0,
  `parent` varchar(255) DEFAULT NULL,
  `parentfield` varchar(255) DEFAULT NULL,
  `parenttype` varchar(255) DEFAULT NULL,
  `idx` int NOT NULL DEFAULT 0,
  `file_name` varchar(255) DEFAULT NULL,
  `file_url` varchar(255) DEFAULT NULL,
  `module` varchar(255) DEFAULT NULL,
  `attached_to_name` varchar(255) DEFAULT NULL,
  `file_size` int NOT NULL DEFAULT 0,
  `attached_to_doctype` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`name`),
  KEY `parent` (`parent`),
  KEY `creation` (`creation`),
  KEY `attached_to_name` (`attached_to_name`),
  KEY `attached_to_doctype` (`attached_to_doctype`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Table structure for table `tabDefaultValue`
--

DROP TABLE IF EXISTS `tabDefaultValue`;
CREATE TABLE `tabDefaultValue` (
  `name` varchar(255) NOT NULL,
  `creation` datetime(6) DEFAULT NULL,
  `modified` datetime(6) DEFAULT NULL,
  `modified_by` varchar(255) DEFAULT NULL,
  `owner` varchar(255) DEFAULT NULL,
  `docstatus` tinyint NOT NULL DEFAULT 0,
  `parent` varchar(255) DEFAULT NULL,
  `parentfield` varchar(255) DEFAULT NULL,
  `parenttype` varchar(255) DEFAULT NULL,
  `idx` int NOT NULL DEFAULT 0,
  `defvalue` text,
  `defkey` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`name`),
  KEY `parent` (`parent`),
  KEY `defaultvalue_parent_defkey_index` (`parent`,`defkey`)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC CHARACTER SET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
