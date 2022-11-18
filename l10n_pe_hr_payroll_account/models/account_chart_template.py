# Part of Hibou Suite Professional. See LICENSE_PROFESSIONAL file for full copyright and licensing details.

from odoo import models

EXP_SALARY = '6211000'
EXP_EXTRA = '621100'
EXP_COM = '6212000'
EXP_BONO = '6220000'
EXP_ESSALUD = '6271000'
EXP_GRATIF = '6214000'

PAY_EE = '4111000'
PAY_AFP = '4170000'
PAY_ONP = '4032000'
PAY_IR_4TA_CAT = '4017200'
PAY_IR_5TA_CAT = '4017300'
PAY_ESSALUD = '4031000'


class AccountChartTemplate(models.Model):
    _inherit = 'account.chart.template'

    def _load(self, sale_tax_rate, purchase_tax_rate, company):
        """
        Override to configure payroll accounting data as well as accounting data.
        """
        res = super()._load(sale_tax_rate, purchase_tax_rate, company)
        self._pe_configure_payroll_account_data(company)
        return res

    def _pe_configure_payroll_account_data(self, companies,
                                           pay_ee=PAY_EE,
                                           pay_afp=PAY_AFP,
                                           pay_onp=PAY_ONP,
                                           pay_ir_4ta_cat=PAY_IR_4TA_CAT,
                                           pay_ir_5ta_cat=PAY_IR_5TA_CAT,
                                           pay_essalud=PAY_ESSALUD,
                                           exp_salary=EXP_SALARY,
                                           exp_extra=EXP_EXTRA,
                                           exp_com=EXP_COM,
                                           exp_bono=EXP_BONO,
                                           exp_essalud=EXP_ESSALUD,
                                           exp_gratif=EXP_GRATIF,
                                           salary_rules=None, full_reset=False):
        account_codes = (
            pay_ee,
            pay_afp,
            pay_onp,
            pay_ir_4ta_cat,
            pay_ir_5ta_cat,
            pay_essalud,
            exp_salary,
            exp_extra,
            exp_com,
            exp_bono,
            exp_essalud,
            exp_gratif,
        )
        pe_structures = self.env['hr.payroll.structure'].search([('country_id', '=', self.env.ref('base.pe').id)])
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
            accounts['none'] = self.env['account.account'].browse()

            def set_rule_accounts(code, account_debit, account_credit):
                rule_domain = [
                    ('struct_id', 'in', pe_structures.ids),
                    ('code', '=like', code),
                ]
                if salary_rules:
                    rule_domain.append(('id', 'in', salary_rules.ids))
                rules = self.env['hr.salary.rule'].search(rule_domain)
                if full_reset:
                    values = {
                        'account_debit': account_debit.id,
                        'account_credit': account_credit.id,
                    }
                    rules.write(values)
                else:
                    # we need to ensure we do not update an account that is already set
                    for rule in rules:
                        values = {}
                        if account_debit and not rule.account_debit:
                            values['account_debit'] = account_debit.id
                        if account_credit and not rule.account_credit:
                            values['account_credit'] = account_credit.id
                        if values:
                            # save a write if no values to write
                            rule.write(values)

            journal = self.env['account.journal'].search([
                ('code', '=', 'PAYR'),
                ('name', '=', 'Payroll'),
                ('company_id', '=', company.id),
            ])
            if journal:
                if not journal.default_account_id:
                    journal.default_account_id = accounts[exp_salary].id
                if hasattr(journal, 'payroll_entry_type'):
                    journal.payroll_entry_type = 'grouped'
            else:
                journal = self.env['account.journal'].create({
                    'name': 'Payroll',
                    'code': 'PAYR',
                    'type': 'general',
                    'company_id': company.id,
                    'default_account_id': accounts[exp_salary].id,
                })
                if hasattr(journal, 'payroll_entry_type'):
                    journal.payroll_entry_type = 'grouped'

                self.env['ir.property']._set_multi(
                    "journal_id",
                    "hr.payroll.structure",
                    {structure.id: journal for structure in pe_structures},
                )

            # Find rules and set accounts on them.
            # Find all rules that are ...

            # BASIC* -> SALARY_EXPENSE debit account
            set_rule_accounts('BASIC%', accounts[exp_salary], accounts['none'])
            # ALW* -> SALARY_EXPENSE debit account
            set_rule_accounts('ALW%', accounts[exp_salary], accounts['none'])
            set_rule_accounts('ALW_BONO%', accounts[exp_bono], accounts['none'])
            set_rule_accounts('ALW_BADGES%', accounts[exp_bono], accounts['none'])
            set_rule_accounts('ALW_COM%', accounts[exp_com], accounts['none'])
            set_rule_accounts('ALW_EXTRA%', accounts[exp_extra], accounts['none'])
            set_rule_accounts('ALW_GRATIF%', accounts[exp_gratif], accounts['none'])
            # EE_* -> AP debit
            set_rule_accounts('EE_%', accounts[pay_ee], accounts['none'])  # initialize
            set_rule_accounts('EE_PE_AFP%', accounts[pay_afp], accounts['none'])
            set_rule_accounts('EE_PE_ONP%', accounts[pay_onp], accounts['none'])
            set_rule_accounts('EE_PE_IR_4TA_CAT%', accounts[pay_ir_4ta_cat], accounts['none'])
            set_rule_accounts('EE_PE_IR_5TA_CAT%', accounts[pay_ir_5ta_cat], accounts['none'])
            # ER_* -> AP debit, SE credit
            set_rule_accounts('ER_%', accounts[pay_ee], accounts[exp_salary])  # initialize
            set_rule_accounts('ER_PE_ESSALUD%', accounts[pay_essalud], accounts[exp_essalud])
            # NET* -> AP credit
            set_rule_accounts('NET%', accounts['none'], accounts[pay_ee])
