# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (c) 2009 CCI  ASBL. (<http://www.ccilconnect.be>).
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# Redefinition of magazine_subscription_source as fields.selection() better than fields.char()
from openerp import models, fields , api , _ 
import time
import datetime


def _get_subscription_sources(self):
    obj = self.env['cci_magazine.subscription_source']
    ids = obj.search([])
    res = ids.read(['code','name'])
    return [(r['code'], r['name']) for r in res] +  [('','')]

class subscription_source(models.Model):
    _name = "cci_magazine.subscription_source"
    _description = "Source of Subscription for the CCI Mag"
    
    name = fields.Char('Name', required=True, size=64)
    code = fields.Char('Code', required=True, size=30)

    _order = 'code'

    @api.multi
    def write(self,vals):
        old = self.code
        new = vals.get('code','') or old
        res = super(subscription_source,self).write(vals)
        if old != new:
            self.env.cr.execute("UPDATE res_partner set magazine_subscription_source = '%s' where magazine_subscription_source = '%s'" % (new,old) )
        return res
    
    @api.one
    def copy(self, default={}):
        this = self.read(['name','code'])[0]
        old_name = this['name']
        old_code = this['code']
        default.update({'name': old_name+ _(' (copy)'), 'code': old_code + _(' (copy)') })
        return super(subscription_source, self).copy(default)
    
    
    @api.multi
    def unlink(self):
        for source in self:
            self.env.cr.execute("UPDATE res_partner set magazine_subscription_source = '' where magazine_subscription_source = '%s'" % source.code )
        return super(subscription_source,self).unlink()

class res_partner_address(models.Model):
    _inherit = "res.partner"

    magazine_lastprospection = fields.Date("Magazine last Sending as Prospection")
    magazine_subscription_source = fields.Selection(_get_subscription_sources,'Source',size=30)

class res_partner_job(models.Model):
    
    _inherit = "res.partner"
    
    @api.model
    def _inactivate_old(self):
        # this method makes jobs with pas 'date-stop' inactive
        # it's launched every day by a cron task but can also be launched manually (not important but for testing)
        # all checks are recorded to keep track of theses automatic changes
        today =  fields.Date.today()
#         obj_job = self.pool.get('res.partner.job')
        job_ids = self.search([('date_stop','<',today)])
        if job_ids:
            jobs = job_ids.write({'active':False})
        
        past_job_check = self.env['cci_magazine.past_job_check']
#         today = datetime.datetime.today()
        
        id = past_job_check.create({
            'name': fields.Datetime.now(),
            'count' : len(job_ids),
            'status': '[' + ','.join( [str(x) for x in job_ids.ids] ) + ']',
            })
        return job_ids

    magazine_subscription_source = fields.Selection(_get_subscription_sources,'Source',size=30)
    magazine_lastprospection = fields.Date("Magazine last Sending as Prospection")

class cci_mag_subscription(models.Model):
    _name = "cci_mag_subscription"
    _description = "Subscription to the CCI Mag"
    
    source = fields.Char('Source',size=30)
    type = fields.Char("Type",size=30)
    model = fields.Char("Model",size=30)
    partner_name = fields.Char("Partner name",size=120)
    membership_state = fields.Char("Membership state",size=30)
    street = fields.Char("Street",size=120)
    street2 = fields.Char("Street2",size=120)
    city = fields.Char("City",size=120)
    contact_name = fields.Char("Contact name",size=60)
    first_name = fields.Char("First name",size=60)
    partner_id = fields.Many2one('res.partner',"Partner data")
    address_id = fields.Many2one('res.partner',"Address data")
    job_id = fields.Many2one('res.partner',"Function data")
    contact_id = fields.Many2one('res.partner',"Contact data")

class past_job_check(models.Model):
    _name = 'cci_magazine.past_job_check'
    _description = '''Recording of a check of past done job'''

    name = fields.Char('Date',size=19,required=True)
    count = fields.Integer('Changes count')
    status = fields.Text('Status')
    
    _order = 'name desc'
