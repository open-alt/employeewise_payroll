import frappe
from frappe import _
from employeewise_payroll.hooks import PayrollEntry
from erpnext.accounts.utils import get_account_currency
from erpnext.accounts.doctype.journal_entry.journal_entry import get_default_bank_cash_account

from frappe.utils import flt, nowdate, get_link_to_form


class CustomPayrollEntry(PayrollEntry):
	def make_accrual_jv_entry(self, *args, **kwargs):
		if self.employeewise_payroll:
			return self.employeewise_journal_entry(*args, **kwargs)
		else:
			return super().make_accrual_jv_entry(*args, **kwargs)

	def validate_payroll_payable_account(self):
		account_type = frappe.db.get_value("Account", self.payroll_payable_account, "account_type")
		if account_type != "Payable":
			frappe.throw(
				_(
					"Account type must be Payable for payroll payable account {0}, please changed and try again"
				).format(frappe.bold(get_link_to_form("Account", self.payroll_payable_account)))
			)

	def _turn_off_payablle(self):
		account_type = frappe.db.get_value("Account", self.payroll_payable_account, "account_type")
		if account_type == "Payable":
			frappe.db.set_value("Account", self.payroll_payable_account, "account_type", "")

		return account_type

	def _restore_account_type(self, account_type):
		frappe.db.set_value("Account", self.payroll_payable_account, "account_type", account_type)

	def _delete_gl_entries(self, journal_entry):
		gl_enteries = frappe.get_all("GL Entry",
			filters = {
				"voucher_no": journal_entry.name,
				"voucher_type": journal_entry.doctype
		})

		for i in gl_enteries:
			frappe.db.set_value("GL Entry", i["name"], "docstatus", 2)
			frappe.delete_doc("GL Entry", i["name"])

	def _replace_journal_entry(self, jv_name):
		journal_entry = frappe.get_doc("Journal Entry", jv_name)
		self._delete_gl_entries(journal_entry)
		new_journal_entry = journal_entry.as_dict()
		self._delete_journal_entry(journal_entry)
		del new_journal_entry["name"]
		del new_journal_entry["docstatus"]
		return new_journal_entry

	def _delete_journal_entry(self, journal_entry):
		journal_entry.cancel()
		frappe.db.sql(
			"delete from `tabGL Entry` where voucher_type=%s and voucher_no=%s", (journal_entry.doctype, journal_entry.name)
		)
		journal_entry.delete()

	def create_parent_jv(self, *args, **kwargs):
		account_type = self._turn_off_payablle()

		jv_name = super().make_accrual_jv_entry(*args, **kwargs)
		new_journal_entry = self._replace_journal_entry(jv_name)

		self._restore_account_type(account_type)

		new_journal_entry = frappe.get_doc(new_journal_entry)

		return new_journal_entry

	def get_salary_slips(self, journal_entry, precision):
		salary_slips = frappe.get_all("Salary Slip",
			filters = {
				"payroll_entry": self.name,
				"docstatus": 1,
			},
			fields = ["employee", "sum(base_gross_pay) - sum(base_total_deduction) as net_pay"],
			group_by = "employee"
		)

		net_pay_sum = flt(sum(( flt(i["net_pay"]) for i in salary_slips )), precision)

		account = list(
			filter(
				lambda x: x.account == self.payroll_payable_account and \
				flt(x.credit_in_account_currency, precision) == net_pay_sum,
				journal_entry.accounts
			))

		return salary_slips, account

	def save_journal_entry(self, journal_entry):
		journal_entry.save()
		try:
			journal_entry.submit()
			jv_name = journal_entry.name
			self.update_salary_slip_status(jv_name=jv_name)
		except Exception as e:
			if type(e) in (str, list, tuple):
				frappe.msgprint(e)
			raise

		return jv_name

	def employeewise_journal_entry(self, *args, **kwargs):
		journal_entry = self.create_parent_jv(*args, **kwargs)
		precision = frappe.get_precision("Journal Entry Account", "debit_in_account_currency")
		salary_slips, account = self.get_salary_slips(journal_entry, precision)

		if len(account) >= 1:
			account_dict = dict(account[0].as_dict())
			del account_dict["name"]
			del account_dict["docstatus"]

			for i in salary_slips:
				account_dict["party_type"] = "Employee"
				account_dict["party"] = i["employee"]
				account_dict["credit_in_account_currency"] = flt(i["net_pay"], precision)
				journal_entry.append("accounts", account_dict)

			journal_entry.remove(account[0])
		else:
			frappe.throw(_(":-("))

		return self.save_journal_entry(journal_entry)


