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
from openerp import api, fields, models, _
import time
import datetime
#import re
import base64
from xlwt import *

class extract_pipeline(models.TransientModel):
    _name = 'extract.pipeline'
    
    year = fields.Integer(string='Year', help='If year given, only interests for that year will be extracted')
    
    @api.multi
    def get_file(self):
        obj_interest = self.env['res.partner.interest']
        year = 0
        res = {}
        pipeline = False
        if self.year:
            if year < 100 and year > 0:
                year = 2000 + year
        if year:
            int_ids = obj_interest.search([('active','=',True),('year','=',year)])
        else:
            int_ids = obj_interest.search([('active','=',True)])
        
        if int_ids:
            interests = int_ids.read(['cci_contact_follow','product'])
            #
            obj_cciproduct = self.env['cci.product']
            prod_ids = obj_cciproduct.search([])
            products = prod_ids.read(['id','name','code'])
            #
            obj_ccicontact = self.env['res.users']
            contact_ids = obj_ccicontact.search([])
            contacts = contact_ids.read(['id','name'])
            #
            totaux_userprod = {}
            # init totals to 0
            for contact in contacts:
                for product in products:
                    totaux_userprod[(contact['id'],product['id'])] = 0
                totaux_userprod[(contact['id'],0)] = 0
            for product in products:
                totaux_userprod[(0,product['id'])] = 0
            totaux_userprod[(0,0)] = 0
            # cumulate each action in each totals
            for interest in interests:
                if interest['cci_contact_follow'] and interest['cci_contact_follow'][0] in contact_ids.ids:
                    user_id = interest['cci_contact_follow'][0]
                else:
                    user_id = 0
                if interest['product'] and interest['product'][0] in prod_ids.ids:
                    product_id = interest['product'][0]
                else:
                    product_id = 0
                totaux_userprod[(user_id,product_id)] += 1
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
            ws1 = wb1.add_sheet('Pipeline')
            
            if year:
                ws1.write_merge(0,0,0,len(prod_ids)+2,"Pipeline pour l'année %s" % str(year), styleMainTitle )
            else:
                ws1.write_merge(0,0,0,len(prod_ids)+2,"Pipeline", styleMainTitle )
            ws1.row(0).height = 27*20
            ws1.write(2,0,"User/Product", styleLeftTitle)
            product_num = 1
            total_col = {}
            for product in products:
                ws1.write(2,product_num,product['code'],styleTitle)
                total_col[product_num] = 0
                product_num += 1
            total_col[product_num] = 0
            ws1.write(2,product_num,u'Indéterminés',styleTitle)
            product_num += 1
            ws1.write(2,product_num,'TOTAL',styleRightTitle)
            total_gen = 0
            contact_num = 4
            for contact in contacts:
                # check if at least one interest for this contact
                found = False
                for product in products:
                    if totaux_userprod[(contact['id'],product['id'])] > 0:
                        found = True
                        break
                if found:
                    ws1.write(contact_num,0,contact['name'],styleData)
                    col = 1
                    total = 0
                    for product in products:
                        ws1.write(contact_num,col,totaux_userprod[(contact['id'],product['id'])],styleData)
                        total += totaux_userprod[(contact['id'],product['id'])]
                        total_col[col] += totaux_userprod[(contact['id'],product['id'])]
                        total_gen += totaux_userprod[(contact['id'],product['id'])]
                        col += 1
                    ws1.write(contact_num,col,totaux_userprod[(contact['id'],0)],styleData)
                    total += totaux_userprod[(contact['id'],0)]
                    total_col[col] += totaux_userprod[(contact['id'],0)]
                    total_gen += totaux_userprod[(contact['id'],0)]
                    col +=1
                    ws1.write(contact_num,col,total,styleData)
                    ws1.row(contact_num).height = 300
                    contact_num += 1
            col = 1
            contact_num += 1
            ws1.write(contact_num,0,u'Total Salesman',styleLeftTitle)
            for product in products:
                ws1.write(contact_num,col,total_col[col],styleTitle)
                col += 1
            ws1.write(contact_num,col,total_col[col],styleTitle)
            col += 1
            ws1.write(contact_num,col,total_gen,styleRightTitle)
            #
            wb1.save('pipeline.xls')
            result_file = open('pipeline.xls','rb').read()

            # give the result to the user
            msg ='Save the File with '".xls"' extension.'
            pipeline = base64.encodestring(result_file)
        else:
            msg = 'No interets found'
            
        ctx = self.env.context.copy()
        ctx['msg'] = msg
        ctx['pipeline'] = pipeline
        result = {
            'name': _('Notification'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.extract.pipeline2',
            'target': 'new',
            'context': ctx,
            'type': 'ir.actions.act_window'
        }
        return result
    
class wizard_extract_pipeline2(models.TransientModel):
    _name = 'wizard.extract.pipeline2'
    msg = fields.Text(string ='File Created', readonly=True)
    pipeline = fields.Binary(string= 'Prepared file', readonly=True)
    name = fields. Char(string ='File Name')
    
    @api.model
    def default_get(self,fields):
        res = super(wizard_extract_pipeline2, self).default_get(fields)
        context = dict(self._context or {})
        res.update({
            'msg': context['msg'],
            'pipeline': context['pipeline'],
            'name': 'pipeline.xls'
        })
        return res
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

