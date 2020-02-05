# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models

ACCOUNT_PAYABLE = '211000'
SALARY_EXPENSES = '630000'


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    def _load(self, sale_tax_rate, purchase_tax_rate, company):
        """
        Override to configure payroll accounting data as well as accounting data.
        """
        res = super()._load(sale_tax_rate, purchase_tax_rate, company)
        self._us_configure_payroll_account_data(company)
        return res

    def _us_configure_payroll_account_data(self, companies, ap_code=ACCOUNT_PAYABLE, salary_exp_code=SALARY_EXPENSES):
        account_codes = (
            ap_code,
            salary_exp_code,
        )
        us_structures = self.env['hr.payroll.structure'].search([('country_id', '=', self.env.ref('base.us').id)])
        journal_field_id = self.env['ir.model.fields'].search([
            ('model', '=', 'hr.payroll.structure'),
            ('name', '=', 'journal_id')], limit=1)

        for company in companies:
            self = self.with_context({'allowed_company_ids': company.ids})
            accounts = {
                code: self.env['account.account'].search(
                    [('company_id', '=', company.id), ('code', '=like', '%s%%' % code)], limit=1)
                for code in account_codes
            }

            def set_rule_accounts(code, account_debit, account_credit):
                rule_domain = [
                    ('struct_id', 'in', us_structures.ids),
                    ('code', '=like', code),
                ]
                rules = self.env['hr.salary.rule'].search(rule_domain)
                values = {}
                if account_debit:
                    values['account_debit'] = account_debit.id
                if account_credit:
                    values['account_credit'] = account_credit.id
                rules.write(values)

            journal = self.env['account.journal'].search([
                ('code', '=', 'PAYR'),
                ('name', '=', 'Payroll'),
                ('company_id', '=', company.id),
            ])
            if journal:
                if not journal.default_credit_account_id:
                    journal.default_credit_account_id = accounts[SALARY_EXPENSES].id
                if not journal.default_debit_account_id:
                    journal.default_debit_account_id = accounts[SALARY_EXPENSES].id
                if hasattr(journal, 'payroll_entry_type'):
                    journal.payroll_entry_type = 'grouped'
            else:
                journal = self.env['account.journal'].create({
                    'name': 'Payroll',
                    'code': 'PAYR',
                    'type': 'general',
                    'company_id': company.id,
                    'default_credit_account_id': accounts[SALARY_EXPENSES].id,
                    'default_debit_account_id': accounts[SALARY_EXPENSES].id,
                })
                if hasattr(journal, 'payroll_entry_type'):
                    journal.payroll_entry_type = 'grouped'

                self.env['ir.property'].create([{
                    'name': 'structure_journal_id',
                    'company_id': company.id,
                    'fields_id': journal_field_id.id,
                    'value_reference': 'account.journal,%s' % journal.id,
                    'res_id': 'hr.payroll.structure,%s' % structure.id,
                } for structure in us_structures])

            # Find rules and set accounts on them.
            # Find all rules that are ...

            # BASIC* -> SALARY_EXPENSE debit account
            set_rule_accounts('BASIC%', accounts[salary_exp_code], None)
            # EE_* -> AP debit
            set_rule_accounts('EE_%', accounts[ap_code], None)
            # ER_* -> AP debit, SE credit
            set_rule_accounts('ER_%', accounts[ap_code], accounts[salary_exp_code])
            # NET* -> AP credit
            set_rule_accounts('NET%', None, accounts[ap_code])
