# -*- encoding: utf-8 -*-
from openerp import models, fields, api , _
from openerp.exceptions import Warning

class res_partner_address(models.Model):
    _inherit = "res.partner"
    _description = "res.partner"

    sector1 = fields.Many2one('res.partner.activsector','Sector 1')
    sector2 = fields.Many2one('res.partner.activsector','Sector 2')
    sector3 = fields.Many2one('res.partner.activsector','Sector 3')
