from odoo import models
import json
DEFAULT_COLUMN = {'default_header_row':6,'default_header_col':0,'default_row':7,'default_col':0}
class PartnerXlsx(models.AbstractModel):
    _name = 'report.base_accounting_kit.report_financial_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data,object):
        company = self.env.company.name
        sheet = workbook.add_worksheet("Test")
        sheet.set_column("A:AZ",20)
        data = json.loads(object.datas)
        sheet.set_column("B:B",34)
        formats = workbook.add_format
        filter_obj = data.get('filter')[0][::-1] if data.get('filter') else {}
        sheet.merge_range("A1:C1",company,formats({'bold':True,'align':'center','valign':'vcenter','font_size':16}))
        sheet.merge_range("A2:C2",data['form'][0]['account_report_id'][1],formats({'bold':True,'valign':'vcenter','align':'center','font_size':14}))
        if not object.enable_filter:
            title = f"{data['form'][0]['date_from'] if data['form'][0]['date_from'] else ''} {'- ' + data['form'][0]['date_to'] if data['form'][0]['date_to'] else ''}"
            sheet.merge_range("A3:C3",title,formats({'align':'center','valign':'vcenter'}))
        sheet.write("A6","Target Moves",formats({'align':'center'})) 
        if data['form'][0]['target_move'] == 'all':
            sheet.write("B6",'All Entries',formats({'valign':'vcenter','align':'center'}))
        else:
            sheet.write("B6",'All Posted Entries',formats({'valign':'vcenter','align':'center'}))

        # sheet.merge_range("F7:G8","DATE",formats({'valign':'vcenter'}))

        # set variabel untuk header column dan row dimulai setelah column balance yaitu 0
        header_row = DEFAULT_COLUMN['default_header_row']
        header_col = DEFAULT_COLUMN['default_header_col']
        sheet.write(header_row,header_col,"Name")
        header_col += 1
        if data['form'][0]['debit_credit']:
            sheet.write(header_row,header_col,"Debit")
            header_col +=1

            sheet.write(header_row,header_col,"Credit")
            header_col += 1
        if object.enable_filter:
            sheet.write(header_row,header_col,object.from_id.name + " " +(object.year_from.name if object.year_from else '') )
            header_col += 1
        else:
            sheet.write(header_row,header_col,"Balance")
            header_col += 1
        if filter_obj:
            for line in filter_obj:
                sheet.write(header_row,header_col,line[0])
                header_col += 1
        line_row = DEFAULT_COLUMN['default_row']
        line_col = DEFAULT_COLUMN['default_col']
        last_line_col = 0
        format_amount = formats({'align':'right','num_format':'[$Rp-421]#,##0;[$Rp-421]#,##0'})
        font_weight = formats({'bold':True})
        for name in object._mapping_account_name:

            first_filter = next(filter(lambda x: x if x.get('name') == name else {}, data['report_lines']), {})

            if first_filter.get('level') > 3:
                font_weight = formats({'bold':False})
            line_col += 1
            
            if data['form'][0]['debit_credit'] == 1:
                sheet.write(line_row,line_col,first_filter.get('debit') if first_filter.get('debit') != 0 else 0,format_amount)
                line_col += 1

                sheet.write(line_row,line_col,first_filter.get('credit') if first_filter.get('credit') != 0 else 0,format_amount)
                line_col += 1

            sheet.write(line_row,line_col,first_filter.get('balance') if first_filter.get('balance') != 0 else 0,format_amount)

            if data.get('filter'):
                line_col += 1
                for index in range(0,len(filter_obj)):
                    second_filter = next(filter(lambda x: x if x.get('name') == name else {}, filter_obj[index][1]), {})
                    sheet.write(line_row,line_col,second_filter.get('balance') if second_filter.get('balance') != 0 else 0,format_amount)
                    line_col += 1
                    if second_filter.get('level') > 3:
                        font_weight = formats({'bold':False})

            last_line_col = line_col
            line_col = 0
            spacing_indent = '  ' * first_filter.get('level',0)
            sheet.write(line_row,line_col,spacing_indent + name,font_weight)
            line_row += 1
            # name dan balance adalah column static yang selalu ada
        # if data.get('filter'):
        #     keys = data['filter'][0].keys()
        #     line_col = last_line_col
        #     for key in list(keys)[::-1]:
        #         header_col += 1
        #         sheet.write(header_row,header_col,key)
        #         line_col += 1
        #         line_row = DEFAULT_COLUMN['default_row']
        #         for v in data['filter'][0][key]:
        #             sheet.write(line_row,line_col,v['balance'] if v.get('balance') != 0 else 'Rp0',format_amount)
        #             line_row += 1