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

import datetime
from openerp import models, fields, api, _

def _correct_escape(string):
    return string.replace("\\" + "'", "'")

class cci_memberdirectory_manual_confirm(models.TransientModel):
    _name = 'cci.memberdirectory.manual.confirm'
    
    @api.multi
    def manual_confirm(self):
        if len(self.env.context['active_ids']) > 1:
            msg = u'Vous ne pouvez confirmer manuellement qu\'une fiche à la fois'
        else:
            obj_proxy = self.env['directory.address.proxy']
            proxy = obj_proxy.browse(self.env.context['active_id'])
            if proxy.user_validated:
                if not proxy.internal_validated:
                    # new_values = self.read(cr, uid, ids, ['user_validated','internal_validated','vat_num','new_vat_num','final_vat_num','complete_name','new_complete_name','final_partner_name','final_address_name','new_zip_code','new_city','final_zip_id','new_desc_activ','final_desc_activ','final_addr_desc_activ','partner_id'], context=context)[0]
                    error_message = ''
                    if proxy.new_complete_name and (_correct_escape(proxy.new_complete_name) != proxy.complete_name) and not (proxy.final_partner_name or proxy.final_address_name):
                        error_message = u'Vous devez répartir le nouveau nom du partenaire entre le partenaire et l\'adresse'
                    if (not error_message) and ((proxy.new_zip_code or proxy.new_city) and not proxy.final_zip_id):
                        error_message = u'Vous devez réattribuer le code postal manuellement'
                    if (not error_message) and proxy.new_desc_activ and not (proxy.final_desc_activ or proxy.final_addr_desc_activ):
                        error_message = u'Vous devez réattribuer la description d\'activité manuellement'
                    old_vat_num = (proxy.vat_num or '').replace('/', '').replace('-', '').replace('.', '').replace(' ', '')
                    if proxy.new_vat_num and old_vat_num <> proxy.final_vat_num:
                        # check if not existing new vat num
                        same_vat_ids = self.env['res.partner'].search([('vat', '=', proxy.final_vat_num)])
                        if same_vat_ids:
                            if len(same_vat_ids) > 1 or proxy.partner_id.id <> same_vat_ids[0]:
                                error_message = u'Il s\'agit d\'un nouveau numéro de TVA qui existe déjà dans la base de données ...'
                    if not error_message:
                        proxy.but_confirm_changes()
                        error_message = u'Confirmé'
                    msg = error_message
                else:
                    msg = u'Cette fiche a déjà été confirmée.'
            else:
                msg = u'Vous ne pouvez confirmer manuellement que les fiches validées par les utilisateurs.'
        
        ctx = self.env.context.copy()
        ctx.update({'msg': msg})
        view = self.env.ref('cci_mailchimp.view_cci_memberdirectory_internal_validate_msg')
        
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cci.memberdirectory.manual.confirm.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class cci_memberdirectory_manual_confirm_msg(models.TransientModel):
    _name = 'cci.memberdirectory.manual.confirm.msg'
    
    msg = fields.Text(string='Details', readonly=True)
    
    @api.model
    def default_get(self, fields):
        rec = super(cci_memberdirectory_manual_confirm_msg, self).default_get(fields)
        if self.env.context.get('msg'):
            rec['msg'] = self.env.context['msg']
        return rec

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: