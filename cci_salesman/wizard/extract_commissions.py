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
import datetime
import base64
from xlwt import *
from openerp import api, fields, models, _
from openerp.exceptions import Warning

class extract_commissions(models.TransientModel):
    _name = 'extract.commissions'
    
    date_from = fields.Many2one('account.period',string='From', required=True)
    to = fields.Many2one('account.period', string='To', required=True) 
    commercial = fields.Many2one('res.users', string='Salesman')
    
    @api.model
    def default_get(self,fields):
        obj_group = self.env['res.groups']
        group_ids = obj_group.search([('name','=','CCI Salesman Commissions')])
        manager_group = group_ids[0]
        found_manager = False
        for user in manager_group.users:
            if user.id == self.env.uid:
                found_manager = True
        if found_manager:
            # manager =< give access to commissions of all salesmen
            obj_contact = self.env['cci.contact']
            contact_ids = obj_contact.search([('commissioned','=',True)])
            contacts = contact_ids.read(['id','user'])
            user_ids = []
            for contact in contacts:
                if contact['user']:
                    user_ids.append(contact['user'][0])
        else:
            # not manager => check if the current user is a salesman
            obj_contact = self.env['cci.contact']
            contact_ids = obj_contact.search([('user','=',self.env.uid)])
            contacts = contact_ids.read(['id','user','commissioned'])
            if len(contacts) == 1 and contacts[0]['commissioned']:
                user_ids = [self.env.uid]
            else:
                # not manager, not salesman => give no access
                raise Warning(_('No access'),_('You are not a commission manager or a salesman.\nYou don\'t have access to this tool'))
#         fields['commercial']['domain'] = "[('id','in',%s)]" % ( [','.join(user_ids)] )
        return super(extract_commissions,self).default_get(fields)

    @api.multi
    def get_file(self):
        # list of concerned users
        commision_file = False
        if self.commercial:
            # only one salesman
            user_ids = self.commercial
        else:
            # all salesman
            obj_contact = self.env['cci.contact']
            contact_ids = obj_contact.search([('commissioned','=',True)])
            contacts = contact_ids.read(['id','user'])
            user_ids = []
            for contact in contacts:
                if contact['user']:
                    user_ids.append(contact['user'][0])
        # select of all 'sale' journals
        journal_ids = self.env['account.journal'].search([('type','=','sale')])
        journal_list = ','.join(map(str,journal_ids.ids))
        # selection of all commissionable accounts
        account_ids = self.env['account.account'].search([('cci_commission','=',True)])
        account_list = ','.join(map(str,account_ids.ids))
        # selection of all concerned periods
        obj_period = self.env['account.period']
        from_period_id = self.date_from
        to_period_id = self.to
        period_from = from_period_id.read(['id','name','date_start','date_stop'])[0]
        period_to = to_period_id.read(['id','name','date_start','date_stop'])[0]
        period_ids = obj_period.search([('special','=',False),('date_start','>=',min(period_from['date_start'],period_to['date_start'])),('date_stop','<=',max(period_from['date_stop'],period_to['date_stop']))])
        period_list = ','.join(map(str,period_ids.ids))
        from_date = period_from['name']
        to_date = period_to['name']
        current_year = period_from['date_start'][0:4]
        # creation of dict with users name and detection of users with sliced commissions
        obj_user = self.env['res.users']
        all_users = obj_user.search(['|',('active','=',True),('active','=',False)])
