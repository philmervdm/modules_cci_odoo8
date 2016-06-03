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
# Version 1.0 Philmer
#         1.1 Philmer - added the sum of the sale.order.line programmed until the end of the year or not programmed
import time
import datetime
import base64
from xlwt import *
from openerp import api, fields, models, _

class extract_comm_results(models.TransientModel):
    _name = 'extract.comm.results'
    
    from_period = fields.Many2one('account.period', string='From', required = True, domain="[('special','=',False)]")
    to = fields.Many2one('account.period', string='To', required=True, domain="[('special','=',False)]")
    years = fields.Integer(string='Years to compare', required=True, default=2)

    @api.model
    def default_get(self, fields):
        res = super(extract_comm_results,self).default_get(fields)
        current_year = datetime.datetime.today().strftime('%Y')
        current_month = datetime.datetime.today().strftime('%m')
        current_month = str(int(current_month)-1).rjust(2,'0')
        obj_period = self.env['account.period']
        period_id = obj_period.search([('name','=','01/' + current_year )])
        if period_id:
            res['from_period'] = period_id.id
        period_id = obj_period.search([('name','=',current_month + '/' + current_year )])
        if period_id:
            res['to'] = period_id.id
        return res
    
    @api.multi
    def get_file(self):
        obj_period = self.env['account.period']
        res ={}
        comm_results = False
        from_period = self.from_period.read(['name','date_start','date_stop'])[0]
        current_year = from_period['name'][-4:]
        to_period = self.to.read(['name','date_start','date_stop'])[0]
        if to_period['name'][-4:] == current_year:
            if self.years >= 1:
                years = [int(current_year)]
                for decalage in range(1,self.years):
                    years.append(int(current_year)-decalage)
                # creation of the array for the results
                obj_product = self.env['product.product']
                product_ids = obj_product.search(['|',('active','=',True),('active','=',False)])
                products = obj_product.read(product_ids,['id','name'])
                dProducts = {}
                for prod in products:
                    dProducts[prod['id']] = prod['name']
                obj_cci_product = self.env['cci.product']
                cci_products = obj_cci_product.search(['|',('active','=',True),('active','=',False)])
