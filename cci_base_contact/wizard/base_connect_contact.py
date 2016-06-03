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
from openerp.exceptions import Warning

class base_connect_contact(models.TransientModel):
    _name = 'base.connect.contact'
    
    @api.model
    def _get_url(self):
        if self.env.context.get('active_id'):
            contact_id = self.env.context.get('active_id')
            contact = self.env['res.partner'].browse(contact_id)
            if not contact.token:
                raise Warning(_('Error :'), _('This contact has no token !'))
            else:
                url = "http://www.cciconnect.be/loginReg.asp?idK=[[[token]]]"
                if '[[[token]]]' in url:
                    url = url.replace('[[[token]]]', contact.token)
        return url
    
    site_address = fields.Char(string='Profile Address', size=240, default=_get_url)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: