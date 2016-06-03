# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 CCI Connect ASBL. (http://www.cciconnect.be) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from openerp import models, fields, api , _ 
import datetime

class delayed_partner(models.Model):
    _name = "cci_connect.delayed_partner"
    _description = "store asked changes for partner and address from internet site"
    
    @api.multi
    def _partner_title_get(self):
        obj = self.env['res.partner.title']
        ids = obj.search([('domain', '=', 'partner')])
        res = ids.read(['shortcut','name'])
        return [(r['shortcut'], r['name']) for r in res] +  [('','')]
    
    partner_id = fields.Many2one('res.partner','Partner',required=True)
    address_id = fields.Many2one('res.partner','Address',required=True)
    partner_name = fields.Char('Name', size=128 )
    partner_title = fields.Char('Title', size=16, translate=True)
    website = fields.Char('Website',size=64)
    vat =  fields.Char('VAT',size=32)
    searching =  fields.Text('Searching')
    selling =  fields.Text('Selling')
    address_name =  fields.Char('Address Name', size=64)
    street =  fields.Char('Street', size=128)
    street2 =  fields.Char('Street2', size=128)
    zip_id = fields.Many2one('res.partner.zip','Zip')
    country_id =  fields.Many2one('res.country', 'Country')
    email =  fields.Char('Site E-Mail', size=240)
    phone =  fields.Char('Site Phone', size=64)
    fax =  fields.Char('Site Fax', size=64)
    activity =  fields.Text('Activity')
    old_functions =  fields.Char('Old functions', size=255)
    asker_id =  fields.Many2one('res.partner','Asker for Change')
    state =  fields.Selection([('draft','Draft'),('done','Done'),('cancel','Canceled')],'State')
    state_changed =  fields.Date('Status Changed')
    final_partner_name =  fields.Char('Final Partner Name', size=128 )
    #'final_partner_title =  fields.Char('Final Title', size=16),
    final_partner_title =  fields.Selection(_partner_title_get, 'Title', size=32)
    #'final_partner_title =  fields.Many2one('res.partner.title','Final Title',domain="[('domain','=','partner')]"),
    final_website =  fields.Char('Final Website',size=64)
    final_vat =  fields.Char('Final VAT',size=32)
    final_searching =  fields.Text('Final Searching')
    final_selling =  fields.Text('Final Selling')
    final_address_name =  fields.Char('Final Address Name', size=64)
    final_street =  fields.Char('Final Street', size=128)
    final_street2 =  fields.Char('Final Street2', size=128)
    final_zip_id = fields.Many2one('res.partner.zip','Final Zip')
    final_country_id =  fields.Many2one('res.country', 'Final Country')
    final_email =  fields.Char('Final Site E-Mail', size=240)
    final_phone =  fields.Char('Final Site Phone', size=64)
    final_fax =  fields.Char('Final Site Fax', size=64)
    final_activity =  fields.Text('Final activity')
    current_partner_name =  fields.Char(related = 'partner_id.name', string="Current Partner Name", store=False)
    current_partner_title =  fields.Char(related = 'partner_id.title.name', string="Current Partner Title", store=False)
    current_website =  fields.Char(related = 'partner_id.website',string="Current Partner WebSite", store=False)
    current_vat = fields.Char(related = 'partner_id.vat',string="Current Partner VAT", store=False)
    current_address_name =  fields.Char(related ='address_id.name',string="Current Partner VAT", store=False)
    current_street =  fields.Char(related ='address_id.street',string="Current Partner VAT", store=False)
    current_street2 =  fields.Char(related ='address_id.street2',string="Current Partner VAT", store=False)
    current_zip_id =  fields.Many2one(related ='address_id.zip_id', relation="res.partner.zip",string="Current Address Zip Code", store=False)
    current_country_id =  fields.Many2one(related ='address_id.country_id',relation="res.country",string="Current Address Country", store=False)
    current_email =  fields.Char(related ='address_id.email',string="Current Site EMail", store=False)
    current_phone =  fields.Char(related ='address_id.phone',string="Current Site Phone", store=False)
    current_fax =  fields.Char(related ='address_id.fax',string="Current Site Fax", store=False)
    current_activity =  fields.Text(related ='partner_id.activity_description',string='Current Activity', store=False)
    
    @api.multi
    def but_cancel(self):
        self.write({'state':'cancel','state_changed':datetime.date.today().strftime('%Y-%m-%d')})
        return True
    
    @api.multi
    def but_confirm_changes(self):
        self.write({'state':'done','state_changed':datetime.date.today().strftime('%Y-%m-%d')})
        for delay in self:
            if delay.final_partner_name or delay.final_partner_title or delay.final_website or delay.final_vat or delay.final_activity:
                obj_partner = self.env['res.partner']
                changes = {}
                if delay.final_partner_name:
                    changes['name'] = delay.final_partner_name
                if delay.final_partner_title:
                    changes['title'] = delay.final_partner_title
                if delay.final_website:
                    changes['website'] = delay.final_website
                if delay.final_vat:
                    changes['vat'] = delay.final_vat
                if delay.final_activity:
                    changes['activity_description'] = delay.final_activity
                ctx = {'lang':'fr_FR'}
                delay.partner_id.with_context(ctx).write(changes)
                
            if delay.final_address_name or delay.final_street or delay.final_street2 or delay.final_zip_id \
                or delay.final_country_id or delay.final_email or delay.final_phone or delay.final_fax:
                obj_addr = self.env['res.partner']
                changes = {}
                if delay.final_address_name:
                    changes['name'] = delay.final_address_name
                if delay.final_street:
                    changes['street'] = delay.final_street
                if delay.final_street2:
                    changes['street2'] = delay.final_street2
                if delay.final_email:
                    changes['email'] = delay.final_email
                if delay.final_phone:
                    changes['phone'] = delay.final_phone
                if delay.final_fax:
                    changes['fax'] = delay.final_fax
                delay.address_id.write(changes)
                
            if delay.final_searching:
                obj_partner = self.env['res.partner']
                query = """
                    select a.id from partner_question_rel as rel, crm_profiling_answer as a
                    where a.question_id = 101 and rel.answer = a.id and rel.partner =%d limit 1"""% delay.partner_id.id
                self.env.cr.execute(query)
                answer_id = self.env.cr.fetchone()
                if answer_id:
                    answer_id = answer_id[0]
                    obj_answer = self.env['crm_profiling.answer']
                    obj_answer.write([answer_id], {'name':'/','text':delay.final_searching})
                else:
                    obj_answer = self.env['crm_profiling.answer']
                    new_id = obj_answer.create({'question_id':101,'name':'/','text':delay.final_searching})
                    query = """
                        select distinct(answer) from partner_question_rel
                        where partner =%d"""% delay.partner_id.id
                    self.env.cr.execute(query)
                    temp = []
                    for x in self.env.cr.fetchall():
                        temp.append(x[0])
                    temp.append(new_id.id)
                    delay.partner_id.write({'answers_ids':[[6,0,temp]]})
            
            if delay.final_selling:
                obj_partner = self.env['res.partner']
                query = """
                    select a.id from partner_question_rel as rel, crm_profiling_answer as a
                    where a.question_id = 102 and rel.answer = a.id and rel.partner =%d limit 1"""% delay.partner_id.id
                self.env.cr.execute(query)
                answer_id = self.env.cr.fetchone()
                if answer_id:
                    answer_id = answer_id[0]
                    obj_answer = self.env['crm_profiling.answer']
                    obj_answer.write([answer_id], {'name':'/','text':delay.final_selling})
                else:
                    obj_answer = self.env['crm_profiling.answer']
                    new_id = obj_answer.create({'question_id':102,'name':'/','text':delay.final_selling})
                    query = """
                        select distinct(answer) from partner_question_rel
                        where partner =%d"""% delay.partner_id.id
                    self.env.cr.execute(query)
                    temp = []
                    for x in self.env.cr.fetchall():
                        temp.append(x[0])
                    temp.append(new_id.id)
                    delay.partner_id.write({'answers_ids':[[6,0,temp]]})
        return True
