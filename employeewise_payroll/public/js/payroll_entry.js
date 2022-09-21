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
		frm.trigger("action")
	},
	action: function(frm){
		if (frm.doc.salary_slips_submitted){
			frm.remove_custom_button(__("Submit Salary Slip"));
		}
		if (frm.doc.employeewise_payroll){
			frm.remove_custom_button(__("Make Bank Entry"));
			frm.events.check_existing(frm, function(r){
				if(! r.message["all_exist"]){
						frm.add_custom_button(__("Make Payment Entries"), function(){
							cash_payment(frm.doc.name);
						});
						frm.change_custom_button_type(__("Make Payment Entries"), null, "primary")
				}

				if(r.message["any_exist"]){
					frm.add_custom_button(__("Payment Entries"), function(){
							go_to_payment(frm.doc.name);
					});
				}
			});
		}
	},
	check_existing: function(frm, callback_method){
		frappe.call({
			method: "employeewise_payroll.employeewise_payroll.payroll_entry.payroll_payment_entry_exists",
			args:{
				payroll_entry: frm.doc.name,
			},
			callback: callback_method
		});
	},
});

function go_to_payment(payroll_entry){
	frappe.set_route("List", "Payment Entry", {"payroll_entry": payroll_entry});
}

function cash_payment(payroll_entry){
	frappe.call({
		method: "employeewise_payroll.employeewise_payroll.payroll_entry.cash_payment",
		args:{
			payroll_entry: payroll_entry,
		},
		callback: function(r){
			if (r.message){
				go_to_payment(r.message)
			}
		}
	});
}
