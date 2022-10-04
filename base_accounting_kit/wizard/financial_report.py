# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import re
from calendar import monthrange
from datetime import datetime,date
from odoo import api, models, fields
from odoo.exceptions import UserError

class FinancialReport(models.TransientModel):
    _name = "financial.report"
    _inherit = "account.common.report"
    _description = "Financial Reports"

    view_format = fields.Selection([
        ('vertical', 'Vertical'),
        ('horizontal', 'Horizontal')],
        default='vertical',
        string="Format")

    @api.model
    def _get_account_report(self):
        reports = []
        if self._context.get('active_id'):
            menu = self.env['ir.ui.menu'].browse(
                self._context.get('active_id')).name
            reports = self.env['account.financial.report'].search([
                ('name', 'ilike', menu)])
        return reports and reports[0] or False

    enable_filter = fields.Boolean(
        string='Enable Comparison',
        default=False)
    account_report_id = fields.Many2one(
        'account.financial.report',
        string='Account Reports',
        required=True)

    filter_selection = fields.Selection([
        ('date','Date'),
        ('quarter','Quarter'),
        ('monthly','Monthly'),
        ('yearly','Yearly'),
    ],string="Filter By", default='date')
    
    config_filter_id = fields.Many2one('config.filter',string="Filter Id",help="for related many2many relation")
    from_id = fields.Many2one('config.filter',string="From")
    to_id = fields.Many2one('config.filter',string="Compare To")
    year_from = fields.Many2one('config.filter',domain=[('type','=','yearly')],string="From Year")
    year_to = fields.Many2one('config.filter',domain=[('type','=','yearly')],string="Compare To Year")
    multi_period = fields.Boolean(string="Multi Period")
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    debit_credit = fields.Boolean(
        string='Display Debit/Credit Columns',
        default=True,
        help="This option allows you to"
             " get more details about the "
             "way your balances are computed."
             " Because it is space consuming,"
             " we do not allow to use it "
             "while doing a comparison.")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        index=True,
        default=lambda self: self.env.company.id)

    def view_report_pdf(self):
        """This function will be executed when we click the view button
        from the wizard. Based on the values provided in the wizard, this
        function will print pdf report"""
        self.ensure_one()
        data = dict()
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(
            ['date_from', 'enable_filter', 'debit_credit', 'date_to',
             'account_report_id', 'target_move', 'view_format',
             'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(
            used_context,
            lang=self.env.context.get('lang') or 'en_US')

        report_lines = self.get_account_lines(data['form'])
        # find the journal items of these accounts
        journal_items = self.find_journal_items(report_lines, data['form'])

        def set_report_level(rec):
            """This function is used to set the level of each item.
            This level will be used to set the alignment in the dynamic reports."""
            level = 1
            if not rec['parent']:
                return level
            else:
                for line in report_lines:
                    key = 'a_id' if line['type'] == 'account' else 'id'
                    if line[key] == rec['parent']:
                        return level + set_report_level(line)

        # finding the root
        for item in report_lines:
            item['balance'] = round(item['balance'], 2)
            if not item['parent']:
                item['level'] = 1
                parent = item
                report_name = item['name']
                id = item['id']
                report_id = item['r_id']
            else:
                item['level'] = set_report_level(item)
        currency = self._get_currency()
        data['currency'] = currency
        data['journal_items'] = journal_items
        data['report_lines'] = report_lines
        # checking view type
        return self.env.ref(
                'base_accounting_kit.financial_report_pdf').report_action(self,data)

    def view_report_xlsx(self):
        """This function will be executed when we click the view button
        from the wizard. Based on the values provided in the wizard, this
        function will print pdf report"""
        self.ensure_one()
        data = dict()
        result = dict()
        data['form'] = self.read(
            ['date_from', 'enable_filter', 'debit_credit', 'date_to',
             'account_report_id', 'target_move', 'view_format',
             'company_id'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(
            used_context,
            lang=self.env.context.get('lang') or 'en_US')

        if self.enable_filter and self.filter_selection != 'date':
            # get amount from filter
            data_copy = data['form']
            if self.multi_period:
                filter_result = self.range_comparison(self.year_from,self.year_to,self.from_id,self.to_id)
            else:
                filter_result = self.set_filter_data(self.to_id,self.year_to)
                
            for line in filter_result:
                data_copy['used_context'].update({'date_from':line[1].get('from_month'),'date_to':line[1].get('to_month')})
                data_copy.update({'date_from':line[1].get('from_month'),'date_to':line[1].get('to_month')})
                res = {f"{line[0]}":self.get_account_lines(data_copy)}
                res = self.froot(res)
                result.update(res)

        if self.filter_selection != 'date':
            filter_result = self.set_filter_data(self.from_id,self.year_from)
            data['form']['used_context'].update({'date_from':filter_result.get('from_month'),'date_to':filter_result.get('to_month')})
            data['form'].update({'date_from':filter_result.get('from_month'),'date_to':filter_result.get('to_month')})

        report_lines = self.get_account_lines(data['form'])
        report_lines = self.froot(report_lines)
        # find the journal items of these accounts
        # journal_items = self.find_journal_items(report_lines, data['form'])

        # currency = self._get_currency()
        # data['currency'] = currency
        # data['journal_items'] = journal_items
        data['filter'] = result
        data['report_lines'] = report_lines
        return self.env.ref(
                'base_accounting_kit.financial_report_excel').report_action(docids=[],data=data)

    def set_filter_data(self,filter=False,year=False):
        result = {}
        today = fields.Datetime.today()
        year_from = year.year_int if year else today.year
        if self.filter_selection == 'quarter':
            # if self.to_id:
            #     filter.update({'to_month_int':self.to_id.months.mapped('month_int').sort(),'year_to':year_to})

            # if self.to_id.quarter_sequence < self.from_id.quarter_sequence and year_to == year_from:
            #     raise UserError(f"Doesnt Match Quarter {self.from_id.name} to {self.to_id.name} in the same year")

            month_int = filter.months.mapped('month_int')
            from_date = date(year_from,min(month_int),1)
            end_from_date = monthrange(year_from,max(month_int))[1]
            to_date = date(year_from,max(month_int),end_from_date)

            result.update({'from_month':from_date,'to_month':to_date})
        elif self.filter_selection == 'monthly':
            from_date = date(year_from,filter.month_int,1)
            end_from_date = monthrange(year_from,from_date.month)[1]
            result.update({'from_month':from_date,'to_month':from_date.replace(day=end_from_date)})
        
        elif self.filter_selection == 'yearly':
            year = filter.year_int
            month_int = filter.months.mapped('month_int')
            from_date = date(year,min(month_int),1)
            end_from_date = monthrange(year_from,max(month_int))[1]
            to_date = date(year,max(month_int),end_from_date)
            result.update({'from_month':from_date,'to_month':to_date})
        return result

    def range_comparison(self,from_year,to_year,filter_from=False,filter_to=False):
        today = date.today()
        default_from_year = from_year if from_year else self.env['config.filter'].search([('name','=',str(today.year))],limit=1)
        default_to_year = to_year if to_year else self.env['config.filter'].search([('name','=',str(today.year))],limit=1)
        result = {}
        list_result = []
        if self.filter_selection == 'quarter':
            if default_to_year.year_int < default_from_year.year_int:
                # get_filter_from = self.env['config.filter'].search([('type','=','quarter'),('quarter_sequence','<=',filter_from.quarter_sequence)])
                # get_filter_to = self.env['config.filter'].search([('type','=','quarter'),('quarter_sequence','>=',filter_to.quarter_sequence)])
                # for line in get_filter_from.sorted(reverse=True):
                #     list_result.append({line.name +" "+ default_from_year.name:self.set_filter_data(line,default_from_year)})
                # for line in get_filter_to.sorted(reverse=True):
                #     list_result.append({line.name +" "+ default_to_year.name:self.set_filter_data(line,default_to_year)})
                # from_date = self.set_filter_data(filter_to,to_year)
                raise UserError(f'Invalid Comparison {self.from_id.name} {self.year_from.name} to {self.to_id.name} {self.year_to.name}')

            elif default_to_year.year_int > default_from_year.year_int:
                get_filter_from = self.env['config.filter'].search([('type','=','quarter'),('quarter_sequence','>=',filter_from.quarter_sequence)])
                get_filter_to = self.env['config.filter'].search([('type','=','quarter'),('quarter_sequence','<=',filter_to.quarter_sequence)])
                # raise UserError(f'Invalid Comparison {self.from_id.name} {self.year_from.name} to {self.to_id.name} {self.year_to.name}')
                for line in get_filter_from:
                    list_result.append({line.name +" "+ default_from_year.name:self.set_filter_data(line,default_from_year)})
                for line in get_filter_to:
                    list_result.append({line.name +" "+ default_to_year.name:self.set_filter_data(line,default_to_year)})

            elif default_to_year.year_int == default_from_year.year_int:
                if filter_from.quarter_sequence < filter_to.quarter_sequence:
                    get_filter = self.env['config.filter'].search([('type','=','quarter'),('quarter_sequence','>=',filter_from.quarter_sequence),('quarter_sequence','<=',filter_to.quarter_sequence)])
                else:
                    get_filter = self.env['config.filter'].search([('type','=','quarter'),('quarter_sequence','<=',filter_from.quarter_sequence),('quarter_sequence','>=',filter_to.quarter_sequence)])
                
                for line in get_filter:
                    list_result.append({line.name +" "+ default_from_year.name:self.set_filter_data(line,default_from_year)})

        elif self.filter_selection == 'monthly':
            if int(default_to_year.name) < int(default_from_year.name):
                # get_filter_from = self.env['config.filter'].search([('type','=','monthly'),('month_int','<=',filter_from.month_int)])
                # get_filter_to = self.env['config.filter'].search([('type','=','monthly'),('month_int','>=',filter_to.month_int)])
                # for line in get_filter_from:
                #     list_result.append({line.name +" "+ default_from_year.name:self.set_filter_data(line,default_from_year)})
                # for line in get_filter_to:
                #     list_result.append({line.name +" "+ default_to_year.name:self.set_filter_data(line,default_to_year)})
                # # from_date = self.set_filter_data(filter_to,to_year)
                raise UserError(f'Invalid Comparison {self.from_id.name} {self.year_from.name} to {self.to_id.name} {self.year_to.name}')

            elif int(default_to_year.name) > int(default_from_year.name):
                get_filter_from = self.env['config.filter'].search([('type','=','monthly'),('month_int','>=',filter_from.month_int)])
                get_filter_to = self.env['config.filter'].search([('type','=','monthly'),('month_int','<=',filter_to.month_int)])
                # raise UserError(f'Invalid Comparison {self.from_id.name} {self.year_from.name} to {self.to_id.name} {self.year_to.name}')
                for line in get_filter_from:
                    list_result.append({line.name +" "+ default_from_year.name:self.set_filter_data(line,default_from_year)})
                for line in get_filter_to:
                    list_result.append({line.name +" "+ default_to_year.name:self.set_filter_data(line,default_to_year)})

            elif int(default_to_year.name) == int(default_from_year.name):
                if filter_from.month_int < filter_to.month_int:
                    get_filter = self.env['config.filter'].search([('type','=','monthly'),('month_int','>=',filter_from.month_int),('month_int','<=',filter_to.month_int)])
                else:
                    get_filter = self.env['config.filter'].search([('type','=','monthly'),('month_int','<=',filter_from.month_int),('month_int','>=',filter_to.month_int)])
                
                for line in get_filter:
                    list_result.append({line.name +" "+ default_from_year.name:self.set_filter_data(line,default_from_year)})
                    
        elif self.filter_selection == 'yearly':
            get_filter = self.env['config.filter'].search([('type','=','yearly')])
            if int(filter_from.name) > int(filter_to.name):
                # res = get_filter.filtered(lambda x:x.year_int <= filter_from.year_int and x.year_int >= filter_to.year_int)
                raise UserError(f'Invalid Comparison {self.from_id.name} to {self.to_id.name}')
            else:
                res = get_filter.filtered(lambda x:x.year_int >= filter_from.year_int and x.year_int <= filter_to.year_int)
            for line in res:
                list_result.append({line.name:self.set_filter_data(line)})

        for l in list_result:
            result.update(l)
        return list(result.items())

    def froot(self,report_lines,currency=False):
        # finding the root
        if not currency:
            currency = self.env.company.currency_id.symbol
        else:
            currency = currency.symbol
        
        def set_report_level(rec):
            """This function is used to set the level of each item.
            This level will be used to set the alignment in the dynamic reports."""
            level = 1
            if not rec['parent']:
                return level
            else:
                for line in list(report_lines.values())[0]:
                    key = 'a_id' if line['type'] == 'account' else 'id'
                    if line[key] == rec['parent']:
                        return level + set_report_level(line)

        for item in list(report_lines.values())[0]:
            item['balance'] = round(item['balance'], 2)
            if not item['parent']:
                item['level'] = 1
                parent = item
                report_name = item['name']
                id = item['id']
                report_id = item['r_id']
            else:
                item['level'] = set_report_level(item)
            item['balance'] = f"{currency} {item['balance']:,.0f}"
            
            if self.debit_credit == True:
                item['debit'] = f"{currency} {item['debit']:,.0f}"
                item['credit'] = f"{currency} {item['credit']:,.0f}"
        return report_lines
        
    def _compute_account_balance(self, accounts):
        """ compute the balance, debit
        and credit for the provided accounts
        """
        mapping = {
            'balance':
                "COALESCE(SUM(debit),0) - COALESCE(SUM(credit), 0)"
                " as balance",
            'debit': "COALESCE(SUM(debit), 0) as debit",
            'credit': "COALESCE(SUM(credit), 0) as credit",
        }

        res = {}
        for account in accounts:
            res[account.id] = dict((fn, 0.0)
                                   for fn in mapping.keys())
        if accounts:
            tables, where_clause, where_params = (
                self.env['account.move.line']._query_get())
            tables = tables.replace(
                '"', '') if tables else "account_move_line"
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            request = ("SELECT account_id as id, " +
                       ', '.join(mapping.values()) +
                       " FROM " + tables +
                       " WHERE account_id IN %s " +
                       filters +
                       " GROUP BY account_id")
            params = (tuple(accounts._ids),) + tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                res[row['id']] = row
        return res

    def _compute_report_balance(self, reports):
        """returns a dictionary with key=the ID of a record and
         value=the credit, debit and balance amount
        computed for this record. If the record is of type :
        'accounts' : it's the sum of the linked accounts
        'account_type' : it's the sum of leaf accounts with
         such an account_type
        'account_report' : it's the amount of the related report
        'sum' : it's the sum of the children of this record
         (aka a 'view' record)"""
        res = {}
        fields = ['credit', 'debit', 'balance']
        for report in reports:
            if report.id in res:
                continue
            res[report.id] = dict((fn, 0.0) for fn in fields)
            if report.type == 'accounts':
                # it's the sum of the linked accounts
                res[report.id]['account'] = self._compute_account_balance(
                    report.account_ids
                )
                for value in \
                        res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_type':
                # it's the sum the leaf accounts
                #  with such an account type
                accounts = self.env['account.account'].search([
                    ('user_type_id', 'in', report.account_type_ids.ids)
                ])
                res[report.id]['account'] = self._compute_account_balance(
                    accounts)
                for value in res[report.id]['account'].values():
                    for field in fields:
                        res[report.id][field] += value.get(field)
            elif report.type == 'account_report' and report.account_report_id:
                # it's the amount of the linked report
                res2 = self._compute_report_balance(report.account_report_id)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
            elif report.type == 'sum':
                # it's the sum of the children of this account.report
                res2 = self._compute_report_balance(report.children_ids)
                for key, value in res2.items():
                    for field in fields:
                        res[report.id][field] += value[field]
        return res

    def get_account_lines(self, data):
        lines = []
        account_report = self.env['account.financial.report'].search([
            ('id', '=', data['account_report_id'][0])
        ])
        child_reports = account_report._get_children_by_order()
        res = self.with_context(
            data.get('used_context'))._compute_report_balance(child_reports)
        if data['enable_filter']:
            comparison_res = self._compute_report_balance(child_reports)
            for report_id, value in comparison_res.items():
                res[report_id]['comp_bal'] = value['balance']
                report_acc = res[report_id].get('account')
                if report_acc:
                    for account_id, val in \
                            comparison_res[report_id].get('account').items():
                        report_acc[account_id]['comp_bal'] = val['balance']

        for report in child_reports:
            r_name = str(report.name)
            # r_name = r_name.replace(" ", "-") + "-"
            r_name = re.sub('[^0-9a-zA-Z]+', '', r_name)
            if report.parent_id:
                p_name = str(report.parent_id.name)
                p_name = re.sub('[^0-9a-zA-Z]+', '', p_name) + str(
                    report.parent_id.id)
                # p_name = p_name.replace(" ", "-") +
                #  "-" + str(report.parent_id.id)
            else:
                p_name = False
            vals = {
                'r_id': report.id,
                'id': r_name + str(report.id),
                'sequence': report.sequence,
                'parent': p_name,
                'name': report.name,
                'balance': res[report.id]['balance'] * int(report.sign),
                'type': 'report',
                'level': bool(
                    report.style_overwrite) and report.style_overwrite or
                         report.level,
                'account_type': report.type or False,
                # used to underline the financial report balances
            }
            if data['debit_credit']:
                vals['debit'] = res[report.id]['debit']
                vals['credit'] = res[report.id]['credit']

            if data['enable_filter']:
                vals['balance_cmp'] = res[report.id]['comp_bal'] * int(
                    report.sign)

            lines.append(vals)
            if report.display_detail == 'no_detail':
                # the rest of the loop is
                # used to display the details of the
                #  financial report, so it's not needed here.
                continue

            if res[report.id].get('account'):
                sub_lines = []
                for account_id, value \
                        in res[report.id]['account'].items():
                    # if there are accounts to display,
                    #  we add them to the lines with a level equals
                    #  to their level in
                    # the COA + 1 (to avoid having them with a too low level
                    #  that would conflicts with the level of data
                    # financial reports for Assets, liabilities...)
                    flag = False
                    account = self.env['account.account'].browse(account_id)
                    # new_r_name = str(report.name)
                    # new_r_name = new_r_name.replace(" ", "-") + "-"
                    vals = {
                        'account': account.id,
                        'a_id': account.code + re.sub('[^0-9a-zA-Z]+', 'acnt',
                                                      account.name) + str(
                            account.id),
                        'name': account.code + '-' + account.name,
                        'balance': value['balance'] * int(report.sign) or 0.0,
                        'type': 'account',
                        'parent': r_name + str(report.id),
                        'level': (
                                report.display_detail == 'detail_with_hierarchy' and
                                4),
                        'account_type': account.internal_type,
                    }
                    if data['debit_credit']:
                        vals['debit'] = value['debit']
                        vals['credit'] = value['credit']
                        if not account.company_id.currency_id.is_zero(
                                vals['debit']) or \
                                not account.company_id.currency_id.is_zero(
                                    vals['credit']):
                            flag = True
                    if not account.company_id.currency_id.is_zero(
                            vals['balance']):
                        flag = True
                    if data['enable_filter']:
                        vals['balance_cmp'] = value['comp_bal'] * int(
                            report.sign)
                        if not account.company_id.currency_id.is_zero(
                                vals['balance_cmp']):
                            flag = True
                    if flag:
                        sub_lines.append(vals)
                lines += sorted(sub_lines,
                                key=lambda sub_line: sub_line['name'])
        return lines

    def find_journal_items(self, report_lines, form):
        cr = self.env.cr
        journal_items = []
        for i in report_lines:
            if i['type'] == 'account':
                account = i['account']
                if form['target_move'] == 'posted':
                    search_query = "select aml.id, am.id as j_id, aml.account_id, aml.date," \
                                   " aml.name as label, am.name, " \
                                   + "(aml.debit-aml.credit) as balance, aml.debit, aml.credit, aml.partner_id " \
                                   + " from account_move_line aml join account_move am " \
                                     "on (aml.move_id=am.id and am.state=%s) " \
                                   + " where aml.account_id=%s"
                    vals = [form['target_move']]
                else:
                    search_query = "select aml.id, am.id as j_id, aml.account_id, aml.date, " \
                                   "aml.name as label, am.name, " \
                                   + "(aml.debit-aml.credit) as balance, aml.debit, aml.credit, aml.partner_id " \
                                   + " from account_move_line aml join account_move am on (aml.move_id=am.id) " \
                                   + " where aml.account_id=%s"
                    vals = []
                if form['date_from'] and form['date_to']:
                    search_query += " and aml.date>=%s and aml.date<=%s"
                    vals += [account, form['date_from'], form['date_to']]
                elif form['date_from']:
                    search_query += " and aml.date>=%s"
                    vals += [account, form['date_from']]
                elif form['date_to']:
                    search_query += " and aml.date<=%s"
                    vals += [account, form['date_to']]
                else:
                    vals += [account]
                cr.execute(search_query, tuple(vals))
                items = cr.dictfetchall()

                for j in items:
                    temp = j['id']
                    j['id'] = re.sub('[^0-9a-zA-Z]+', '', i['name']) + str(
                        temp)
                    j['p_id'] = str(i['a_id'])
                    j['type'] = 'journal_item'
                    journal_items.append(j)
        return journal_items

    @api.model
    def _get_currency(self):
        journal = self.env['account.journal'].browse(
            self.env.context.get('default_journal_id', False))
        if journal.currency_id:
            return journal.currency_id.id
        return self.env.company.currency_id.symbol


class ProfitLossPdf(models.AbstractModel):
    """ Abstract model for generating PDF report value and send to template """

    _name = 'report.base_accounting_kit.report_financial'
    _description = 'Financial Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """ Provide report values to template """
        ctx = {
            'data': data,
            'journal_items': data['journal_items'],
            'report_lines': data['report_lines'],
            'account_report': data['form']['account_report_id'][1],
            'currency': data['currency'],
        }
        return ctx
