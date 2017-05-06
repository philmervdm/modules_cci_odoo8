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
from openerp import api, fields, models, _
from openerp.exceptions import Warning
import datetime
import base64
from xlwt import *


class compare_paid_multiple_years(models.TransientModel):
    _name = 'compare.paid.multiple.years'

    first_year = fields.Integer(string='First year', help='First of the years to compare', required=True)
    last_year = fields.Integer(string='Last year', help='Last of the years to compoare', required=True)
#####################################################
#     def _defaults(self, cr, uid, data, context):
#         data['form']['year'] = datetime.datetime.today().year - 1
#         return data['form']

    @api.multi
    def create_excel_file(self):
        # manage parameters
        if self.last_year < 1900 or self.first_year < 1900:
            raise Warning(_('Warning'),
                          _('You must give the year of membership concerned; between 1900 and the next year'))
        # we extract the 'membership products' for the tw concerned years
        # for theses products, we extract all account.invoice.line.
        # For each invoice.line we check if invoice type is sale and if the move linked to the invoice is reconciled on 'receivable' account
        # We keep the id and the amount for each such invoice.line and the concerned years
        # with the invoice_lines ids, we extract concerned partners
        # and for each concerned partners we cumulate by years and compare the two years in excel file
        # we do this because the 'paid' state of invoices is not trustable at 100%
        # But in ths version, we must treat credit nota in another way because they are not linked to membershipline as the invoice lines...
        first_year = self.first_year
        last_year = self.last_year
        concerned_years = range(first_year, last_year+1)
        product_obj = self.env['product.product']
        product_ids = product_obj.search([('membership', '=', True),
                                          ('membership_year', 'in', concerned_years),
                                          '|', ('active', '=', True), ('active', '=', False)])
        if not product_ids:
            raise Warning(_('Warning'),
                          _('There is no membership products for the concerned years : %s' % ','.join([str(x) for x in concerned_years])))
        products = product_ids.read(['id', 'membership_year'])
        dProducts = {}
        for prod in products:
            dProducts[prod['id']] = prod['membership_year']
        ailine_obj = self.env['account.invoice.line']
        ailines = ailine_obj.search([('product_id', 'in', product_ids.ids)])
        if not ailines:
            raise Warning(_('Warning'),
                          _('There is no invoices for the concerned years : %s' % ','.join([str(x) for x in concerned_years])))
        account_obj = self.env['account.account']
        receivable_account_ids = account_obj.search([('type', '=', 'receivable')])
        concerned_ailine_ids = []
        dAILines = {}
        for ailine in ailines:
            move_reconciled = False
            multiplier = 1
            if ailine.invoice_id and ailine.invoice_id.state in ('open', 'paid') and ailine.invoice_id.journal_id and ailine.invoice_id.journal_id.type == 'sale':
                if ailine.invoice_id.journal_id.refund_journal:
                    multiplier = -1
                if ailine.invoice_id.move_id and ailine.invoice_id.move_id.line_id:
                    for mline in ailine.invoice_id.move_id.line_id:
                        if mline.account_id.id in receivable_account_ids.ids and mline.reconcile_id:
                            move_reconciled = True
            if move_reconciled:
                concerned_ailine_ids.append(ailine.id)
                dAILines[ailine.id] = {'amount':ailine.price_subtotal * multiplier,'year':dProducts[ailine.product_id.id],'period_name':ailine.invoice_id.period_id.name,
                                       'partner_name':ailine.invoice_id.partner_id.name,'partner_id':ailine.invoice_id.partner_id.id,'state_id':ailine.invoice_id.partner_id.state_id.id,
                                       'user_id':ailine.invoice_id.partner_id.user_id and ailine.invoice_id.partner_id.user_id.name or '','mmline_found':False,
                                       'state_name':ailine.invoice_id.partner_id.state_id and ailine.invoice_id.partner_id.state_id.name or ''}
        mmline_obj = self.env['membership.membership_line']
        mmlines = mmline_obj.search([('account_invoice_line', 'in', concerned_ailine_ids)])
        dPartners = {}
        dPeriods = {}
        for mmline in mmlines:
            if mmline.partner:
                if dPartners.has_key(mmline.partner.id):
                    partner = dPartners[mmline.partner.id]
                else:
                    partner = {'name': mmline.partner.name,
                               'user_id': mmline.partner.user_id and mmline.partner.user_id.name or '',
                               'state_id': mmline.partner.state_id.id,
                               'state_name': mmline.partner.state_id and mmline.partner.state_id.name or ''}
                    for year in concerned_years:
                        partner['year'+str(year)] = 0.0
                if dPeriods.has_key(dAILines[mmline.account_invoice_line.id]['period_name']):
                    period = dPeriods[dAILines[mmline.account_invoice_line.id]['period_name']]
                else:
                    period = {'name': dAILines[mmline.account_invoice_line.id]['period_name']}
                    for year in concerned_years:
                        period[year] = 0.0
                partner['year'+str(dAILines[mmline.account_invoice_line.id]['year'])] += dAILines[mmline.account_invoice_line.id]['amount']
                period[dAILines[mmline.account_invoice_line.id]['year']] += dAILines[mmline.account_invoice_line.id]['amount']
                dPartners[mmline.partner.id] = partner
                dPeriods[dAILines[mmline.account_invoice_line.id]['period_name']] = period
                dAILines[mmline.account_invoice_line.id]['mmline_found'] = True

        for (ail_id,ailine) in dAILines.items():
            if not ailine['mmline_found']:
                #print ail_id
                #print ailine
                if dPartners.has_key(ailine['partner_id']):
                    partner = dPartners[ailine['partner_id']]
                else:
                    partner = {'name':ailine['partner_name'],'user_id':ailine['user_id'],'state_id':ailine['state_id'],'state_name':ailine['state_name']}
                    for year in concerned_years:
                        partner['year'+str(year)] = 0.0
                if dPeriods.has_key(ailine['period_name']):
                    period = dPeriods[ailine['period_name']]
                else:
                    period = {'name':ailine['period_name']}
                    for year in concerned_years:
                        period[year] = 0.0
                partner['year'+str(ailine['year'])] += ailine['amount']
                period[ailine['year']] += ailine['amount']
                dPartners[ailine['partner_id']] = partner
                dPeriods[ailine['period_name']] = period

        wb = Workbook()
        ws1 = wb.add_sheet('Partners')
        ws1.write(0,0,_('Paid means Reconciled Entries'))
        ws1.write(1,0,_('Shown partners are based on membership_lines, not exactly invoice lines, to be more exact'))
        ws1.write(2,0,_(u'partner_id'))
        ws1.write(2,1,_(u'name'))
        ws1.write(2,2,u'Commercial')
        ws1.write(2,3,u'Etat Activité')
        ws1.write(2,4,_(u'Paid %s') % str(concerned_years[0]))
        col = 4
        count_lost = {}
        count_new = {}
        count_less = {}
        count_more = {}
        count = {}
        count[concerned_years[0]] = 0
        count_faithfull = {}
        amount = {}
        amount[concerned_years[0]] = 0.0
        for year in concerned_years[1:]:
            ws1.write(2,col+1,_(u'Paid %s') % str(year))
            ws1.write(2,col+2,_(u'Status ') + str(year-1) + '->' + str(year))
            ws1.write(2,col+3,_(u'Amount Diff ') + str(year-1) + '->' + str(year))
            count_lost[year] = 0
            count_new[year] = 0
            count_less[year] = 0
            count_more[year] = 0
            count[year] = 0
            count_faithfull[year] = 0
            amount[year] = 0.0
            col += 3
        count_final_faithfull = 0 ## +1 if member first AND last years
        count_all_faithfull = 0 ## + 1 if member first, last and all between years
        count_active_first_year = 0 ## +1 if member the first year and active today
        count_final_active_faithfull = 0 ## +1 if member first AND last years, and active today
        count_all_active_faithfull = 0 ## + 1 if member first, last and all between years, and active_today
        line = 3
        for (partner_id,partner) in dPartners.items():
            ws1.write(line,0,partner_id)
            ws1.write(line,1,partner['name'])
            ws1.write(line,2,partner['user_id'])
            ws1.write(line,3,partner['state_name'])
            ws1.write(line,4,partner['year'+str(concerned_years[0])])
            if partner['year'+str(concerned_years[0])] >= 0.001:
                count[concerned_years[0]] += 1
            amount[concerned_years[0]] += partner['year'+str(concerned_years[0])]
            col = 4
            all_years_paid = ( partner['year'+str(concerned_years[0])] >= 0.01 )
            for year in concerned_years[1:]:
                past_year = 'year'+str(year-1)
                curr_year = 'year'+str(year)
                ws1.write(line,col+1,partner[curr_year])
                if partner[past_year] >= 0.001 and partner[curr_year] <= 0.001:
                    ws1.write(line,col+2,'lost')
                    count_lost[year] += 1
                elif partner[past_year] <= 0.001 and partner[curr_year] >= 0.001:
                    ws1.write(line,col+2,'new')
                    count_new[year] += 1
                elif partner[past_year] >= 0.001 and partner[curr_year] >= 0.001 and partner[past_year] > partner[curr_year]:
                    ws1.write(line,col+2,'less money')
                    count_less[year] += 1
                elif partner[past_year] >= 0.001 and partner[curr_year] >= 0.001 and partner[past_year] < partner[curr_year]:
                    ws1.write(line,col+2,'more money')
                    count_more[year] += 1
                if partner[curr_year] >= 0.001:
                    count[year] += 1
                amount[year] += partner[curr_year]
                if partner[past_year] >= 0.001 and partner[curr_year] >= 0.001:
                    count_faithfull[year] += 1
                ws1.write(line,col+3,partner[curr_year]-partner[past_year])
                if not ( partner[curr_year] >= 0.01):
                    all_years_paid = False
                col += 3
            if partner['year'+str(concerned_years[0])] >= 0.01 and partner['year'+str(concerned_years[-1])] >= 0.01:
                count_final_faithfull += 1
            if all_years_paid:
                count_all_faithfull += 1
            if partner['state_id'] == 1:
                if partner['year'+str(first_year)] >= 0.01:
                    count_active_first_year += 1
                if partner['year'+str(concerned_years[0])] >= 0.01 and partner['year'+str(concerned_years[-1])] >= 0.01:
                    count_final_active_faithfull += 1
                if all_years_paid:
                    count_all_active_faithfull += 1
            line += 1
        col = 4
        ws1.write(line,0,u'Total')
        ws1.write(line,4,'%i=%.2f' % (count[concerned_years[0]],amount[concerned_years[0]]))
        for year in concerned_years[1:]:
            ws1.write(line,col+1,'%i=%.2f' % (count[year],amount[year]) )
            col += 3
        line += 1
        # record the global data on worsheet 2
        ws2 = wb.add_sheet(_('Global Data'))
        ws2.write(0,0,_('Global Results'))
        ws2.write(1,0,_('Date'))
        ws2.write(1,1,datetime.datetime.today().strftime('%d/%m/%Y'))
        ws2.write(3,0,_('Count'))
        ws2.write(4,0,_('Lost'))
        ws2.write(5,0,_('New'))
        ws2.write(6,0,_('Less money'))
        ws2.write(7,0,_('More money'))
        ws2.write(8,0,_('Amount'))
        ws2.write(9,0,_('Faithfull'))
        ws2.write(10,0,_('Fidelity Rate'))
        ws2.write(2,1,str(concerned_years[0]))
        ws2.write(3,1,count[concerned_years[0]])
        ws2.write(8,1,amount[concerned_years[0]])
        col = 2
        for year in concerned_years[1:]:
            ws2.write(2,col,_(u'From %i to %i') % (year-1,year))
            ws2.write(3,col,count[year])
            ws2.write(4,col,count_lost[year])
            ws2.write(5,col,count_new[year])
            ws2.write(6,col,count_less[year])
            ws2.write(7,col,count_more[year])
            ws2.write(8,col,amount[year])
            ws2.write(9,col,count_faithfull[year])
            if count[year-1]:
                ws2.write(10,col,str(int(count_faithfull[year]*100/count[year-1]))+'%')
            else:
                ws2.write(10,col,0)
            col += 1
        ws2.write(12,0,_(u'Final fidelity rate from %i to %i (just comparing these tow years, not what between !)') % (first_year,last_year))
        if count[first_year]:
            ws2.write(13,0,str(int(count_final_faithfull*100/count[first_year]))+'%')
            ws2.write(13,5,count_final_faithfull)
            ws2.write(13,6,count[first_year])
        ws2.write(13,1,count_final_faithfull)
        ws2.write(14,0,_(u'Final complete fidelity rate from %i to %i (paid members all years!)') % (first_year,last_year))
        if count[first_year]:
            ws2.write(15,0,str(int(count_all_faithfull*100/count[first_year]))+'%')
            ws2.write(15,5,count_all_faithfull)
            ws2.write(15,6,count[first_year])
        ws2.write(15,1,count_all_faithfull)
        # just count active ones
        ws2.write(17,0,_(u'Final fidelity rate from %i to %i (just comparing these tow years, not what between !) if the partner is still active today') % (first_year,last_year))
        if count[first_year]:
            ws2.write(18,0,str(int(count_final_active_faithfull*100/count_active_first_year))+'%')
            ws2.write(18,5,count_final_active_faithfull)
            ws2.write(18,6,count_active_first_year)
        ws2.write(19,0,_(u'Final complete fidelity rate from %i to %i (paid members all years!) if the partner is still active today') % (first_year,last_year))
        if count[first_year]:
            ws2.write(20,0,str(int(count_all_active_faithfull*100/count_active_first_year))+'%')
            ws2.write(20,5,count_all_active_faithfull)
            ws2.write(20,6,count_active_first_year)

        # record the data by periods on worsheet 3
        lPeriods = sorted([x[3:]+x[0:2] for x in dPeriods.keys()])
        ws3 = wb.add_sheet('Periods')
        ws3.write(0,0,_('Amounts by membership Year and Period'))
        ws3.write(2,0,_('Period'))
        ws3.write(1,1,_('Amount'))
        col = 1
        for year in concerned_years:
            ws3.write(2,col,year)
            col += 1
        line = 3
        for period_name in lPeriods:
            period = dPeriods[period_name[4:]+'/'+period_name[0:4]]
            ws3.write(line,0,period['name'])
            col = 1
            for year in concerned_years:
                if period[year] <= -0.01 or period[year] >= 0.01:
                    ws3.write(line,col,period[year])
                col +=1
            line += 1

        # Enregistrement en excel
        wb.save('compare_paidmembers.xls')
        result_file = open('compare_paidmembers.xls', 'rb').read()

        # give the result tos the user
        view = self.env.ref('cci_membership_extend.view_wizard_compare_paid_multiple_years_msg_form')
        ctx = self.env.context.copy()
        ctx['msg'] = 'Save the File with '".xls"' extension.'
        ctx['file'] = base64.encodestring(result_file)
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.compare.paid.multiple.years.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx
        }


class wizard_compare_paid_multiple_years_msg(models.TransientModel):
    _name = 'wizard.compare.paid.multiple.years.msg'

    name = fields.Char(string='File name')
    msg = fields.Text(string='File created', size=100, readonly=True)
    compare_paidmembers_xls = fields.Binary(string='Prepared file', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(wizard_compare_paid_multiple_years_msg, self).default_get(fields)
        res['name'] = 'compare_paidmembers.xls'
        res['msg'] = self.env.context.get('msg')
        res['compare_paidmembers_xls'] = self.env.context.get('file')
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
