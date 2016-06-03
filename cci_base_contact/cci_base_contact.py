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

from openerp import models, fields, api, _

class res_partner_contact(models.Model):
    _inherit = 'res.partner'
    
    data_private = fields.Boolean('Private data', help="The data on this screen are private, don't diffuse them outside the CCI")
    self_sufficent = fields.Boolean('Keep contact', help='This contact will not be removed even if all his addresses are deleted')
    who_date_accept = fields.Date('Accept Date')
    who_date_last = fields.Date('Last Modification')
    who_date_publication = fields.Date(string='Publication')
    who_presence = fields.Boolean(string='In WsW', default=True)
    who_description = fields.Text('WsW Description', translate=True)
    origin = fields.Char('Origin', size=20, help='The DB from which the info is coming from')
    # fse_work_status = fields.Char('FSE Work Status',size=20)
    # fse_work_experience = fields.Char('FSE Work Exp.',size=20)
    # fse_studies = fields.Char('FSE Studies',size=20)
    fse_nationality = fields.Selection([('belgian', 'Belgian'), ('european', 'European Union'), ('world', 'Outside European Union'), ('none', 'No nationality'), ('unknown', 'Unknown')], "FSE Nationality")
    fse_work_experience = fields.Selection([('few', '< 5 years'), ('year59', '5 - 9 years'), ('year1014', '10 - 14 years'), ('year1519', '15 - 19 years'), ('more', '20 years and more')], 'FSE Work Exp.')
    fse_work_status = fields.Selection([('worker', 'Ouvrier'), ('employee', 'Employé'), ('manager', 'Cadre'), ('independent', 'Indépendant'), ('temporary', 'Intérimaire'), ('workingmarried', 'Conjoint aidant')], 'FSE Work Status')
    fse_studies = fields.Selection([('prof_exp', 'Professional Experience'), ('primary', 'Primary'), ('lowersecondary', 'Secondaire inférieur'), ('uppersecondary', 'Secondaire supérieur'), ('non-academic', 'Supérieur non universitaire'), ('academic', 'Universitaire')], 'FSE Studies')
    country_ids = fields.Many2many('res.country', 'res_country_rel', 'contact', 'country', "Expertize's Countries")
    link_ids = fields.One2many('res.partner.contact.link', 'current_contact_id', 'Contact Link')
    canal_id = fields.Many2one('crm.tracking.medium', 'Favourite Channel')
    national_number = fields.Char('National Number', size=15)
    magazine_subscription = fields.Selection([('never', 'Never'), ('prospect', 'Prospect'), ('personal', 'Personal'), ('postal', 'Postal')], "Magazine subscription")
    magazine_subscription_source = fields.Char('Mag. Subscription Source', size=30)
    old_id = fields.Integer('Old Datman ID')
    badge_title = fields.Char('Badge Title', size=128)
    badge_name = fields.Char('Badge Name', size=128)
    login_name = fields.Char('Login', size=240)
    password = fields.Char('Password', size=60)
    token = fields.Char('Website token', size=36)
    forced_login = fields.Boolean('Forced login for non-member')
    gender = fields.Selection([('man', 'Man'), ('women', 'Women')], string="Gender", default='man')
    #job_email = fields.related('job_id', 'email', type='char', size=240, string='Main Job Email')
    #job_phone = fields.related('job_id', 'phone', type='char', size=60, string='Main Job Phone')
    note = fields.Text('Note')
    write_date = fields.Datetime(string='Last Modification')
    write_uid = fields.Many2one('res.users', 'Last Modifier', help='The last person who has modified this contact')
    #TODO: Need to discuss
    #partner_id = fields.related('job_ids', 'address_id', 'partner_id', type='many2one', relation='res.partner', string='Main Employer')
    #main_title = fields.related('job_ids', 'function_label', type='string', string='Main Title')
    
    @api.multi
    def name_get(self):
        # will return name and first_name (courtesy)
        if not len(self.ids):
            return []
        res = []
        for r in self.read(['name', 'first_name', 'title']):
            addr = r.get('name', '')
            if r['name'] and r['first_name']:
                addr += ' '
            addr += (r.get('first_name', '') or '')
            if r.get('title',False):
                addr += ' (' + r.get('title')[1] + ')'
            res.append((r['id'], addr))
        return res

class res_partner_contact_link_type(models.Model):
    _name = "res.partner.contact.link.type"
    _description = "res.partner.contact.link.type"
    
    name = fields.Char('Name', size=20, required=True)

class res_partner_contact_link(models.Model):
    _name = 'res.partner.contact.link'
    _description = 'res.partner.contact.link'

    name = fields.Char('Name', size=40, required=True)
    type_id = fields.Many2one('res.partner.contact.link.type', 'Type', required=True)
    contact_id = fields.Many2one('res.partner', 'Contact', required=True)
    current_contact_id = fields.Many2one('res.partner', 'Current contact', required=True)

class project(models.Model):
    _inherit = 'project.project'
    _description = 'Project'
    
    contact_id2 = fields.Many2one('res.partner', string='Contact')

#NOTE: These field already exits in res.partner.contact
# class res_partner_job(models.Model):
#     _inherit = 'res.partner'
        
#     login_name = fields.Char('Login Name', size=80)
#     password = fields.Char('Password', size=50)
#     token = fields.Char('Token', size=40)
#     mobile_contact = fields.related('contact_id', 'mobile', type='char', string='Contact Mobile')
#     write_date = fields.Datetime('Last Modification')
#     write_uid = fields.Many2one('res.users', 'Last Modifier', help='The last person who has modified this job')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: