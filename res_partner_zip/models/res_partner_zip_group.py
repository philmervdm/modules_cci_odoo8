# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class res_partner_zip_group(models.Model):
    _name = 'res.partner.zip.group'
    _description = 'Group of zip codes.\nA zip code can exists only in once in a group of a givent type'
    _order = 'name'
    
    type_id = fields.Many2one('res.partner.zip.group.type', string='Type')
    name = fields.Char('Name', size=50, required=True)

