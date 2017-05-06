# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import inspect

class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    
    zip_id = fields.Many2one('res.partner.zip', string='Zip')

    @api.model
    def create(self, vals):
        if vals.has_key('zip_id'):
            if vals['zip_id']:
                vals['zip'] = self.env['res.partner.zip'].browse(vals['zip_id']).name
                vals['city'] = self.env['res.partner.zip'].browse(vals['zip_id']).city
                vals['country_id'] = self.env['res.partner.zip'].browse(vals['zip_id']).country_id.id
                vals['state_id'] = self.env['res.partner.zip'].browse(vals['zip_id']).state_id.id
            else:
                vals['zip'] = False
                vals['city'] = False
                vals['country_id'] = False
                vals['state_id'] = False
        new_record = super(res_partner, self).create(vals)
        return new_record
    
#    @api.multi
#    def write(self, vals):
#        import pdb; pdb.set_trace()
#        if vals.has_key('zip_id'):
#            if vals['zip_id']:
#                vals['zip'] = self.env['res.partner.zip'].browse(vals['zip_id']).name
#                vals['city'] = self.env['res.partner.zip'].browse(vals['zip_id']).city
#                vals['country_id'] = self.env['res.partner.zip'].browse(vals['zip_id']).country_id.id
#                vals['state_id'] = self.env['res.partner.zip'].browse(vals['zip_id']).state_id.id
#            else:
#                vals['zip'] = False
#                vals['city'] = False
#                vals['country_id'] = False
#                vals['state_id'] = False
#        super(res_partner, self).write(vals)
#        return True