#         all_users = obj_user.browse(all_user_ids)
        sliced_ids = []
        sliced_slices = {}
        dUsers = {}
        for user in all_users:
            dUsers[user['id']] = {'id':user['id'],'name':user['name']}
            if user.slice_ids:
                slices = []
                for slice_def in user.slice_ids:
                    if str(slice_def.year) == current_year:
                        slices.append({'amount_from':slice_def['amount_from'],'rate':slice_def['rate100']/100})
                if slices:
                    sliced_ids.append(user.id)
                    # sort of slices to add 'amount_to'
                    slices = sorted(slices, key=lambda x: x['amount_from'])
                    index = 1
                    full_slices = []
                    for slice_def in slices:
                        if index < len(slices):
                            slice_def['amount_to'] = (slices[index]['amount_from']-0.01)
                        else:
                            slice_def['amount_to'] = 99999999999999.99
                        full_slices.append(slice_def)
                        index += 1
                    sliced_slices[user.id] = full_slices
        # selection of all account move line for all users; the selection on users will be made later
        selection = """
            SELECT aml.name, aml.id, aml.debit, aml.credit, aml.product_id, cp.id, cp.code, rp.id, rp.name, rp.user_id, ai.user_id, am.name, am.state, aa.code
                FROM account_move_line as aml
                    LEFT OUTER JOIN res_partner as rp ON ( aml.partner_id = rp.id )
                    LEFT OUTER JOIN account_move as am ON ( aml.move_id = am.id )
                    LEFT OUTER JOIN account_invoice as ai ON ( am.id = ai.move_id )
                    LEFT OUTER JOIN product_product as pp ON ( aml.product_id = pp.id )
                    LEFT OUTER JOIN cci_product as cp ON ( pp.cci_product_id = cp.id )
                    LEFT OUTER JOIN account_account as aa ON ( aml.account_id = aa.id )
                WHERE aml.period_id in (%s) AND 
                      aml.journal_id in (%s) AND
                      aml.account_id in (%s) AND 
                      aml.state = 'valid'
        """ % (period_list,journal_list,account_list)
        self.env.cr.execute(selection)
        res = self.env.cr.fetchall()
        # selection of all sale.order.line for all users; the selection on users will be made later
        selection = """
            SELECT sol.name, sol.id, (sol.price_unit * sol.product_uos_qty ) as price_subtotal, sol.expected_invoice_date, sol.product_id, cp.id, cp.code, rp.id, rp.name, rp.user_id, so.user_id, so.name, sol.state
                FROM sale_order_line as sol
                    LEFT OUTER JOIN sale_order as so ON ( sol.order_id = so.id )
                    LEFT OUTER JOIN res_partner as rp ON ( so.partner_id = rp.id )
                    LEFT OUTER JOIN product_product as pp ON ( sol.product_id = pp.id )
                    LEFT OUTER JOIN cci_product as cp ON ( pp.cci_product_id = cp.id )
                WHERE sol.invoiced = false AND
                      ( ( sol.expected_invoice_date between '%s-01-01' AND '%s-12-31' ) OR sol.expected_invoice_date IS NULL ) AND
                      sol.state <> 'draft' AND sol.state <> 'cancel'
        """ % (current_year,current_year)
        self.env.cr.execute(selection)
        pipeline = self.env.cr.fetchall()
        if res or pipeline:
            # creation of dict of partner browse objects for each selected partner_id
            partner_ids = []
            for line in res:
                if line[7] and line[7] not in partner_ids:
                    partner_ids.append(line[7])
            dPartners = {}
            if partner_ids:
                partners = self.env['res.partner'].browse(partner_ids)
                for partner in partners:
                    dPartners[partner.id] = partner
            # initialization of the result table by user and cci_product_id
            obj_cci_product = self.env['cci.product']
            product_ids = obj_cci_product.search([])
            products = product_ids.read(['id','name','commissioned','code'])
            product_ids = product_ids.ids
            dProducts = {}
            for prod in products:
                dProducts[prod['id']] = prod
            dProducts[0] = {'id':0,'name':'Lignes sans produits','commissioned':False,'code':'Aucun'}
            #
            dResults = {}
            dPipeline = {}
            dPossible = {}
            user_ids = user_ids.ids
            for user_id in user_ids:
                key = (user_id,0)
                dResults[key] = 0.0
                dPipeline[key] = 0.0
                dPossible[key] = 0.0
                for prod_id in product_ids:
                    key = (user_id,prod_id)
                    dResults[key] = 0.0
                    dPipeline[key] = 0.0
                    dPossible[key] = 0.0
            # writing in excel files
            wb = Workbook()
            # writing of details while computing totals
            wsd = wb.add_sheet(_('Details'))
            wsd.write(0,0,_("Line ID" ))
            wsd.write(0,1,_("Description"))
            wsd.write(0,2,_("Amount"))
            wsd.write(0,3,_("CCI Product"))
            wsd.write(0,4,_("Move Name"))
            wsd.write(0,5,_("Partner Name"))
            wsd.write(0,6,_("Partner Location"))
            wsd.write(0,7,_("Salesman"))
            wsd.write(0,8,_("Account"))
            iline = 1
            for line in res:
                if ( line[12] == 'posted' ) and (line[10] or line[9]):
                    salesman_id = ( line[10] or line[9] )
                    cci_product_id = ( line[5] or 0 )
                    partner = False
                    if line[7] and line[7] in dPartners.keys():
                        partner = dPartners[line[7]]
                    if (salesman_id in user_ids) or (66 in user_ids and salesman_id != 66 and cci_product_id == 14):
                        wsd.write(iline,0,line[1] or '')
                        wsd.write(iline,1,line[0])
                        wsd.write(iline,2,line[3]-line[2])
                        wsd.write(iline,3,line[6] or '')
                        wsd.write(iline,4,line[11] or '')
                        wsd.write(iline,5,line[8] or '')
                        # extract of invoice address, else default address, else first address
                        address = False
                        for addr in partner.child_ids:
                            if addr.type == 'invoice':
                                address = addr
                            elif addr.type == 'default' and not address:
                                address = addr
                        if ( not address ) and partner.child_ids:
                            address = partner.child_ids[0]
                        wsd.write(iline,6,address and address.zip_id and ( address.zip_id.name + ' ' + address.zip_id.city ) or '')
                        wsd.write(iline,7,dUsers.has_key(salesman_id) and dUsers[salesman_id]['name'] or ( _('Unkwnow user ') + str(salesman_id) ) )
                        wsd.write(iline,8,line[13] or '')
                        key = (salesman_id,cci_product_id)
                        if salesman_id in user_ids:
                            dResults[key] += ( line[3] - line[2] )
                        # special case for Solange Nys : she cumulates all 'pub' sales, not only those linked to her
                        # 66 = res_user 'Solange Nys'
                        # 14 = cci_product 'CCI Mag'
                        if 66 in user_ids and salesman_id != 66 and cci_product_id == 14:
                            dResults[(66,14)] += ( line[3] - line[2] )
                        iline += 1
            all_product_ids = [0,]
            for prod_id in product_ids:
                all_product_ids.append(prod_id)
            # search for objectives by user by product
            obj_objectif = self.env['cci.objectif']
            dObjectives = {}
            for user_id in user_ids:
                for prod_id in product_ids:
                    objectif_ids = obj_objectif.search([('year','=',current_year),('user','=',user_id),('cci_product','=',prod_id)])  # there is only one
                    if len(objectif_ids) > 0:
                        objectif = objectif_ids[0].read(['objective'])
                        current_objective = objectif['objective']
                    else:
                        current_objective = 0
                        
                    key = (user_id,prod_id)
                    dObjectives[key] = current_objective
            # writing of pipeline details while computing totals
            wsp = wb.add_sheet(_('Sale Order Details'))
            wsp.write(0,0,_("Line ID" ))
            wsp.write(0,1,_("Expected Invoice Date"))
            wsp.write(0,2,_("Description"))
            wsp.write(0,3,_("Amount"))
            wsp.write(0,4,_("CCI Product"))
            wsp.write(0,5,_("Sale Order Name"))
            wsp.write(0,6,_("Partner Name"))
            wsp.write(0,7,_("Salesman"))
            wsp.write(0,8,_("Line State"))
            iline = 1
            for line in pipeline:
                salesman_id = line[10] or line[9]
                cci_product_id = line[5] or 0
                if (salesman_id in user_ids) or (66 in user_ids and salesman_id != 66 and cci_product_id == 14):
                    wsp.write(iline,0,line[1] or '')
                    wsp.write(iline,1,line[3] and ( line[3][8:10]+'/'+line[3][5:7]+'/'+line[3][0:4]) or '' )
                    wsp.write(iline,2,line[0])
                    wsp.write(iline,3,line[2])
                    wsp.write(iline,4,line[6] or '')
                    wsp.write(iline,5,line[11] or '')
                    wsp.write(iline,6,line[8] or '')
                    wsp.write(iline,7,dUsers.has_key(salesman_id) and dUsers[salesman_id]['name'] or ( _('Unkwnow user ') + str(salesman_id) ) )
                    key = (salesman_id,cci_product_id)
                    if (salesman_id in user_ids):
                        if (line[3] and (line[3][0:4] == current_year)):
                            dPipeline[key] += line[2]
                        else:
                            dPossible[key] += line[2]
                    # special case for Solange Nys : she cumulates all 'pub' sales, not only those linked to her
                    # 66 = res_user 'Solange Nys'
                    # 14 = cci_product 'CCI Mag'
                    if 66 in user_ids and salesman_id != 66 and cci_product_id == 14:
                        if line[3] and (line[3][0:4] == current_year):
                            dPipeline[(66,14)] += line[2]
                        else:
                            dPossible[(66,14)] += line[2]
                    iline += 1
            # calculation of paid amounts
            selection = """
                SELECT user_id, SUM(amount)
                    FROM cci_salesman_commission_payment
                    WHERE period_id in (%s)
                    GROUP BY user_id
            """ % (period_list)
            self.env.cr.execute(selection)
            res = self.env.cr.fetchall()
            dPaidUsers = {}
            for total in res:
                dPaidUsers[total[0]] = total[1]
            # take commission adjustment into account
            dAdjustments = {}
            dGlobalAdjust = {}
            dListAdjustByUser = {}
            for user_id in user_ids:
                for prod_id in all_product_ids:
                    dAdjustments[(user_id,prod_id)] = 0.0
                dGlobalAdjust[user_id] = 0.0
                dListAdjustByUser[user_id] = []
            selection = """
                SELECT user_id, amount, commission, cci_product_id, period_id, cp.code, ap.name, ce.name
                    FROM cci_salesman_commission_exception as ce
                        LEFT OUTER JOIN cci_product as cp ON ( ce.cci_product_id = cp.id )
                        LEFT OUTER JOIN account_period as ap ON ( ce.period_id = ap.id )
                    WHERE period_id in (%s)
            """ % (period_list)
            self.env.cr.execute(selection)
            res = self.env.cr.fetchall()
            for adjus in res:
                if adjus[0] in user_ids:
                    if adjus[1]:
                        # amount - not commission => there MUST be an cci_product_id, else ignored
                        if adjus[3]:
                            key = (adjus[0],adjus[3])
                            dResults[key] += adjus[1]
                    elif adjus[2]:
                        # not amount but commission : if product, adjust the product commission; if not, keep it for global commission at the end of calculation
                        if adjus[3]:
                            dAdjustments[(adjus[0],adjus[3])] += adjus[2]
                        else:
                            dGlobalAdjust[adjus[0]] += adjus[2]
                    list_of_adjustment = dListAdjustByUser[adjus[0]]
                    list_of_adjustment.append( {'period':adjus[6],'desc':adjus[7],'amount':adjus[1] or 0.0,'commission':adjus[2] or 0.0,'cci_product':adjus[5] or '-aucun-'} )
                    dListAdjustByUser[adjus[0]] = list_of_adjustment
            # output of results user by user
            for user_id in user_ids:
                if user_id not in sliced_ids:
                    # output for classic commissions
                    ws = wb.add_sheet(u'Chargé - ' + dUsers[user_id]['name'] )
                    ws.write(0,0,u'Chargé de relation : ' + dUsers[user_id]['name'] )
                    ws.write(1,0,u'Période : de %s à %s' % (from_date,to_date) )
                    ws.write(2,0,u'Objectifs : Année %s' % current_year )
                    ws.write(3,0,u'Date : %s' % datetime.datetime.today().strftime('%d/%m/%Y') )
                    ws.write(5,1,u'Réalisé')
                    ws.write(5,2,u'Objectif')
                    ws.write(5,3,u'Comm. 1,5%')
                    ws.write(5,4,u'Comm. 2,5%')
                    ws.write(5,5,u'B.Cmd -> 12/' + current_year)
                    ws.write(5,6,u'Possible en attente')
                    iline = 6
                    comm_total = 0.0
                    for prod_id in all_product_ids:
                        key = (user_id,prod_id)
                        ws.write(iline,0,dProducts[prod_id]['code'])
                        ws.write(iline,1,round(dResults[key],2))
                        current_objective = dObjectives.has_key( key ) and dObjectives[key] or 0.0
                        ws.write(iline,2,current_objective)
                        if dProducts[prod_id]['commissioned']:
                            if dResults[key] >= current_objective:
                                ws.write(iline,3,0.0)
                                ws.write(iline,4,round( ( dResults[key] * 0.025 ) + dAdjustments[(user_id,prod_id)], 2 ))
                                comm_total += round( ( dResults[key] * 0.025 ) + dAdjustments[(user_id,prod_id)], 2 )
                            else:
                                ws.write(iline,3,round( ( dResults[key] * 0.015 ) + dAdjustments[(user_id,prod_id)], 2 ))
                                ws.write(iline,4,0.0)
                                comm_total += round( ( dResults[key] * 0.015 ) + dAdjustments[(user_id,prod_id)], 2 )
                        else:
                            ws.write(iline,3,0.0)
                            ws.write(iline,4,0.0)
                        ws.write(iline,5,round( dPipeline[key], 2 ))
                        ws.write(iline,6,round( dPossible[key], 2 ))
                        iline += 1
                    # total by user
                    ws.write(iline,0,u'Total commissions dues')
                    ws.write(iline,4,round(comm_total,2))
                    iline += 1
                    ws.write(iline,0,u'Total ajustement globaux')
                    ws.write(iline,4,round(dGlobalAdjust[user_id],2))
                    iline += 1
                    ws.write(iline,0,u'Total commissions déjà payées')
                    already_paid = dPaidUsers.has_key(user_id) and dPaidUsers[user_id] or 0.0
                    ws.write(iline,4,round(already_paid,2))
                    iline += 1
                    ws.write(iline,0,u'Solde à percevoir')
                    ws.write(iline,4,round(comm_total+dGlobalAdjust[user_id]-already_paid,2))
                    
                    # details of adjustments
                    details = dListAdjustByUser[user_id]
                    if details:
                        sorted_details = sorted(details,key=lambda k: k['period'])
                        iline += 2
                        ws.write(iline,0,u'Détails des ajustements')
                        iline += 1
                        ws.write(iline,0,u'Description')
                        ws.write(iline,1,u'Période')
                        ws.write(iline,2,u'Produit commercial')
                        ws.write(iline,3,u'Montant')
                        ws.write(iline,4,u'Commission')
                        iline += 1
                        for line in sorted_details:
                            ws.write(iline,0,line['desc'])
                            ws.write(iline,1,line['period'])
                            ws.write(iline,2,line['cci_product'])
                            ws.write(iline,3,line['amount'])
                            ws.write(iline,4,line['commission'])
                            iline += 1

                    # details of already made payments
                    selection = """
                        SELECT cp.date_payment, ap.name, cp.amount, cp.comments
                            FROM cci_salesman_commission_payment as cp
                                LEFT OUTER JOIN account_period as ap ON ( cp.period_id = ap.id )
                            WHERE period_id in (%s) AND user_id = %s
                            ORDER BY cp.date_payment
                    """ % (period_list,user_id)
                    self.env.cr.execute(selection)
                    res = self.env.cr.fetchall()
                    iline += 2
                    ws.write(iline,0,u'Détails des paiements effectués')
                    iline += 1
                    ws.write(iline,0,u'Date')
                    ws.write(iline,1,u'Période')
                    ws.write(iline,2,u'Montant')
                    ws.write(iline,3,u'Description')
                    iline += 1
                    if res:
                        for line in res:
                            ws.write(iline,0,line[0] and (line[0][8:10]+'/'+line[0][5:7]+'/'+line[0][:4]) or '')
                            ws.write(iline,1,line[1])
                            ws.write(iline,2,line[2])
                            ws.write(iline,3,line[3] or '-')
                            iline += 1
                else:
                    # output for user with sliced commissions
                    ws = wb.add_sheet(u'Chargé - ' + dUsers[user_id]['name'] )
                    ws.write(0,0,u'Chargé de relation : ' + dUsers[user_id]['name'] )
                    ws.write(1,0,u'Période : de %s à %s' % (from_date,to_date) )
                    ws.write(2,0,u'Tranches : Année %s' % current_year )
                    ws.write(3,0,u'Date : %s' % datetime.datetime.today().strftime('%d/%m/%Y') )
                    ws.write(5,0,u'Réalisé global')
                    ws.write(5,2,u'Tranche')
                    ws.write(5,3,u'Taux')
                    ws.write(5,4,u'Montant')
                    ws.write(5,5,u'Commission' + current_year)
                    iline = 6
                    ca_total = 0.0
                    comm_total = 0.0
                    for prod_id in all_product_ids:
                        key = (user_id,prod_id)
                        #ws.write(iline,0,dProducts[prod_id]['code'])
                        if user_id == 66:
                            if prod_id == 14:
                                ca_total += round(dResults[key],2)
                        else:
                            ca_total += round(dResults[key],2)
                    full_slices = sliced_slices[user_id]
                    ws.write(iline,0,ca_total)
                    ws.write(iline+len(full_slices),4,ca_total)
                    for slice_def in full_slices:
                        ws.write(iline,2,str(int(slice_def['amount_from']))+'-'+str(int(slice_def['amount_to'])))
                        ws.write(iline,3,str(round(slice_def['rate']*100,2)))
                        if ca_total <= slice_def['amount_to'] and ca_total >= slice_def['amount_from']:
                            current_amount = ca_total - slice_def['amount_from']
                        elif ca_total > slice_def['amount_to']:
                            current_amount = slice_def['amount_to'] - slice_def['amount_from']
                        else:
                            current_amount = 0.0
                        ws.write(iline,4,round(current_amount,2))
                        ws.write(iline,5,round(current_amount*slice_def['rate'],2))
                        comm_total += round(current_amount*slice_def['rate'],2)
                        iline += 1
                    ws.write(iline,5,comm_total)
                    iline += 2
                    
                    # total by user
                    ws.write(iline,0,u'Total commissions dues')
                    ws.write(iline,4,round(comm_total,2))
                    iline += 1
                    ws.write(iline,0,u'Total ajustement globaux')
                    ws.write(iline,4,round(dGlobalAdjust[user_id],2))
                    iline += 1
                    ws.write(iline,0,u'Total commissions déjà payées')
                    already_paid = dPaidUsers.has_key(user_id) and dPaidUsers[user_id] or 0.0
                    ws.write(iline,4,round(already_paid,2))
                    iline += 1
                    ws.write(iline,0,u'Solde à percevoir')
                    ws.write(iline,4,round(comm_total+dGlobalAdjust[user_id]-already_paid,2))
                    
                    # details of adjustments
                    details = dListAdjustByUser[user_id]
                    if details:
                        sorted_details = sorted(details,key=lambda k: k['period'])
                        iline += 2
                        ws.write(iline,0,u'Détails des ajustements')
                        iline += 1
                        ws.write(iline,0,u'Description')
                        ws.write(iline,1,u'Période')
                        ws.write(iline,2,u'Produit commercial')
                        ws.write(iline,3,u'Montant')
                        ws.write(iline,4,u'Commission')
                        iline += 1
                        for line in sorted_details:
                            ws.write(iline,0,line['desc'])
                            ws.write(iline,1,line['period'])
                            ws.write(iline,2,line['cci_product'])
                            ws.write(iline,3,line['amount'])
                            ws.write(iline,4,line['commission'])
                            iline += 1

                    # details of already made payments
                    selection = """
                        SELECT cp.date_payment, ap.name, cp.amount, cp.comments
                            FROM cci_salesman_commission_payment as cp
                                LEFT OUTER JOIN account_period as ap ON ( cp.period_id = ap.id )
                            WHERE period_id in (%s) AND user_id = %s
                            ORDER BY cp.date_payment
                    """ % (period_list,user_id)
                    self.env.cr.execute(selection)
                    res = self.env.cr.fetchall()
                    iline += 2
                    ws.write(iline,0,u'Détails des paiements effectués')
                    iline += 1
                    ws.write(iline,0,u'Date')
                    ws.write(iline,1,u'Période')
                    ws.write(iline,2,u'Montant')
                    ws.write(iline,3,u'Description')
                    iline += 1
                    if res:
                        for line in res:
                            ws.write(iline,0,line[0] and (line[0][8:10]+'/'+line[0][5:7]+'/'+line[0][:4]) or '')
                            ws.write(iline,1,line[1])
                            ws.write(iline,2,line[2])
                            ws.write(iline,3,line[3] or '-')
                            iline += 1
                
            wb.save('commissions.xls')
            result_file = open('commissions.xls','rb').read()

            # give the result to the user
            msg ='Save the File with '".xls"' extension.'
            commision_file = base64.encodestring(result_file)
        else:
            msg = 'No results'
            
        ctx = self.env.context.copy()    
        ctx.update({'msg': msg,'name': 'actions.xls', 'commissions': commision_file})
        result = {
            'name': _('Notification'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.extract.commissions2',
            'target': 'new',
            'context': ctx,
            'type': 'ir.actions.act_window'
        }
        return result

class wizard_extract_commissions2(models.TransientModel):
    _name = 'wizard.extract.commissions2'
    msg = fields.Text(string ='File Created', readonly=True)
    commissions = fields.Binary(string= 'Prepared file', readonly=True)
    name = fields. Char(string ='File Name')
    
    @api.model
    def default_get(self,fields):
        res = super(wizard_extract_commissions2, self).default_get(fields)
        context = dict(self._context or {})
        res.update({'name':'commissions.xls','msg': context.get('msg',''), 'commissions': context.get('commissions',False)})
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

