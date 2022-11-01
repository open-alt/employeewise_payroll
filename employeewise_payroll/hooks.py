from . import __version__ as app_version
from frappe.model.base_document import get_controller
PayrollEntry = get_controller("Payroll Entry")

app_name = "employeewise_payroll"
app_title = "Employeewise Payroll"
app_publisher = "open-alt"
app_description = "Make employee-wise Journal Entry for payroll entry"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "erpnext@open-alt.com"
app_license = "GNU General Public License (v3+)"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/employeewise_payroll/css/employeewise_payroll.css"
# app_include_js = "/assets/employeewise_payroll/js/employeewise_payroll.js"

# include js, css files in header of web template
# web_include_css = "/assets/employeewise_payroll/css/employeewise_payroll.css"
# web_include_js = "/assets/employeewise_payroll/js/employeewise_payroll.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "employeewise_payroll/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Payroll Entry" : "public/js/payroll_entry.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "employeewise_payroll.install.before_install"
# after_install = "employeewise_payroll.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "employeewise_payroll.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Payroll Entry": "employeewise_payroll.employeewise_payroll.payroll_entry.CustomPayrollEntry"
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"employeewise_payroll.tasks.all"
# 	],
# 	"daily": [
# 		"employeewise_payroll.tasks.daily"
# 	],
# 	"hourly": [
# 		"employeewise_payroll.tasks.hourly"
# 	],
# 	"weekly": [
# 		"employeewise_payroll.tasks.weekly"
# 	]
# 	"monthly": [
# 		"employeewise_payroll.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "employeewise_payroll.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "employeewise_payroll.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "employeewise_payroll.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"employeewise_payroll.auth.validate"
# ]
