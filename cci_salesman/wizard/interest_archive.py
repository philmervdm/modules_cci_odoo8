# -*- coding: utf-8 -*-

from openerp import api, fields, models, _
import time

class interest_archive(models.TransientModel):
    _name = 'interest.archive'
    year =  fields.Integer(string='Year', required = True, default= int(time.strftime('%Y')) - 1)   
    product_ids = fields.Many2many('cci.product', 'interest_archive_rel', 'archieve_id', 'cci_product_id', string='Products', required = True)
    
    @api.multi
    def do_next(self,data):
        return {}
    