#                 cci_products = obj_cci_product.browse(cci_product_ids)
                dCCIProducts = {}
                dCCIProductsFromProducts = {}
                dResults = {}
                CCIProducts = []
                result = {}
                for year in years:
                    result[year] = 0.0
                this_result = result.copy()
                dResults[0] = this_result
                for cci_prod in cci_products:
                    dCCIProducts[cci_prod.id] = cci_prod
                    CCIProducts.append((cci_prod.name,cci_prod.id))
                    for product_id in cci_prod.product_ids:
                        dCCIProductsFromProducts[product_id.id] = cci_prod.id
                    this_result = result.copy()
                    dResults[cci_prod.id] = this_result
                CCIProducts.sort(key=lambda tup: tup[0])
                # search for the criteria of extraction
                obj_journal = self.env['account.journal']
                sale_journal_ids = obj_journal.search([('type','=','sale')])
                obj_account = self.env['account.account']
                ignored_account_ids = obj_account.search(['|',('code','=','400000'),'|',('code','ilike','411%'),('code','ilike','451%')])
                # writing in excel files
                wb = Workbook()
                wsr = wb.add_sheet(_('Results'))
                wsr.write(0,0,_('From'))
                wsr.write(0,1,from_period['name'])
                wsr.write(1,0,_('To'))
                wsr.write(1,1,to_period['name'])
                wsr.write(2,0,_('Date'))
                wsr.write(2,1,datetime.datetime.today().strftime('%d/%m/%Y'))
                wsr.write(3,0,_('Years'))
                wsr.write(3,1,self.years)
                wsr.write(5,0,_("Commercial Product"))
                col = 1
                for year in years:
                    wsr.write(5,col,_("Sales ") + str(year) )
                    col += 1
                wsd = wb.add_sheet(_('Detail Sums'))
                wsd.write(0,0,_('Year'))
                wsd.write(0,1,_('Product sold'))
                wsd.write(0,2,_('Commercial Product associated'))
                wsd.write(0,3,_('Amount'))
                linexls = 2
                # extraction of results year by year
                for year in years:
                    obj_period = self.env['account.period']
                    start = str(year)+from_period['date_start'][4:]
                    stop = str(year)+to_period['date_stop'][4:]
                    period_ids = obj_period.search([('date_start','>=',start),('date_stop','<=',stop),('special','=',False)])
                    selection = """SELECT aml.product_id, SUM(aml.debit) as sdebit, SUM(aml.credit) as scredit
                                        FROM account_move_line as aml, account_move as am
                                        WHERE aml.period_id in (%s) AND aml.journal_id in (%s) AND
                                              aml.account_id not in (%s) AND aml.state = 'valid' AND
                                              aml.move_id = am.id AND am.state = 'posted'
                                        GROUP BY aml.product_id
                    """ % (','.join([str(x) for x in period_ids.ids]), ','.join([str(x) for x in sale_journal_ids.ids]), ','.join([str(x) for x in ignored_account_ids.ids]))
                    self.env.cr.execute(selection)
                    res = self.env.cr.fetchall()
                    for line in res:
                        if dCCIProductsFromProducts.has_key(line[0]):
                            current_res = dResults[ dCCIProductsFromProducts[line[0]] ]
                        else:
                            current_res = dResults[0]
                        current_res[year] += ((line[2] or 0.0 ) - (line[1] or 0.0 ))
                        # writing of details while computing totals
                        wsd.write(linexls,0,year)
                        if line[0]:
                            wsd.write(linexls,1,dProducts[line[0]] + ' [' + str(line[0]) + ']')
                            wsd.write(linexls,2,dCCIProductsFromProducts.has_key(line[0]) and dCCIProducts[dCCIProductsFromProducts[line[0]]].name or '-')
                        else:
                            wsd.write(linexls,1,'- []')
                            wsd.write(linexls,2,'-')
                        wsd.write(linexls,3,((line[2] or 0.0 ) - (line[1] or 0.0 )))
                        linexls += 1
                # writing of cumulated results lines in excel file
                wsr.write(6,0,_('Produit inconnu'))
                result = dResults[0]
                dTotals = {}
                col = 1
                for year in years:
                    wsr.write(6,col,result[year])
                    dTotals[year] = result[year]
                    col += 1
                line = 7
                for cci_prod in CCIProducts:
                    wsr.write(line,0,cci_prod[0] or _('No name'))
                    result = dResults[cci_prod[1]]
                    col = 1
                    for year in years:
                        wsr.write(line,col,result[year])
                        dTotals[year] += result[year]
                        col += 1
                    line += 1

                # writing of global sales by year
                line += 1
                col = 1
                wsr.write(line,0,_('Total'))
                for year in years:
                    wsr.write(line,col,dTotals[year])
                    col += 1
                wb.save('comm_results.xls')
                result_file = open('comm_results.xls','rb').read()

                # give the result to the user
                msg='Save the File with '".xls"' extension.'
                comm_results = base64.encodestring(result_file)
            else:
                msg='The number of years must be 1 or greater.'
        else:
            msg='The two periods must be in the same year.'
        
        ctx = self.env.context.copy()
        ctx['msg'] = msg
        ctx['comm_results'] = comm_results
        
        result = {
            'name': _('Notification'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'extract.comm.results2',
            'target': 'new',
            'context': ctx,
            'type': 'ir.actions.act_window'
        }
        return result
     
class extract_comm_results2(models.TransientModel):
    _name = 'extract.comm.results2'
    
    msg = fields.Text(string ='File Created', readonly=True)
    comm_results = fields.Binary(string= 'Prepared file', readonly=True)
    name = fields. Char(string ='File Name')
    
    @api.model
    def default_get(self,fields):
        res = super(extract_comm_results2, self).default_get(fields)
        context = dict(self._context or {})
        res.update({
            'msg': context['msg'],
            'comm_results': context['comm_results'],
            'name': 'comm_results.xls'
        })
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

