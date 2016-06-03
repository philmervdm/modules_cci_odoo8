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

class prepare281_50(models.TransientModel):
    _name = 'wizard.prepare281_50'

    year_id = fields.Many2one('account.fiscalyear',string='Concerned Year',required=True, help='The year of the extracted purchases')
    tag_id = fields.Many2one('crm_profiling.question', string='Tag associated',required=True)
    account_starts_list = fields.Char(string = 'Accounts list',required = True, help = 'List of accounts beginnings on wich extract purchases; i.e. "603,613,612950"')


    @api.model
    def default_get(self,fields):
        res = super(prepare281_50,self).default_get(fields)
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
    def create_control_file(self):
        filename = 'control_281_50.xls'

        # construction of the account_ids list
        account_starts_list = self.account_starts_list
        account_starts = account_starts_list.split(',')
        account_starts = [x.strip() for x in account_starts]
        account_ids = []
        
        for start in account_starts:
            start_ids = self.env['account.account'].search([('code','ilike',start+'%'),('type','<>','view')])
            account_ids.extend(start_ids.ids)
            
        accounts = self.env['account.account'].browse(account_ids).read(['code','name'])
        account_codes_list = []
        dAccounts = {}
        for acc in accounts:
            dAccounts[acc['id']] = ( '%s - %s' % ((acc['code'] or '??????'), (acc['name'] or 'Unknown')))
            account_codes_list.append(acc['code'] or '??????')

        # creation of the table to convert periods to year in string
        all_periods = self.env['account.period'].search_read([],['date_start'])
        dPeriod2Year = {}
        for per in all_periods:
            dPeriod2Year[ per['id'] ] = per['date_start'][0:4]
        
        # creation of the list of period inside this year
        period_ids = self.env['account.period'].search([('fiscalyear_id','=',self.year_id.id)])
        concerned_year = dPeriod2Year[period_ids[0].id]
        
        # extraction of the tag name
        tag_name = self.tag_id.name

        # Creation of the result file
        wb = Workbook()
        ws1 = wb.add_sheet(_('Moves on specified accounts'))
        ws2 = wb.add_sheet(_('Purchases for tagged suppliers'))
        
        # print help on excel sheets
        ws1.write(0,0,_('Moves on specified accounts'))
        ws1.write(1,0,_('Parameters'))
        ws1.write(2,0,_('Year'))
        ws1.write(2,1,concerned_year)
        ws1.write(3,0,_('Tag'))
        ### TODO not "tag id" but "tag name [tag_id]"
        #ws1.write(3,1,data['form']['tag_id'])
        ws1.write(3,1,tag_name)
        ws1.write(4,0,_('Account Starts List'))
        ws1.write(4,1,self.account_starts_list)
        ws1.write(5,0,_('Corresponding accounts'))
        ws1.write(5,1,','.join(account_codes_list))
        ws1.write(7,0,_('This list gives you all moves on specified accounts, not only in the given year'))
        ws1.write(8,0,_('but also on another years if linked payment(s) are in specified year.'))
        ws1.write(9,0,_('The goal of this list is to find partners not yet tagged, but to be tagged.'))
        ws1.write(10,0,_('With this list, we can also find invoices where associated payments exist'))
        ws1.write(11,0,_('in more than a year, that is a problem to solve before extracting final data !'))
        ws1.write(13,0,_('Don\'t forget to control also the second sheet of this excel file !'))
        ws1.write(15,0,_('We extract also open invoices to show them and control if they are not paid.'))
        ws1.write(17,0,_('Invoice ID'))
        ws1.write(17,1,_('Price wo VAT'))
        ws1.write(17,2,_('Invoice Period'))
        ws1.write(17,3,_('Payment(s) Year(s)'))
        ws1.write(17,4,_('Payment(s) Moves'))
        ws1.write(17,5,_('Payment Normal'))
        ws1.write(17,6,_('Partner ID'))
        ws1.write(17,7,_('Partner Name'))
        ws1.write(17,8,_('VAT Number'))
        ws1.write(17,9,_('Tag Profession'))
        ws1.write(17,10,_('Personal National Number'))
        ws1.write(17,11,_('First Name'))
        ws1.write(17,12,_('Last Name'))
        ws1.write(17,13,_('Street'))
        ws1.write(17,14,_('Street number'))
        ws1.write(17,15,_('Zip Code'))
        ws1.write(17,16,_('City'))
        ws1.write(17,17,_('Country'))
        line_sheet1 = 18
        #
        ws2.write(0,0,_('Purchases for tagged suppliers'))
        ws2.write(1,0,_('Parameters'))
        ws2.write(2,0,_('Year'))
        ws2.write(2,1,concerned_year)
        ws2.write(3,0,_('Tag'))
        ### TODO not "tag id" but "tag name [tag_id]"
        ws2.write(3,1,tag_name)
        ws2.write(4,0,_('Account Starts List'))
        ws2.write(4,1,self.account_starts_list)
        ws2.write(5,0,_('Corresponding accounts'))
        ws1.write(5,1,','.join(account_codes_list))
        ws2.write(7,0,_('This list gives you all lines of purchase invoices linked to tagged partners,'))
        ws2.write(8,0,_('not only for the selected year but also preceding year, because the concerned'))
        ws2.write(9,0,_('date is the date of the payment, not the date of the purchase.'))
        ws2.write(10,0,_('Only the lines on others accounts than thoses selected are printed here.'))
        ws2.write(11,0,_('The goal of this list is to find moves on wrong accounts not extracted for'))
        ws2.write(12,0,_('belgian 281.50 records, to correct them BEFORE extraction of the final data.'))
        ws2.write(14,0,_('Don\'t forget to extract this list again if you tag new partners !'))
        ws2.write(16,0,_('Don\'t forget to control also the first sheet of this Excel file !'))
        ws2.write(18,0,_('Line ID'))
        ws2.write(18,1,_('Move ID'))
        ws2.write(18,2,_('Partner ID'))
        ws2.write(18,3,_('Move Name'))
        ws2.write(18,4,_('Account'))
        ws2.write(18,5,_('Amount'))
        ws2.write(18,6,_('Line Name'))
        ws2.write(18,7,_('Partner Name'))
        ws2.write(18,8,_('Period'))
        ws2.write(18,9,_('Payment(s) year(s)'))
        ws2.write(18,10,_('Payment(s)'))
        line_sheet2 = 19
        
        # extraction of purchases invoices with at least a line in the selected accounts
        # for each of them, we control if the invoice OR the payments are in the concerned year
        # If concerned, we put it on the Excel file
        selection = """SELECT id
                           FROM account_invoice 
                           WHERE type in ('in_invoice','in_refund') AND
                                 state in ('open','paid') AND 
                                 id in ( SELECT invoice_id
                                             FROM account_invoice_line 
                                             WHERE account_id in (%s) )
                    """ % ','.join([str(x) for x in account_ids])
        self.env.cr.execute(selection)
        res = self.env.cr.fetchall()
        invoice_ids = [x[0] for x in res]
        invoices = self.env['account.invoice'].browse(invoice_ids)
        
        for invoice in invoices:
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
            if dPeriod2Year[invoice.period_id.id] == concerned_year or concerned_year in pay_years:
                ws1.write(line_sheet1,0,invoice.id)
                total_wo_tax = 0.0
                for line in invoice.invoice_line:
                    if line.account_id.id in account_ids:
                        total_wo_tax += round(line.price_subtotal or 0.0,2)
                ws1.write(line_sheet1,1,total_wo_tax)
                ws1.write(line_sheet1,2,invoice.period_id.name)
                ws1.write(line_sheet1,3,','.join(pay_years))
                ws1.write(line_sheet1,4,','.join(payments))
                ws1.write(line_sheet1,5,len(pay_years)>1 and u'NON - à vérifier !!!')
                ws1.write(line_sheet1,6,invoice.partner_id.id)
                ws1.write(line_sheet1,7,invoice.partner_id.name)
                ws1.write(line_sheet1,8,invoice.partner_id.vat or '')
                profession = ''
                if invoice.partner_id.answers_ids:
                    for answer in invoice.partner_id.answers_ids:
                        if answer.question_id.id == data['form']['tag_id']:
                            profession = answer.text or _('strange profession')
                            break
                ws1.write(line_sheet1,9,profession)
                # extraction of the national number of the unique contact person
                if invoice.partner_id.child_ids and invoice.partner_id.child_ids[0].contact_id:
                    ws1.write(line_sheet1,10,invoice.partner_id.child_ids[0].contact_id.national_number or '')
                    ws1.write(line_sheet1,11,invoice.partner_id.child_ids[0].contact_id.first_name or '')
                    ws1.write(line_sheet1,12,invoice.partner_id.child_ids[0].contact_id.name or '')
                if invoice.partner_id.child_ids and invoice.partner_id.child_ids[0]:
                    (street,number) = self._split_streets_and_number(invoice.partner_id.child_ids[0].street,invoice.partner_id.child_ids[0].street2)
                    ws1.write(line_sheet1,13,street)
                    ws1.write(line_sheet1,14,number)
                    if invoice.partner_id.address[0].zip_id:
                        ws1.write(line_sheet1,15,invoice.partner_id.child_ids[0].zip_id.name)
                        ws1.write(line_sheet1,16,invoice.partner_id.child_ids[0].zip_id.city)
                    if invoice.partner_id.child_ids[0].country_id and invoice.partner_id.child_ids[0].country_id.code != 'BE':
                        ws1.write(line_sheet1,17,invoice.partner_id.child_ids[0].country_id.name)
                line_sheet1 += 1
            
        # extraction of purchases invoice lines on others accounts but linked to tagged partners
        # to check if there is no errors on accounts attribution
        # the final total doesn(t take these lines on others accounts into account,
        # thus we must verify this list BEFORE printing final total 281.50 records

        # search all periods in the selection fiscal year and preceding one
        this_fy_start = self.year_id.date_start
        prec_fy_start = str(int(this_fy_start[0:4])-1)+this_fy_start[4:]
        prec_fy_id = self.env['account.fiscalyear'].search([('date_start','=',prec_fy_start)])
        if prec_fy_id:
            prec_fy_id = prec_fy_id.id
        else:
            prec_fy_id = 0  ## 0 if selected FY = first year of bookkeeping
        years2_period_ids = self.env['account.period'].search([('fiscalyear_id','in',[prec_fy_id,self.year_id.id])])
        #
        #selection = """SELECT ail.id
        #                   FROM account_invoice_line as ail, account_invoice as ai
        #                   WHERE ai.type in ('in_invoice','in_refund') AND
        #                         ai.state in ('open','paid') AND 
        #                         ai.partner_id in
        #                             ( SELECT partner
        #                                   FROM partner_question_rel as pqr, crm_profiling_answer as cpa
        #                                   WHERE cpa.question_id = %s AND pqr.answer = cpa.id 
        #                             ) AND
        #                         ai.period_id in (%s) AND
        #                         ail.account_id not in (%s)
        #            """ % (data['form']['tag_id'],
        #                   ','.join([str(x) for x in years2_period_ids]),
        #                   ','.join([str(x) for x in account_ids]))
        #print 'selection'
        #print selection

        # in three steps is quickier ...
        selection1 = """SELECT partner
                                           FROM partner_question_rel as pqr, crm_profiling_answer as cpa
                                           WHERE cpa.question_id = %s AND pqr.answer = cpa.id 
                     """ % self.tag_id.id
        self.env.cr.execute(selection1)
        res1 = self.env.cr.fetchall()
        partner_ids = [str(x[0]) for x in res1]
        #
        selection2 = """SELECT id
                            FROM account_invoice
                            WHERE type in ('in_invoice','in_refund') AND
                                  state in ('open','paid') AND 
                                  partner_id in (%s) AND
                                  period_id in (%s)
                     """ % (','.join(partner_ids),
                            ','.join([str(x) for x in years2_period_ids.ids]))
        self.env.cr.execute(selection2)
        res2 = self.env.cr.fetchall()
        invoice_ids = [str(x[0]) for x in res2]
        #
        selection3 = """SELECT id
                            FROM account_invoice_line
                            WHERE invoice_id in (%s) AND
                                  account_id not in (%s)
                     """ % (','.join(invoice_ids),
                            ','.join([str(x) for x in account_ids]))
        self.env.cr.execute(selection3)
        res3 = self.env.cr.fetchall()
        #
        iline_ids = [x[0] for x in res3]
        ilines = self.env['account.invoice.line'].browse(iline_ids)
        for iline in ilines:
            # if this invoice is linked to payment(s), we extract the list of payment(s) name and payment(s) year(s)
            ws2.write(line_sheet2,0,iline.id)
            ws2.write(line_sheet2,1,iline.invoice_id.id)
            ws2.write(line_sheet2,2,iline.invoice_id.partner_id.id)
            ws2.write(line_sheet2,3,iline.invoice_id.number)
            ws2.write(line_sheet2,4,(iline.account_id.code or '' ) + ' - ' + iline.account_id.name)
            ws2.write(line_sheet2,5,iline.price_subtotal)
            ws2.write(line_sheet2,6,iline.name)
            ws2.write(line_sheet2,7,iline.invoice_id.partner_id.name or 'Partenaire inconnu')
            ws2.write(line_sheet2,8,iline.invoice_id.period_id.name)
            # search payments_years on linked invoice
            pay_years = []
            payments = []
            if iline.invoice_id.payment_ids:
                for payment in iline.invoice_id.payment_ids:
                    payment_year = str(dPeriod2Year[payment.period_id.id])
                    payment_name = payment.move_id.name and payment.move_id.name or payment.journal_id.name
                    if payment_year not in pay_years:
                        pay_years.append(payment_year)
                    payments.append(payment_name)
            ws2.write(line_sheet2,9,','.join(pay_years))
            ws2.write(line_sheet2,10,','.join(payments))
            line_sheet2 += 1
        # record the created file
        wb.save(filename)
        result_file = open(filename,'rb').read()
        # give the result to the user
        
        ctx = self.env.context.copy()
        ctx['control_281_50'] = base64.encodestring(result_file)
        ctx['name'] = filename
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.prepare281_50.msg',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }
        
class prepare281_50_msg(models.TransientModel):
    _name = 'wizard.prepare281_50.msg'

    name = fields.Char(string='File')
    control_281_50 = fields.Binary(string='Prepared control file', readonly = True)
    
    @api.model
    def default_get(self,fields):
        res = super(prepare281_50_msg,self).default_get(fields)
        res['name'] = self.env.context.get('name')
        res['control_281_50'] = self.env.context.get('control_281_50')
        return res


