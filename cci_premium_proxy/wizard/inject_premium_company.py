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
from openerp import models,fields,api , _
from openerp.exceptions import Warning
import datetime

class inject_premium_company(models.TransientModel):
    
    _name = 'inject.premium.company'
    
    partner_id = fields.Many2one('res.partner','Partner')
    address_id = fields.Many2one('res.partner','Address', domain = "[('parent_id','=',partner_id)]")
    address_work_id = fields.Many2one('res.partner', 'Address', domain = "[('parent_id','=',partner_id)]")
    
    @api.multi
    def inject_company(self):
        company_obj = self.env['premium_company']
        if not self.partner_id and self.address_id:
            raise Warning('You can\'t give an address and no partner.\n\nAlways select a partner, then an address !')
        else:
            error_msg = company_obj._try_inject_company(self.env.context.get('active_id',False),self.partner_id.id,self.address_id and self.address_id.id or False,self.address_work_id and self.address_work_id.id or False,'wizard')
            if not error_msg or error_msg == 'Partner and Address Injected' or error_msg == 'Partner and Address Injected/Created':
                msg = 'Company fully injected'
            else:
                msg = 'Not injected.\n\nReason : %s' % error_msg
        
        ctx = self.env.context.copy()
        ctx.update({'msg':msg})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'inject.premium.company.msg',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }
        
class inject_premium_company_msg(models.TransientModel):
    _name = 'inject.premium.company.msg'
    
    msg = fields.Text(string='Injection Results', readonly=True)
    
    @api.model
    def default_get(self, fields):
        res = super(inject_premium_company_msg, self).default_get(fields)
        res.update({'msg': self.env.context.get('msg','')})
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

