frappe.ui.form.on("Payroll Entry", {
	onload: function(frm){
		frm.payroll_payable_account_filter = frm.fields_dict["payroll_payable_account"].get_query;
	},

	refresh: function(frm){
		frm.set_query("payroll_payable_account", function(){
			let res = frm.payroll_payable_account_filter.call(frm.fields_dict["payroll_payable_account"]);
			if (frm.doc.employeewise_payroll){
				res.filters["account_type"] = "Payable";
			}
			return res;
		});
	},

	
});
