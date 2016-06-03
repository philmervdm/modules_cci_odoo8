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
# import re
from openerp import tools
import base64
from openerp import models, fields, api, _

def _correct_escape(string):
    return string.replace("\\" + "'", "'")

class cci_memberdirectory_internal_validate(models.TransientModel):
    _name = 'cci.memberdirectory.internal.validate'
    
    @api.multi
    def try_confirm(self):
        recorded = 0
        bloqued = 0
        obj_proxy = self.env['directory.address.proxy']
        proxies = obj_proxy.search([('user_validated', '=', True), ('internal_validated', '=', False)])
        if proxies:
            for proxy in proxies:
                # new_values = self.read(cr, uid, ids, ['user_validated','internal_validated','vat_num','new_vat_num','final_vat_num','complete_name','new_complete_name','final_partner_name','final_address_name','new_zip_code','new_city','final_zip_id','new_desc_activ','final_desc_activ','final_addr_desc_activ','partner_id'], context=context)[0]
                try_to_record = True
                if proxy.new_complete_name and (_correct_escape(proxy.new_complete_name) != proxy.complete_name) and not (proxy.final_partner_name or proxy.final_address_name):
                    try_to_record = False
                if try_to_record and ((proxy.new_zip_code or proxy.new_city) and not proxy.final_zip_id):
                    try_to_record = False
                if try_to_record and proxy.new_desc_activ and not (proxy.final_desc_activ or proxy.final_addr_desc_activ):
                    try_to_record = False
                old_vat_num = (proxy.vat_num or '').replace('/', '').replace('-', '').replace('.', '').replace(' ', '')
                if proxy.new_vat_num and old_vat_num <> proxy.final_vat_num:
                    # check if not existing new vat num
                    same_vat_ids = self.env['res.partner'].search([('vat', '=', proxy.final_vat_num)], limit=1)
                    if same_vat_ids:
                        if len(same_vat_ids) > 1 or proxy.partner_id.id <> same_vat_ids[0]:
                            try_to_record = False
                if try_to_record:
                    proxy.but_confirm_changes()
                    recorded += 1
                else:
                    bloqued += 1
        msg = u'Enregistrés : %i\nEn attente de gestion manuelle : %i' % (recorded, bloqued)
        
        ctx = self.env.context.copy()
        ctx.update({'msg':msg})
        
        view = self.env.ref('cci_memberdirectory.view_cci_memberdirectory_internal_validate_msg')
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cci.memberdirectory.internal.validate.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class cci_memberdirectory_internal_validate_msg(models.TransientModel):
    _name = 'cci.memberdirectory.internal.validate.msg'
    
    msg = fields.Text(string='Details', readonly=True)
    
    @api.model
    def default_get(self, fields):
        rec = super(cci_memberdirectory_internal_validate_msg, self).default_get(fields)
        if self.env.context.get('msg'):
            rec['msg'] = self.env.context['msg']
        return rec
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: