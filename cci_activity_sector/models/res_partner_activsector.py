# -*- encoding: utf-8 -*-
from openerp import models, fields, api , _
from openerp.exceptions import Warning

class res_partner_activsector(models.Model):
    _name = 'res.partner.activsector'
    _description = 'Activity sector description for CCI'
    
    @api.constrains('parent_id')
    def _check_recursion(self):
        level = 100
        ids = self.ids
        while len(ids):
            self.env.cr.execute('select distinct parent_id from res_partner_activsector where id in %s', (tuple(ids),))
            ids = filter(None, map(lambda x:x[0], self.env.cr.fetchall()))
            if not level:
                raise Warning(_('Error ! You can not create recursive sectors.'))
            level -= 1
        return True

    code = fields.Char('Sector Code', required=True, size=6)
    name = fields.Char('Sector Name', required=True, size=64, translate=True)
    parent_id = fields.Many2one('res.partner.activsector', 'Parent Sector', select=True)
    child_ids = fields.One2many('res.partner.activsector', 'parent_id', 'Child Sectors')
    active = fields.Boolean('Active', default=True, help="The active field allows you to hide the sector without removing it.")
    directly = fields.Boolean('Directly usable', help='The concerned sector can be directly used by a partner, it isn\'t a header sector')
    
    _order = 'code'
    
