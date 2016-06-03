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
from openerp import models, fields ,api , _
from openerp.exceptions import Warning
import time
import datetime

class select_criteria(models.TransientModel):
    _name = 'select.criteria'
    
    select = fields.Selection(string = 'Select Criteria', selection = [('lines', 'Criteria about amount sold and membership state'),
                                                                       ('crm','Criteria about registration to specified event')], default='lines')
    
    @api.multi
    def go(self):
        if self.select == 'lines':
            return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'choose.lines',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            }
        else:
            return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'choose.crm',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            }
        
class choose_crm(models.TransientModel):
    _name = 'choose.crm'
    
    section = fields.Many2one('crm.case.section', string='Event', required=True, domain = "[('name','like','Events')]")
#     state = fields.Selection(string = 'State', selection=[('draft','Draft'),('open','Open'),('cancel', 'Cancel'),('done', 'Close'),('pending','Pending')],
#                              required = True, default='open', help='The wizard will look if a partner has a registration of that specified state for the chosen event')
#     
    stage_id = fields.Many2one('crm.case.stage',string = 'Stage', required=True,help='The wizard will look if a partner has a registration of that specified state for the chosen event')
    removing_from_list = fields.Boolean(string='Keep only fetching partners',help= """The result will be a list of partner:
                                        \n* Either only the fetching partners, if this box is checked.
                                        \n* Otherwise, all the partners minus the ones that fetch the criteria.""")
    
    @api.multi
    def open_window_selected_partners(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']

        result = mod_obj.browse(mod_obj._get_id('base', 'action_partner_form'))
        list_ids = []
        
        self.env.cr.execute("select distinct(partner_id),section_id,stage_id from crm_lead where section_id=%s and stage_id=%s and (partner_id is not null)", (self.section.id , self.stage_id.id))
        p_ids = self.env.cr.fetchall()
        list_ids = [x[0] for x in p_ids]
        action = act_obj.browse(result.res_id)
        result = action.read([])[0]
        if self.removing_from_list:
            result['domain'] = [('id', 'in', list_ids)]
        else:
            result['domain'] = [('id', 'not in', list_ids)]
        return result
                    
class choose_lines(models.TransientModel):
    _name = 'choose.lines'
    
    date_from = fields.Date(string = 'Start of period',required =True)
    date_to = fields.Date(string='End of period', required=True, default=time.strftime('%Y-%m-%d'))
    amount = fields.Float(string = 'Amount', required=True, default=0.0)
    member_state = fields.Selection(string = 'Current Membership state',
                                    selection = [('none', 'Non Member'),('canceled','Canceled Member'),('old','Old Member'),('waiting','Waiting Member'),('invoiced','Invoiced Member'),('free','Free Member'),('paid','Paid Member')],
                                    required = True, help= 'The wizard will only pay attention to partners in this membership state')
    removing_from_list = fields.Boolean(string = 'Keep only fetching partners', help = """The result will be a list of partner:
                                        \n* Either only the fetching partners, if this box is checked.
                                        \n* Otherwise, all the partners minus the ones that fetch the criteria.""")
    
    @api.model
    def default_get(self,fields):
        res = super(choose_lines,self).default_get(fields)
        today = datetime.datetime.today()
        from_date = today - datetime.timedelta(30)
        res['date_from'] = from_date.strftime('%Y-%m-%d')
        res['member_state'] = 'free'
        return res
    
    @api.multi
    def open_window_selected_partners(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']

        result = mod_obj.browse(mod_obj._get_id('base', 'action_partner_form'))
        list_ids = []
        
        if not self.amount:
            raise Warning('Warning','Amount should be greater than zero')
        
        self.env.cr.execute("select distinct(partner_id) from account_move_line where credit>=%s and (date between to_date(%s,'yyyy-mm-dd') and to_date(%s,'yyyy-mm-dd')) and (partner_id is not null)", (self.amount, self.date_from, self.date_to))
        entry_lines = self.env.cr.fetchall()
        entry_ids = self.env['res.partner'].browse([x[0] for x in  entry_lines])
        a_id = entry_ids.read(['membership_state'])
        for i in range(0, len(a_id)):
            if a_id[i]['membership_state'] == self.member_state:
                list_ids.append(a_id[i]['id'])

        action = act_obj.browse(result.res_id)
        result = action.read([])[0]
        if self.removing_from_list:
            result['domain'] = [('id', 'in', list_ids)]
        else:
            result['domain'] = [('id', 'not in', list_ids)]
        return result
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

