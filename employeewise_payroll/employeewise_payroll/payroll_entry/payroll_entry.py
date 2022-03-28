import frappe
from frappe import _
from erpnext.payroll.doctype.payroll_entry.payroll_entry import PayrollEntry

from frappe.utils import flt
import erpnext


class CustomPayrollEntry(PayrollEntry):
	def make_accrual_jv_entry(self, *args, **kwargs):
		if self.employeewise_payroll:
			return self.employeewise_journal_entry(*args, **kwargs)
		else:
			return super().make_accrual_jv_entry(*args, **kwargs)


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
		journal_entry.cancel()
		journal_entry.delete()
		del new_journal_entry["name"]
		del new_journal_entry["docstatus"]
		return new_journal_entry


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
