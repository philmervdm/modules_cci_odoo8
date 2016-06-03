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

from openerp import tools
from openerp import models, fields, api, _

class part_email(models.TransientModel):
    _name = 'part.email'
    
    email_from = fields.Char(string="Sender's email", size=64, required=True)
    subject = fields.Char(string='Subject', size=64, required=True)
    text = fields.Html(string='Message', required=True)
    event = fields.Boolean(string='Open Partners for Event History')
    
    # this sends an email to ALL the addresses of the selected partners.
    @api.multi
    def mass_mail_send(self):
        nbr = 0
        
        partner_ids = self.env.context.get('active_ids', [])
        if partner_ids:
            partners = self.env['res.partner'].browse(partner_ids)
            for partner in partners:
                for adr in partner.child_ids:
                    if adr.email:
                        name = adr.name or partner.name
                        to = '%s <%s>' % (name, adr.email)
        # TODO: add some tests to check for invalid email addresses
        # CHECKME: maybe we should use res.partner/email_send
                        res = tools.email_send(self.email_from, [to], self.subject, self.text, subtype='html')
                        nbr += 1
#                 pooler.get_pool(cr.dbname).get('res.partner.event').create(cr, uid, # TODO: Need to complete
#                         {'name': 'Email sent through mass mailing',
#                          'partner_id': partner.id,
#                          'description': data['form']['text'], })
        ctx = self.env.context.copy()
        ctx.update({'nbr': nbr})
        
        if self.event:
            return self.open_partners()
        return self.nbr_mail()
        
    @api.multi
    def nbr_mail(self):
        view = self.env.ref('cci_partner.part_email_nbr_form')
        return {
            'name': _('Mass Mailing'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'part.email.nbr',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }
    
    @api.multi
    def open_partners(self):
         view = self.env.ref('base.view_partner_form')
         partner_ids = self.env.context['active_ids']
         return {
            'domain': "[('id','in', [" + ','.join(map(str, partner_ids)) + "])]",
            'name': 'Partners',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'views': [(False, 'tree'), (view.id, 'form')],
            'type': 'ir.actions.act_window'
        }

class part_email_nbr(models.TransientModel):
    _name = 'part.email.nbr'
     
    nbr = fields.Char(string='Number of Mail Sent', size=64, readonly=True)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: