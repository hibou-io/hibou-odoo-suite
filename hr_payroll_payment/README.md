Pay your Payroll
================

Hibou's Payroll Payments modifies, and abstracts, the way that the accounting for payslips is generated.

In stock Odoo 13, journal entries are grouped by account and name, but has no linking to partners.

On the Payroll Journal, you can now select optional journal entry creation with the options:

- Original: Stock Implementation
- Grouped: Lines are grouped by account and partner.  The slip line names will be comma separated in the line name.
- Payslip: Lines are grouped by account and partner, as above, but a single journal entry will be created per payslip.

Adds configuration on how you would pay your employees on the Payroll journal.  e.g. You write a "check" from "Bank"

Adds button on payslip and payslip batch to generate payment for the employee's payable portion.

When paying on a batch, a "Batch Payment" will be generated and linked to the whole payslip run.

Adds Accounting Date field on Batch to use when creating slips with the batch's date.

Adds fiscal position mappings to set a fiscal position on the contract and have payslips map their accounts.

Tested
------

Passes original Payroll Accounting tests and additional ones for gouping behavior.