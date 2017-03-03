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
# Version 1.1 2011-12-09 Philmer
#             Added the field 'vat' on members export for Jean-Pierre Trésegnie
# Version 2.0 2017-0220 Philmer
#             Extracted the definition of res.partner.zip to make them an stand alone module for open sourcing it
{
    'name' : 'CCI Partner',
    'version' : '1.1',
    'author' : 'Tiny',
    'website' : 'http://www.openerp.com',
    'category' : 'Generic Modules/CCI',
    'description': '''
        Specific module for cci project which will inherit partner module
    ''',
    'depends' : [
        'base_vat', 
        'crm_profiling',
        'cci_base_contact', 
#        'account_l10nbe_domiciliation', 
        'cci_country', 
        'l10n_be_postal_subscriber', 
        'account_followup',
        'res_partner_zip',
    ],
    'demo' : [
        'cci_data.xml',
       # 'user_data.xml',
        'zip_data.xml',
        'courtesy_data.xml',
        'links_data.xml',
        'activity_data.xml',
       # 'states_data.xml',
       # 'category_data.xml',
#         'function_data.xml'
    ],
    'data' : [
         'cci_partner_view.xml',
        'wizard/cci_export_partner_view.xml',
        'wizard/cci_recalc_categ_view.xml',
        'wizard/simple_members_excel_view.xml',
        'wizard/export_all_emails_view.xml',
        'wizard/cci_partner_event_history_view.xml',
        'wizard/cci_wizard_spam_view.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'article_sequence.xml',
        'report/report_count_invoices_qweb.xml',
        'cci_partner_report.xml',
    ],
    'installable': True,
    'certificate': '00530566150061571341',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
