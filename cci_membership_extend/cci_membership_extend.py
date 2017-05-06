# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
from openerp import models, fields, api , _
import datetime
import time

#class membership_range(models.Model):
#    _name = 'cci_membership.membership_range'
#    _description = '''Range of employees with standard membership price'''
#    
#    year = fields.Integer('Year',required=True)
#    from_range = fields.Integer('From',help='Lower number of local employees for this range',required=True)
#    to_range = fields.Integer('To',help='Upper number of employees for this range',required=True)
#    amount = fields.Float('Standard amount',digits=(15,2),help='Amount to invoice by default for this range of employees')
#
#class membership_askedused(models.Model):
#    _name = 'cci_membership.membership_askedused'
#    _description = '''Used asked amount of membership'''
#
#    amount = fields.Float('Amount',digits=(15,2),readonly=True)
#    count = fields.Integer('Count',readonly=True)
#    total_value = fields.Float('Total Value',digits=(15,2),readonly=True)
#    type = fields.Char('Type of selection',size=7)
#
#class membership_call(models.Model):
#    _name = 'cci_membership.membership_call'
#    _description = '''Data for calling membership'''
#    
#    partner_id = fields.Many2one('res.partner', string='Partner')
#    address_id = fields.Many2one('res.partner', string='Address')
#    job_id =  fields.Many2one('res.partner', string='Job')
#    contact_id = fields.Many2one('res.partner', string='Contact')
#    partner_name = fields.Char('Sending Name',size=200)
#    street = fields.Char('Street',size=250)
#    street2 = fields.Char('Street2',size=250)
#    zip_code = fields.Char('Zip Code',size=30)
#    city = fields.Char('City',size=80)
#    email_addr = fields.Char('Email Address',size=200)
#    phone_addr = fields.Char('Phone Address',size=50)
#    fax_addr = fields.Char('Fax Address',size=50)
#    name = fields.Char('Contact Name',size=120)
#    first_name = fields.Char('Contact First Name',size=120)
#    courtesy = fields.Char('Courtesy',size=20)
#    title = fields.Char('Title',size=1000)
#    title_categs = fields.Char('Categs',size=20)
#    email_contact = fields.Char('Professionnal Email',size=200)
#    base_amount = fields.Float('Base Amount',digits=(15,2))
#    count_add_sites = fields.Integer('Additional Sites')
#    unit_price_site = fields.Float('Unit Price per Site',digits=(15,2))
#    desc_add_site = fields.Char('Explanation Additional Sites',size=200)
#    wovat_amount = fields.Float('Invoiced Price without VAT',digits=(15,2))
#    wvat_amount = fields.Float('Invoiced Price with VAT',digits=(15,2))
#    salesman = fields.Char('Salesman',size=45)
#    salesman_phone = fields.Char('Salesman Phone',size=45)
#    salesman_fax = fields.Char('Salesman Fax',size=45)
#    salesman_mobile = fields.Char('Salesman Mobile',size=45)
#    salesman_email = fields.Char('Salesman Email',size=45)
#    vcs = fields.Char('VCS',size=30)
#
#class membership_by_partner(models.Model):
#    _name = 'cci_membership.membership_by_partner'
#    _description = '''Subtotal Membership by Partner'''
#
#    partner_id = fields.Many2one('res.partner','Partner')
#    user_id = fields.Many2one('res.users','Salesman')
#    year =  fields.Integer('Membership Year')
#    invoiced = fields.Float('Invoiced',digits=(15,2))
#    paid = fields.Float('Paid',digits=(15,2))
#    canceled = fields.Float('Canceled',digits=(15,2))
#    open = fields.Float('Open',digits=(15,2))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
