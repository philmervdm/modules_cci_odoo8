# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 CCILV ASBL. (http://www.ccilv.be) All Rights Reserved.
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

from openerp import models, fields

class cci_country(models.Model):
    _name = "cci.country"
    _description = "Country or Area for CCI"

    code = fields.Char('Code', size=3, required=True)
    name = fields.Char('Name', size=64, required=True)
    official_name = fields.Char('Official Name', size=120)
    postalabbrev = fields.Char('Postal Abbreviation', size=4)
    phoneprefix = fields.Integer('Phone Prefix')
    description = fields.Text('Description')
    iscountry = fields.Boolean('Country', help='Indicates if this code designates a country; if False, designates an area', default=True)
    active = fields.Boolean('Active', help='Indicates if we can still use this country-area code', default=True)
    valid4certificate = fields.Boolean('Certificates', help='Indicates if this code can be used for certificates', default=True)
    valid4ata = fields.Boolean('ATA', help='Indicates if this code can be used for carnets ATA')
    valid4embassy = fields.Boolean('Embassy', help='Indicates if this code can be used for Embassies', default=True)
    cci_country_ids = fields.Many2many('cci.country', 'cci_country_rel', 'country_id', 'current_country_id', 'Linked Countries-Areas')

