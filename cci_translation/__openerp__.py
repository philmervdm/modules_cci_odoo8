# -*- encoding: utf-8 -*-
##############################################################################
#    
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.     
#
##############################################################################
{
    'name' : 'CCI Translation',
    'version' : '1.0',
    'author' : 'Tiny',
    'website' : 'http://www.openerp.com',
    'category' : 'Generic Modules/CCI',
    'description': '''
        cci translation
    ''',
    'depends' : ['base', 'product', 'purchase'],  # , 'cci_account'
    'data' : [
        'cci_translation_data.xml',
        'cci_translation_view.xml',
        'cci_translation_workflow.xml',
        'cci_translation_report.xml',
        'cci_translation_sequence.xml',
        'wizard/make_invoice_view.xml',
        'wizard/wizard_awex_report_view.xml',
        'security/security.xml',
        'security/cci_translation_security.xml',
        'security/ir.model.access.csv',
        'report/report_translation_awex.xml'
    ],
    'installable': True,
    'certificate': '00761838574443429981',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: