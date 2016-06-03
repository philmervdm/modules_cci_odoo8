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
import time
import datetime
#import re
import base64
from xlwt import *
from openerp import api, fields, models, _

class extract_actions(models.TransientModel):
    _name="extract.actions"
    
    date_from = fields.Date(string='From', required=True)
    to = fields.Date(string='To', required=True) 
    
    @api.multi
    def get_file(self):
        res = {}
        actions_file = False
        obj_history = self.env['res.partner.history']
        if self.date_from > self.to:
            date_from = self.to
            date_to   = self.date_from
        else:
            date_from = self.date_from
            date_to   = self.to
        #valid_ids = []
        #if data['form']['only_commercials']:
        #    obj_ccicontact = pooler.get_pool(cr.dbname).get('cci.contact')
        #    contact_ids = obj_cciconnect.search(cr,uid,[])
        #    contacts = obj_cciconnect.read(cr,uid,contact_ids,['user'])
        #    for comm in contacts:
        #        if comm['user']:
        #            valid_ids.append( comm['user'][0] )
        #else:
        #    obj_resusers = pooler.get_pool(cr.dbname).get('res.users')
        #    valid_ids = obj_resusers.search(cr,uid,[])
        action_ids = obj_history.search([('date','>=',date_from),('date','<=',date_to)])
        if action_ids:
            actions = action_ids.read(['action','cci_contact','product','state'])
            #
            action_types = [('appel_sortant','Appel sortant'),
                                ('appel_entrant','Appel entrant'),
                                ('commando','Commando'),
                                ('mail','Mail'),
                                ('site','Site Internet'),
                                ('meeting_cci','Meeting CCI'),
                                ('meeting_externe','Meeting externe'),
                                ('midi','Midi'),
                                ('rdv','RDV'),
                                ('publication','Publication')]
            #
            obj_cciproduct = self.env['cci.product']
            prod_ids = obj_cciproduct.search([])
            products = prod_ids.read(['id','name','code'])
            #
            obj_ccicontact = self.env['cci.contact']
            contact_ids = obj_ccicontact.search([])
            contacts = contact_ids.read(['id','name','user'])
            #
            totaux_usertype = {}
            totaux_userprod = {}
            # init totals to 0
            for contact in contacts:
                for action_type in action_types:
                    totaux_usertype[(contact['id'],action_type[0])] = 0
                for prod in products:
                    totaux_userprod[(contact['id'],prod['id'])] = 0
                totaux_usertype[(contact['id'],0)] = 0
                totaux_userprod[(contact['id'],0)] = 0
            # cumulate each action in each totals
            for action in actions:
                if action['cci_contact']:
                    if action['cci_contact'][0] in contact_ids.ids:
                        if action['state'] == 'closed':
                            if action['action']:
                                totaux_usertype[(action['cci_contact'][0],action['action'])] += 1
                            else:
                                totaux_usertype[(action['cci_contact'][0],0)] += 1
                            if action['product']:
                                totaux_userprod[(action['cci_contact'][0],action['product'][0])] += 1
                            else:
                                totaux_userprod[(action['cci_contact'][0],0)] += 1
                        else:
                            totaux_usertype[(action['cci_contact'][0],0)] += 1
                            totaux_userprod[(action['cci_contact'][0],0)] += 1
            #
            wb1 = Workbook()
            # defining output styles
            fntMainTitle = Font()
            fntMainTitle.height = 25*20
            fntMainTitle.bold = True
            fntMainTitle.name = "Arial"
            #
            fntTitle = Font()
            fntTitle.height = 15*20
            fntTitle.bold = True
            fntTitle.name = "Arial"
            #
            fntData = Font()
            fntData.height = 15*20
            fntData.name = "Arial"
            #
            all_thick_borders = Borders()
            all_thick_borders.left = 3
            all_thick_borders.right = 3
            all_thick_borders.top = 3
            all_thick_borders.bottom = 3
            #
            left_thick_borders = Borders()
            left_thick_borders.left = 3
            left_thick_borders.top = 3
            left_thick_borders.bottom = 3
            #
            inside_thick_borders = Borders()
            inside_thick_borders.top = 3
            inside_thick_borders.bottom = 3
            #
            right_thick_borders = Borders()
            right_thick_borders.right = 3
            right_thick_borders.top = 3
            right_thick_borders.bottom = 3
            #
            all_thin_borders = Borders()
            all_thin_borders.left = 1
            all_thin_borders.right = 1
            all_thin_borders.top = 1
            all_thin_borders.bottom = 1
            #
            styleMainTitle = XFStyle()
            styleMainTitle.font = fntMainTitle
            #styleMainTitle.alignment = 0x02 # Center
            styleMainTitle.pattern.set_pattern_back_colour(0x0B) # cyan
            styleMainTitle.borders = all_thick_borders
            #
            styleTitle = XFStyle()
            styleTitle.font = fntTitle
            #styleTitle.alignment = 0x02 # Center
            styleTitle.pattern.set_pattern_back_colour(0x0B) # lime
            styleTitle.borders = inside_thick_borders
            #
            styleLeftTitle = XFStyle()
            styleLeftTitle.font = fntTitle
            #styleLeftTitle.alignment = 0x02 # Center
            styleLeftTitle.pattern.set_pattern_back_colour(0x0B) # lime
            styleLeftTitle.borders = left_thick_borders
            #
            styleRightTitle = XFStyle()
            styleRightTitle.font = fntTitle
            #styleRightTitle.alignment = 0x02 # Center
            styleRightTitle.pattern.set_pattern_back_colour(0x0B) # lime
            styleRightTitle.borders = right_thick_borders
            #
            styleData = XFStyle()
            styleData.font = fntData
            #styleData.alignment = 0x02 # Center
            styleData.borders = all_thin_borders
            
            # worksheet with totals by users and types of actions
            ws1 = wb1.add_sheet('Actions par Type')
            ws1.write_merge(0,0,0,len(action_types)+2,"Actions commerciales du %s au %s" % (date_from,date_to), styleMainTitle )
            ws1.row(0).height = 27*20
            ws1.write(2,0,"User/Type", styleLeftTitle)
            action_num = 1
            total_col = {}
            for action_type in action_types:
                ws1.write(2,action_num,action_type[1],styleTitle)
                total_col[action_num] = 0
                action_num += 1
            total_col[action_num] = 0
            ws1.write(2,action_num,u'Ouverts/Indéterminés',styleTitle)
            action_num += 1
            ws1.write(2,action_num,'TOTAL',styleRightTitle)
            total_gen = 0
            contact_num = 4
            for contact in contacts:
                ws1.write(contact_num,0,contact['name'],styleData)
                col = 1
                total = 0
                for action_type in action_types:
                    ws1.write(contact_num,col,totaux_usertype[(contact['id'],action_type[0])],styleData)
                    total += totaux_usertype[(contact['id'],action_type[0])]
                    total_col[col] += totaux_usertype[(contact['id'],action_type[0])]
                    total_gen += totaux_usertype[(contact['id'],action_type[0])]
                    col += 1
                ws1.write(contact_num,col,totaux_usertype[(contact['id'],0)],styleData)
                total += totaux_usertype[(contact['id'],0)]
                total_col[col] += totaux_usertype[(contact['id'],0)]
                total_gen += totaux_usertype[(contact['id'],0)]
                col +=1
                ws1.write(contact_num,col,total,styleData)
                ws1.row(contact_num).height = 300
                contact_num += 1
            col = 1
            contact_num += 1
            ws1.write(contact_num,0,u'Total Salesman',styleLeftTitle)
            for action_type in action_types:
                ws1.write(contact_num,col,total_col[col],styleTitle)
                col += 1
            ws1.write(contact_num,col,total_col[col],styleTitle)
            col += 1
            ws1.write(contact_num,col,total_gen,styleRightTitle)

            # worksheet with totals by users and cci.products
            ws2 = wb1.add_sheet('Actions par Produit')
            ws2.write_merge(0,0,0,len(products)+2,"Actions par produit du %s au %s" % (date_from,date_to),styleMainTitle)
            ws2.write(2,0,"User/Produit",styleLeftTitle)
            prod_num = 1
            total_col = {}
            for prod in products:
                ws2.write(2,prod_num,prod['code'],styleTitle)
                total_col[prod_num] = 0
                prod_num += 1
            total_col[prod_num] = 0
            ws2.write(2,prod_num,u'Ouvert/Indéterminé',styleTitle)
            prod_num += 1
            ws2.write(2,prod_num,'TOTAL',styleRightTitle)
            total_gen = 0
            contact_num = 4
            for contact in contacts:
                ws2.write(contact_num,0,contact['name'],styleData)
                col = 1
                total = 0
                for prod in products:
                    ws2.write(contact_num,col,totaux_userprod[(contact['id'],prod['id'])],styleData)
                    total += totaux_userprod[(contact['id'],prod['id'])]
                    total_col[col] += totaux_userprod[(contact['id'],prod['id'])]
                    total_gen += totaux_userprod[(contact['id'],prod['id'])]
                    col += 1
                ws2.write(contact_num,col,totaux_userprod[(contact['id'],0)],styleData)
                total += totaux_userprod[(contact['id'],0)]
                total_col[col] += totaux_userprod[(contact['id'],0)]
                total_gen += totaux_userprod[(contact['id'],0)]
                col +=1
                ws2.write(contact_num,col,total,styleData)
                contact_num += 1
            col = 1
            contact_num += 1
            ws2.write(contact_num,0,u'Total Salesman',styleLeftTitle)
            for prod in products:
                ws2.write(contact_num,col,total_col[col],styleTitle)
                col += 1
            ws2.write(contact_num,col,total_col[col],styleTitle)
            col += 1
            ws2.write(contact_num,col,total_gen,styleRightTitle)
            #
            wb1.save('actions.xls')
            result_file = open('actions.xls','rb').read()

            # give the result to the user
            msg ='Save the File with '".xls"' extension.'
            actions_file = base64.encodestring(result_file)
        else:
            msg='No actions found between these two dates : %s -> %s' % (date_from,date_to)
        
        ctx = self.env.context.copy()
        ctx['msg'] = msg
        ctx['actions'] = actions_file
        result = {
            'name': _('Notification'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.extract.actions2',
            'target': 'new',
            'context': ctx,
            'type': 'ir.actions.act_window'
        }
        return result
    
class wizard_extract_actions2(models.TransientModel):
    _name = 'wizard.extract.actions2'
    msg = fields.Text(string ='File Created', readonly=True)
    actions = fields.Binary(string= 'Prepared file', readonly=True)
    name = fields. Char(string ='File Name')
    
    @api.model
    def default_get(self,fields):
        res = super(wizard_extract_actions2, self).default_get(fields)
        context = dict(self._context or {})
        res.update({
            'msg': context.get('msg'),
            'actions': context.get('actions',False),
            'name': 'actions.xls'
        })
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

