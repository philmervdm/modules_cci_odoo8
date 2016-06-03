# -*- coding: utf-8 -*-
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
from openerp import models, fields , api , _

import datetime

class wizard_check_membership(models.TransientModel):
    _name = 'wizard.check.membership'
    
    final_text = fields.Text(string = 'Changes', readonly = True)
    final_count = fields.Integer(string = 'Count', readonly = True)

    @api.v7
    def _check_membership(self, cr, uid, data, context):
        # this method is partially copied in the method cci_membership=>cci_membership.py=>_membership_state_job()
        res = super(wizard_check_membership,self).default_get(self)
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, ['|',('active','=','True'),('active','=','False')], context=context)
        if partner_ids:
            partners = partner_obj.read(cr, uid, partner_ids, ['id','membership_state'] )
            new_mstates = partner_obj._membership_state(cr, uid, partner_ids, '', args=None, context=None)
            changed_lines = []
            for partner in partners:
                if new_mstates.has_key( partner['id'] ):
                    if partner['membership_state'] <> new_mstates[partner['id']]:
                        partner_name = partner_obj.read(cr, uid, [partner['id']], ['name'] )[0]['name']
                        changed_lines.append( u"Partenaire '%s' (id=%s) passe de '%s' à '%s'" % (partner_name, str(partner['id']),partner['membership_state'],new_mstates[partner['id']]) )
                        partner_obj.write(cr, uid, [partner['id']], {}, context )
            if changed_lines:
                final_text = 'Changements : \n' + ( u'\n'.join( changed_lines ) )
            else:
                final_text = "Changements : aucun"
            membership_check = self.pool.get('cci_membership.membership_check')
            today = datetime.datetime.today()
            id = membership_check.create(cr, uid, {
                'name': today.strftime('%Y-%m-%d-%H:%M:%S'),
                'count' : len(changed_lines),
                'status': final_text,
                })
            res['final_text'] = str(final_text.encode('ascii','ignore'))
            res['final_count'] = len(changed_lines)
        return res
    
#     @api.model
#     def default_get(self,fields):
#         res = super(wizard_check_membership,self).default_get(self)
#         
#         partner_obj = self.env['res.partner']
#         partners = partner_obj.search(['|',('active','=','True'),('active','=','False')])
#         if partners:
#             new_mstates = partner_obj._membership_state(partners.ids, '')
#             changed_lines = []
#             for partner in partners:
#                 if new_mstates.has_key( partner.id ):
#                     if partner.membership_state <> new_mstates[partner.id]:
#                         partner_name = partner.name
#                         changed_lines.append( u"Partenaire '%s' (id=%s) passe de '%s' à '%s'" % (partner_name, str(partner.id),partner.membership_state,new_mstates[partner.id]) )
# #                         partner_obj.write(cr, uid, [partner['id']], {}, context )
#             if changed_lines:
#                 final_text = 'Changements : \n' + ( u'\n'.join( changed_lines ) )
#             else:
#                 final_text = "Changements : aucun"
#             membership_check = self.env['cci_membership.membership_check']
#             today = datetime.datetime.today()
#             id = membership_check.create({
#                 'name': today.strftime('%Y-%m-%d-%H:%M:%S'),
#                 'count' : len(changed_lines),
#                 'status': final_text,
#                 })
#             res['final_text'] = str(final_text.encode('ascii','ignore'))
#             res['final_count'] = len(changed_lines)
#         return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
