# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class res_partner_zip_group_type(models.Model):
    _name = 'res.partner.zip.group.type'
    _description = 'A type of group of zip codes.\nA zip code can exists only in a group of the same type.'
    _order = 'name'
    
    name = fields.Char('Name', size=50, required=True)

