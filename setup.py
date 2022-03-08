from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in employeewise_payroll/__init__.py
from employeewise_payroll import __version__ as version

setup(
	name="employeewise_payroll",
	version=version,
	description="Make employee-wise Journal Entry for payroll entry",
	author="open-alt",
	author_email="erpnext@open-alt.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
