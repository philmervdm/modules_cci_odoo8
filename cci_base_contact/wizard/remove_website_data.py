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

from openerp import models, fields, api, _

class remove_website_data(models.TransientModel):
    _name = 'remove.website.data'
    
    reason = fields.Selection([
                    ('autrezone', "Prioritaire dans une autre CCI"),
                    ('jamais', u"Ne désire plus être abonné"),
                    ('double_email', u"Cette adresse email existe sur une autre fiche, en double"),
                    ('erase', u"Simple effacement (si membre, sera réabonné)")], string='Reason', default='jamais')
    
    @api.multi
    def remove_data(self):
        active_ids = self.env.context.get('active_ids')
        if active_ids:
            partners = self.env['res.partner'].browse(active_ids)
            for form in self:
                newlogin = form.reason
                if form.reason == 'erase':
                    newlogin = ''
                    partners.write({'login_name': newlogin, 'token': '', 'password': ''})
        return {'type': 'ir.actions.act_window_close'}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: