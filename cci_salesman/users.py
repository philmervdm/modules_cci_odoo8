# -*- coding: utf-8 -*-
# 27/11/2012 : Philmer - Change in the way to calculate yearly and monthly commissions
from openerp import api, fields, models, _
from datetime import date
from openerp.exceptions import except_orm, Warning
from openerp.api import constrains

class commission_slice(models.Model):
    _name = 'cci_salesman.commission_slice'

    user_id = fields.Many2one('res.users', string='User', required=True)
    year = fields.Integer(string='Year',required=True)
    amount_from = fields.Float(string='From Amount',digit=(15,2))
    rate100 =  fields.Float(string='Rate (pourcents)',digit=(4,2),required=True)

class res_users(models.Model):
    _inherit = 'res.users'
    
    salesman = fields.Boolean(string='Salesman', default=False)
    cci_crm_follower = fields.Boolean(string ='CRM Follower',help='Select only if this person will use his/her CCI CRM Todo list', default=False)
    slice_ids = fields.One2many('cci_salesman.commission_slice', 'user_id', string = 'Slices')

class cci_objectif(models.Model):
    _name = 'cci.objectif'

    objective = fields.Integer(string='Objectif')
    cci_product = fields.Many2one('cci.product', string='Product')
    user = fields.Many2one('res.users', string='User')
    year = fields.Char(string ='Year')
    cci_contact_id = fields.Many2one('cci.contact', string='Salesman')

class res_commission(models.Model):
    _name = 'res.commission'
    
    @api.multi
    def _get_com1(self):
        res = {}
        for line in self:
            if not line.objectif or line.realised >= line.objectif:
                line.com1 = 0
            else:
                line.com1 = line.realised*0.015
        return res
    
    @api.multi
    def _get_com2(self, name):
        res = {}
        for line in self:
            if not line.objectif or line.realised < line.objectif:
                line.com2 = 0
            else:
                line.com2 = line.realised*0.025
        return res
    
    product = fields.Many2one('cci.product', string='Product', domain=[('commissioned', '=', True)], readonly=True)
    realised = fields.Integer(string='Realised', readonly=True)
    objectif = fields.Integer(string='Objectif')
    com1 = fields.Integer(string='Com (1.5pourcent)')
    com2 = fields.Integer(string='Com (2.5pourcent)')
    objective_id = fields.Many2one('cci.objectif', string='Objective_id')
    
    @api.model
    def create(self,vals):
        context = dict(self._context or {})
        res = {}
        if 'read' in context and context.get('read') == True:
            res = super(res_commission, self).create(vals)
        else:
            raise Warning(_('Action non permise!'),
                _('Vous ne pouvez pas ajouter de lignes.'))
        
        return res
    
    @api.multi
    def write(self, vals):
        objective_id =  self.objective_id or False
        if objective_id:
            objective_id.write({'objective': vals.get('objectif')})
        return super(res_commission,self).write(vals)

class commission_exception(models.Model):
    
    _name = 'cci_salesman.commission_exception'
    
    @api.constrains('amount','commission')
    def check_only_one_value(self):
        for data in self:
            if data.amount and data.commission:
                raise Warning(_('Error!'),_('You can define a change on amount or on final commission, not both.'))
        return True
    
    @api.constrains('cci_product_id','amount','commission')
    def check_global_comm_change(self):
        for data in self:
            if not data.cci_product_id and data.amount:
                raise Warning(_('Error!'),_("You can let the 'CCI product' undefined but only for global commission change."))
        return True

    name = fields.Char(string='Name', required=True)
    period_id = fields.Many2one('account.period', string='Period', domain=[('special', '=', False)],required=True)
    user_id = fields.Many2one('res.users', string='User',required=True)
    cci_product_id = fields.Many2one('cci.product', string='CCI Product') ### not mandatory, because it can be global in case of a diminution of commission on a given period
    amount = fields.Float(string='Amount correction',digit=(15,2))
    commission = fields.Float(string='Commission correction',digit=(15,2))
    comments = fields.Text(string='Comments')
    

class commission_payment(models.Model):
    
    _name = 'cci_salesman.commission_payment'

    period_id = fields.Many2one('account.period', string='Period', domain=[('special', '=', False)],required=True)
    user_id = fields.Many2one('res.users', string='User',required=True)
    amount = fields.Float(string='Paid Amount',digit=(15,2))
    date_payment = fields.Date(string='Real Date of payment')
    comments = fields.Text('Comments')

