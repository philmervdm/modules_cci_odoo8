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
    'name' : 'CCI mission',
    'version' : '1.0',
    'author' : 'Tiny',
    'website' : 'http://www.openerp.com',
    'category' : 'Generic Modules/CCI',
    'description': '''
        specific module for cci project.
    ''',
    'depends' : ['base','crm','cci_partner','product','membership', 'sale','cci_country','cci_translation'],
                #'cci_event','cci_account','cci_translation',
    'init' : [],
    'demo' : ['cci_mission_data.xml'],
    'data' : [
                'cci_mission_wizard.xml',
                'wizard/add_product_line.xml', 
                'cci_mission_view.xml',
                'cci_mission_report.xml',
                'cci_mission_workflow.xml',
                'security/security.xml',
                'security/cci_missions_security.xml',
                'security/ir.model.access.csv',
                'wizard/create_invoice_view.xml',
                'wizard/create_invoice_embassy.xml',
                'wizard/wizard_create_embassy_folder.xml',
                'wizard/create_invoice_carnet.xml',
                'wizard/wizard_fedration_certificate.xml',
                'wizard/wizard_federation_sending.xml',
                'wizard/wizard_simulation_carnet.xml',
                'wizard/cci_encode_cash.xml',
                'wizard/wizard_print_carnet.xml',
                'wizard/create_legalization.xml',
                'wizard/carnet_before_validity.xml',
                'wizard/carnet_after_validity.xml',
                'wizard/print_stats_mission.xml',
                'wizard/make_invoice_group.xml',
                'report/report_print_carnet_header_qweb.xml',
                'report/report_print_carnet_export_qweb.xml',
                'report/report_print_carnet_import_qweb.xml',
                'report/report_print_carnet_transit_qweb.xml',
                'report/report_print_carnet_reexport_qweb.xml',
                'report/report_print_carnet_reimport_qweb.xml',
                'report/report_print_carnet_presence_qweb.xml',
                'report/report_print_carnet_export_reimport_qweb.xml',
                'report/report_print_carnet_import_reexport_qweb.xml',
                'report/report_print_carnet_vtransit_qweb.xml',
                'report/carnet_after_validity_qweb.xml',
                'report/carnet_before_validity_qweb.xml',
              ],
    'active': False,
    'installable': True,
    'certificate': '001306008984766423325',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

