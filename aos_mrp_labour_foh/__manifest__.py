# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Nusatama MRP Labour Cost',
    'version': '14.0.0.1.0',
    'license': 'OPL-1',
    'summary': '-- Nusatama -- Create Journal Entry labour cost & FOH per MO',
    'sequence': 1,
    "author": "Alphasoft - Imronsyabani",
    'description': """
        -- Nusatama
            Create Jurnal labour cost per MO
    """,
    'category' : 'Accounting',
    'website': 'https://www.alphasoft.co.id/',
    'images':  [],
    'depends' : ['mrp','account'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/mrp_labour_foh_view.xml',
        'views/menuitem.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}