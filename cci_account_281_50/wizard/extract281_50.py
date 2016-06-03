# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api , _
import datetime
import time
import base64
from xlwt import *

class wizard_extract281_50(models.TransientModel):
    _name = 'wizard.extract281_50'
    
    year_id = fields.Many2one('account.fiscalyear',string='Concerned Year',required=True, help='The year of the extracted purchases')
    tag_id = fields.Many2one('crm_profiling.question', string='Tag associated',required=True)
    account_starts_list = fields.Char(string = 'Accounts list',required = True, help = 'List of accounts beginnings on wich extract purchases; i.e. "603,613,612950"')
    limit = fields.Float(string='Limit', required = True, default = 125.0, help='Limit under witch no 281.50 are emitted.')
    min_natnum_percent = fields.Integer(string='Percent minimum Nat.Number', required=True, default = 85, help = 'Minimum percent of national number')
    
    @api.model
    def default_get(self,fields):
        res = super(wizard_extract281_50,self).default_get(fields)
        past_year = int(datetime.datetime.now().strftime('%Y'))-1
        prec_fy_id = self.env['account.fiscalyear'].search([('date_start','=',str(past_year)+'-01-01')])
        if prec_fy_id:
            res['year_id'] = prec_fy_id.id
        return res

    @api.model
    def _split_streets_and_number(self,street1,street2):
        final_street = street1 or ''
        number = ''
        if ',' in final_street:
            pos = final_street.find(',')
            number = final_street[pos+1:].strip()
            final_street = final_street[0:pos].strip()
        if street2:
            final_street += ( ' - ' + street2 )
        return (final_street,number)
    
    @api.multi
    def create_records(self):
        # erase the records of the same year to create new ones
        sel_year = self.year_id.date_start[0:4]
        record_obj = self.env['account.partner281_50']
        old_record_ids = record_obj.search([('year','=',sel_year)])
        if old_record_ids:
            old_record_ids.unlink()
        # extraction of purchases invoices with at least a line in the selected accounts
        # for each of them, we control if the invoice OR the payments are in the concerned year
        # If concerned, we get it

        # construction of the account_ids list
        account_starts_list = self.account_starts_list
        account_starts = account_starts_list.split(',')
        account_starts = [x.strip() for x in account_starts]
        account_ids = []
        
        for start in account_starts:
            start_ids = self.env['account.account'].search([('code','ilike',start+'%'),('type','<>','view')])
            account_ids.extend(start_ids.ids)

        # creation of the table to convert periods to year in string
#         all_period_ids = self.env['account.period'].search(cr,uid,[])
        all_periods = self.env['account.period'].search_read([],['date_start'])
        dPeriod2Year = {}
        for per in all_periods:
            dPeriod2Year[ per['id'] ] = int(per['date_start'][0:4])

        # selection of tagged partners
        selection1 = """SELECT partner
                                           FROM partner_question_rel as pqr, crm_profiling_answer as cpa
                                           WHERE cpa.question_id = %s AND pqr.answer = cpa.id 
                     """ % self.tag_id.id
        self.env.cr.execute(selection1)
        res1 = self.env.cr.fetchall()
        partner_ids = [str(x[0]) for x in res1]
        
        # selection of concerned invoices
        selection = """SELECT id
                           FROM account_invoice 
                           WHERE type in ('in_invoice','in_refund') AND
                                 state in ('open','paid') AND 
                                 partner_id in (%s) AND
                                 id in ( SELECT invoice_id
                                             FROM account_invoice_line 
                                             WHERE account_id in (%s) )
                    """ % (','.join(partner_ids),
                           ','.join([str(x) for x in account_ids])
                          )
        self.env.cr.execute(selection)
        res = self.env.cr.fetchall()
        dPartners = {}
        invoice_ids = [x[0] for x in res]
        invoices = self.env['account.invoice'].browse(invoice_ids)
        for invoice in invoices:
            lInvoiceToTake = False
            # if this invoice is linked to payment(s), we extract the list of payment(s) name and payment(s) year(s)
            pay_years = []
            payments = []
            if invoice.payment_ids:
                for payment in invoice.payment_ids:
                    payment_year = dPeriod2Year[payment.period_id.id]
                    payment_name = payment.move_id.name and payment.move_id.name or payment.journal_id.name
                    if payment_year not in pay_years:
                        pay_years.append(payment_year)
                    payments.append(payment_name)
                # we keep the invoice if the invoice year or one of the payment(s) year is the concerned year
                if sel_year in pay_years:
                    lInvoiceToTake = True
            if lInvoiceToTake:
                # for this invoice, we'll check each line to check the account
                # and we'll cumulate these lines by partners
                for iline in invoice.invoice_line:
                    if iline.account_id.id in account_ids:
                        if iline.invoice_id.partner_id.id not in dPartners.keys():
                            dPartners[iline.invoice_id.partner_id.id] = 0.0
                        if invoice.type == 'in_invoice':
                            dPartners[iline.invoice_id.partner_id.id] += iline.price_subtotal
                        else:
                            dPartners[iline.invoice_id.partner_id.id] -= iline.price_subtotal
                            
        partners = self.env['res.partner'].browse(dPartners.keys())
        new_ids = []
        for partner in partners:
            if dPartners[partner.id] > self.limit:
                new_record = {}
                new_record['partner_id'] = partner.id
                new_record['year'] = sel_year
                new_record['calc_sum_b'] = dPartners[partner.id]
                new_record['name'] = partner.name
                if partner.child_ids:
                    new_record['street1'] = partner.child_ids[0].street or ''
                    new_record['street2'] = partner.child_ids[0].street2 or ''
                    if partner.child_ids[0].zip_id:
                        new_record['zip_code'] = partner.child_ids[0].zip_id.name or ''
                        new_record['city'] = partner.child_ids[0].zip_id.city or ''
                    if partner.vat:
                        new_record['company_number'] = partner.vat
                    else:
                        # search of national number of the first contact_person
                        if partner.child_ids[0].other_contact_ids:
                            if partner.child_ids[0].other_contact_ids[0].contact_id:
                                new_record['national_number'] = partner.child_ids[0].contact_id.national_number or ''
                if partner.answers_ids:
                    for answer in partner.answers_ids:
                        if answer.question_id.id == self.tag_id.id:
                            new_record['profession'] = answer.text.replace('\n','').strip()
                new_record['calc_sum_b'] = dPartners[partner.id]
                new_id = record_obj.create(new_record)
                new_ids.append(new_id.id)
                
        result = {
            'domain': [('id', 'in', new_ids)],
            'name': _('Final 281.50 records'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.partner281_50',
            'context': {},
            'type': 'ir.actions.act_window'
        }
        return result