def get_payment_entry(doc, ref_doc, journal_entry, liability_entry, payment_account, received_amount,
					grand_total=None, outstanding_amount=None, remark=None):
	"""
		doc: frappe.model.document.Document
		journal_entry: journal_entry which need to repay
		liability_entry: one of journal_entry.accounts row thats has liability
	"""

	party_type = liability_entry.get("party_type")
	# party = liability_entry.get("party")
	party_account = liability_entry.get("account")
	party_account_currency = get_account_currency(party_account)
	payment_account_currency = get_account_currency(payment_account)
	payment_type = "Pay" if liability_entry.get("credit_in_account_currency") else "Receive"
	grand_total, outstanding_amount = get_grand_total_and_outstanding_amount(grand_total, outstanding_amount, journal_entry, liability_entry, payment_type)

	# bank or cash
	# payment_account = get_default_bank_cash_account(journal_entry.get("company"), account_type = account_type)

	# paid_amount, received_amount = set_paid_amount_and_received_amount(
	# 	dt, party_account_currency, bank, outstanding_amount, payment_type, bank_amount, doc)

	# paid_amount, received_amount, discount_amount = apply_early_payment_discount(paid_amount, received_amount, doc)

	pe = frappe.new_doc("Payment Entry")
	pe.payment_type = payment_type
	pe.company = journal_entry.company
	pe.cost_center = liability_entry.get("cost_center")
	pe.posting_date = nowdate()
	pe.party_type = party_type
	pe.party = liability_entry.get("party")

	pe.paid_from = party_account if payment_type=="Receive" else payment_account
	pe.paid_to = party_account if payment_type=="Pay" else payment_account
	pe.paid_from_account_currency = party_account_currency \
		if payment_type=="Receive" else payment_account_currency
	pe.paid_to_account_currency = party_account_currency if payment_type=="Pay" else payment_account_currency
	pe.received_amount = received_amount
	pe.paid_amount = received_amount
	#pe.remark= remark

	pe.project = liability_entry.get('project')

	pe.append("references", {
		'reference_doctype': "Journal Entry",
		'reference_name': journal_entry.name,
		'total_amount': grand_total,
		'outstanding_amount': outstanding_amount,
		'allocated_amount': outstanding_amount
	})

	pe.setup_party_account_field()
	pe.set_missing_values()
	pe.set_exchange_rate(ref_doc)
	pe.received_amount = pe.received_amount / (flt(pe.target_exchange_rate) or 1)
	pe.paid_amount = pe.paid_amount / (flt(pe.source_exchange_rate) or 1)

	return pe


def get_grand_total_and_outstanding_amount(grand_total, outstanding_amount, journal_entry, account, payment_type):
	if not grand_total:
		grand_total = (
				account.get("credit_in_account_currency") if payment_type == "Pay"
				else account.get("debit_in_account_currency")
		)

	if not outstanding_amount:
		outstanding_amount = grand_total

	return grand_total, outstanding_amount


def make_payment_entry(salary_slips, payroll_entry, payroll_account, payment_account):
	for ss in salary_slips:
		salary_slip_doc = frappe.get_doc("Salary Slip", ss["name"])
		if not salary_payment_entry_exists(salary_slip_doc, salary_slip_doc.journal_entry, payroll_entry.name):
			journal_entry = frappe.get_doc("Journal Entry", salary_slip_doc.journal_entry)

			if salary_slip_doc.mode_of_payment:
				payment_account = get_default_bank_cash_account(journal_entry.get("company"), account_type=salary_slip_doc.mode_of_payment)
				payment_account = payment_account.get("account")

			received_amount = salary_slip_doc.get("base_net_pay")
			outstanding_amount = salary_slip_doc.get("base_net_pay")
			liability_entry = list(filter(lambda x: x.party == salary_slip_doc.employee and x.account == payroll_account,
							journal_entry.accounts))

			if liability_entry:
				pe = get_payment_entry(
						salary_slip_doc,
						payroll_entry,
						journal_entry,
						liability_entry[0],
						payment_account,
						received_amount,
						outstanding_amount=outstanding_amount
				)
				pe.payroll_entry = payroll_entry.name

				pe.save()
				pe = None

	return


def salary_payment_entry_exists(salary_slip, journal_entry, payroll_entry):
	exist = frappe.get_all("Payment Entry", fields = ["COUNT(*) AS `count`"], filters = {
		"party": salary_slip.employee,
		"payroll_entry": payroll_entry,
		"docstatus": ["<", 2],
	})
	return exist[0]["count"]


@frappe.whitelist()
def payroll_payment_entry_exists(payroll_entry):
	salary_slips = frappe.get_all("Salary Slip",
		filters = {
			"payroll_entry": payroll_entry,
			"docstatus": 1,
			"journal_entry": ["is", "set"]
	})

	all_exist = True
	any_exist = False

	for ss in salary_slips:
		doc = frappe.get_doc("Salary Slip", ss["name"])
		exist = salary_payment_entry_exists(doc, doc.journal_entry, payroll_entry)
		all_exist = all_exist and exist
		any_exist = any_exist or exist

	return {"any_exist" : any_exist, "all_exist": all_exist}


@frappe.whitelist()
def cash_payment(payroll_entry):
	payroll_entry = frappe.get_doc("Payroll Entry", payroll_entry)

	salary_slips = frappe.get_all("Salary Slip",
		filters = {
			"payroll_entry": payroll_entry.name,
			"docstatus": 1,
			"journal_entry": ["is", "set"]
	})

	payroll_account = payroll_entry.payroll_payable_account
	payment_account = payroll_entry.payment_account

	make_payment_entry(salary_slips, payroll_entry, payroll_account, payment_account)
	return payroll_entry.name
