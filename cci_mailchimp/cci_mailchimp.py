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
import datetime
import mailchimp
import xmlrpclib
from openerp import tools
from openerp import models, fields, api, _

class res_partner_contact(models.Model):
    _inherit = 'res.partner'
    _description = 'res.partner'

    rdp_subscribe = fields.Selection([('default', 'Default'), ('always', 'Always'), ('never', 'Never'), ('unsubscribed', 'Unsubscribed by MailChimp')], 'Sending of Revue de Presse', default='default')
    agenda_subscribe = fields.Selection([('default', 'Default'), ('always', 'Always'), ('never', 'Never'), ('unsubscribed', 'Unsubscribed by MailChimp')], 'Sending of Agenda', default='default')
    alterego_subscribe = fields.Selection([('default', 'Default'), ('always', 'Always'), ('never', 'Never'), ('unsubscribed', 'Unsubscribed by MailChimp')], 'Sending of Alter Ego newsletter', default='default')
    rdp_forced_area = fields.Selection([('default', 'Default'), ('brabant_wallon', 'Brabant Wallon'), ('vlanderen', 'Flandres'), ('hainaut', 'Hainaut'), ('liege', 'Liege'), ('namur', 'Namur'), ('wapi', 'WAPI')], 'Forced Area for Revue de Presse', default='default')
    leid = fields.Char('MailChimp leid', size=8)
    euid = fields.Char('MailChimp euid', size=10)

class cci_newsletter_source(models.Model):
    _inherit = 'cci_newsletter.source'

    followup_email = fields.Char('Email for Follow-Up', size=250)

class mail_usage(models.Model):
    _name = 'mail_usage'
    _description = 'An usage of an email address'

    name = fields.Char('Name-Email', required=True, size=200)
    source = fields.Char('Source', size=120)
    source_id = fields.Integer('Source ID')

class mail_bounce(models.Model):
    _name = 'mail_bounce'
    _description = "An email address that has bounced in MailChimp"

    name = fields.Char('Name-Email', required=True, size=200)
    date = fields.Date('Date')
    type = fields.Char('Type of Bounce', size=40)
    active = fields.Boolean('Active', default=True)
    
    @api.model
    def _recup_cleaned(self, list_names=('rdp',)):
        # start log
        cronline_id = self.env['cci_logs.cron_line']._start('RecupHardBounceMailChimp')
        final_result = False
        final_count = 0
        #
        # We get the API key
        parameter_obj = self.env['cci_parameters.cci_value']
        param_values = parameter_obj.get_value_from_names(['MailChimpAPIKey'])
        if param_values.has_key('MailChimpAPIKey'):
            # we extract all email address already 'cleaned'
            already_bounced = []
            bounce_obj = self.env['mail_bounce']
            bounce_ids = bounce_obj.search([('type', '=', 'hard-bounce')])
            if bounce_ids:
                bounces = bounce_ids.read(['name'])
                already_bounced = [x['name'] for x in bounces]
            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\nAlready Bounced : %s' % str(len(already_bounced)))
            final_result = True
            for list_name in list_names:
                param_list_values = parameter_obj.get_value_from_names(['MailChimp%sListID' % list_name.upper()])
                if param_list_values.has_key('MailChimp%sListID' % list_name.upper()):
                    mailchimp_list_id = param_list_values['MailChimp%sListID' % list_name.upper()]
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\nGetting cleaned of List %s' % list_name)
                    # We create necessary MailChimp objects
                    mailchimp_server = mailchimp.Mailchimp(param_values['MailChimpAPIKey'], False)
                    mailchimp_lists = mailchimp.Lists(mailchimp_server)
                    result = mailchimp_lists.members(mailchimp_list_id, 'cleaned')
                    to_delete = []
                    total = result['total']
                    page = 0
                    while total > 0:
                        result = mailchimp_lists.members(mailchimp_list_id, 'cleaned', {'start':page})
                        page += 1
                        total = total - len(result['data'])
                        for member in result['data']:
                            if member['email'] not in already_bounced:
                                to_delete.append(member['email'])
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\nEmails found to delete : %s' % str(len(to_delete)))
                    if to_delete:
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n -' + '\n - '.join(to_delete))
                        obj_proxy = self.env['mailchimp_proxy']
                        final_count = obj_proxy.delete_email(to_delete, True)
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nEmails deleted from tables : %s' % str(final_count))
                        obj_bounce = self.env['mail_bounce']
                        today = datetime.date.today().strftime('%Y-%m-%d')
                        for email in to_delete:
                            obj_bounce.create({'name':email, 'date':today, 'type':'hard-bounce'})
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nEmails recorded as hard-bounces : %s' % str(len(to_delete)))
                else:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n Parameter not found \'MailChimp%sListID\'. Others possible lists managed.' % list_name.upper())
                    final_result = False
        else:           
            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n No Parameters found \'MailChimpAPIKey\'. End of procedure.')
        #
        final_result = True
        self.env['cci_logs.cron_line']._stop(cronline_id, final_result, '\n---end---')
        return True
    
    @api.model
    def _recup_unsubscribed(self, list_names=('rdp',)):
        # start log
        cronline_id = self.env['cci_logs.cron_line']._start('RecupUnsubscribedMailChimp')
        final_result = False
        final_count = 0
        #
        # We get the API key
        parameter_obj = self.env['cci_parameters.cci_value']
        param_values = parameter_obj.get_value_from_names(['MailChimpAPIKey'])
        if param_values.has_key('MailChimpAPIKey'):
            final_result = True
            for list_name in list_names:
                param_list_values = parameter_obj.get_value_from_names(['MailChimp%sListID' % list_name.upper()])
                if param_list_values.has_key('MailChimp%sListID' % list_name.upper()):
                    mailchimp_list_id = param_list_values['MailChimp%sListID' % list_name.upper()]
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\nGetting unsubscribed of List %s' % list_name)

                    # we extract all email address already 'cleaned'
                    already_bounced = []
                    bounce_obj = self.env['mail_bounce']
                    bounce_ids = bounce_obj.search([('type', '=', 'unsubscribed_' + list_name)])
                    if bounce_ids:
                        bounces = bounce_ids.read(['name'])
                        already_bounced = [x['name'] for x in bounces]
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAlready Unsubscribed : %s' % str(len(already_bounced)))

                    # We create necessary MailChimp objects
                    mailchimp_server = mailchimp.Mailchimp(param_values['MailChimpAPIKey'], False)
                    mailchimp_lists = mailchimp.Lists(mailchimp_server)
                    result = mailchimp_lists.members(mailchimp_list_id, 'unsubscribed')
                    to_unsubscribe = []
                    total = result['total']
                    page = 0
                    while total > 0:
                        result = mailchimp_lists.members(mailchimp_list_id, 'unsubscribed', {'start':page})
                        page += 1
                        total = total - len(result['data'])
                        for member in result['data']:
                            if member['email'] not in already_bounced:
                                to_unsubscribe.append(member['email'])
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\nEmails found to unsubscribe : %s' % str(len(to_unsubscribe)))
                    if to_unsubscribe:
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n -' + '\n - '.join(to_unsubscribe))
                        obj_proxy = self.env['mailchimp_proxy']
                        final_count = obj_proxy.unsubscribe_email(to_unsubscribe, list_name, True)
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nEmails unsubscribed in tables : %s' % str(final_count))
                        obj_bounce = self.env['mail_bounce']
                        today = datetime.date.today().strftime('%Y-%m-%d')
                        for email in to_unsubscribe:
                            obj_bounce.create({'name':email, 'date':today, 'type':'unsubscribed_' + list_name})
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nEmails recorded as unsubscribed : %s' % str(len(to_unsubscribe)))
                else:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n Parameter not found \'MailChimp%sListID\'. Others possible lists managed.' % list_name.upper())
                    final_result = False
        else:           
            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n No Parameters found \'MailChimpAPIKey\'. End of procedure.')
        #
        final_result = True
        self.env['cci_logs.cron_line']._stop(cronline_id, final_result, '\n---end---')
        return True

class mailchimp_proxy(models.Model):
    _name = "mailchimp_proxy"
    _description = "An email address synchronised with MailChimp"

    name = fields.Char('Name-Email', required=True, size=200)
    list_name = fields.Selection([('rdp', 'Revue de Presse'), ('agenda', 'Agenda CCI'), ('alterego', 'Alter Ego'), ('rdpvl', 'RDP Vlanderen')], 'List')
    first_name = fields.Char('First Name', size=120)
    last_name = fields.Char('Last Name', size=120)
    company = fields.Char('Company', size=250)
    area_rdp = fields.Selection(selection=[('none', 'None'), ('brabant_wallon', 'Brabant Wallon'), ('vlanderen', 'Flandres'), ('hainaut', 'Hainaut'), ('liege', 'Liege'), ('namur', 'Namur'), ('wapi', 'WAPI'), ('test', 'For Test')], string='Area for RdP', default='none')
    title = fields.Char('Job Title', size=250)
    categs = fields.Char('Job Categories', size=10)
    courtesy_code = fields.Char('Courtesy Code', size=15)
    courtesy_full1 = fields.Char('Courtesy Full 1', size=120)
    courtesy_full2 = fields.Char('Courtesy Full 2', size=120)
    member = fields.Boolean('Member of source CCI')
    job_id = fields.Many2one('res.partner.job', 'Linked Job')
    contact_id = fields.Many2one('res.partner', 'Linked Contact')
    subscriber_id = fields.Many2one('cci_newsletter.subscriber', 'Linked Subscriber')
    source = fields.Char('Source of Data', size=30)
    active = fields.Boolean('Active', default=True)
    dirty = fields.Boolean('Dirty', default=True)
    todelete = fields.Boolean('To delete')
    
    @api.model
    def _normalize_email(self, email_address):
        normalized_email = email_address and email_address.strip() or ''
        return normalized_email.lower()
    
    @api.model
    def _subscribe_contact(self, contact, list_name, dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_area, source, specific_email):
        if contact.email or specific_email:
            selected_email = self._normalize_email(specific_email or contact.email)
            if dProxyName2ID.has_key(self._normalize_email(selected_email)):
                # there is an proxy with this email address and this proxy was not yet 'controlled'
                proxy_id = dProxyName2ID[self._normalize_email(selected_email)]
                if dProxies[proxy_id]['todelete']:
                    dProxies[proxy_id]['todelete'] = False
                    # check if data have changed in partners data
                    dirty = False
                    if (dProxies[proxy_id]['first_name'] or '') != (contact.first_name or '').strip():
                        dProxies[proxy_id]['first_name'] = (contact.first_name or '').strip()
                        dirty = True
                    if (dProxies[proxy_id]['last_name'] or '') != (contact.name or '').strip():
                        dProxies[proxy_id]['last_name'] = (contact.name or '').strip()
                        dirty = True
                    if dProxies[proxy_id]['company']:
                        dProxies[proxy_id]['company'] = ''
                        dirty = True
                    if contact.rdp_subscribe == 'never':
                        selected_area = 'none'
                    else:
                        if contact.rdp_forced_area == 'default':
                            if default_area == 'liege-namur':
                                # we choose between liege and namur following the zip code of linked address
                                # here, we don't have any linked address => default = 'liege'
                                selected_area = 'liege'
                            else:
                                selected_area = default_area
                        else:
                            selected_area = contact.rdp_forced_area
                    if (dProxies[proxy_id]['area_rdp'] or '') != selected_area:
                        dProxies[proxy_id]['area_rdp'] = selected_area
                        dirty = True
                    if dProxies[proxy_id]['title'] or dProxies[proxy_id]['categs'] or dProxies[proxy_id]['job_id'] or (dProxies[proxy_id]['contact_id'] != contact.id) or dProxies[proxy_id]['job_id'] or dProxies[proxy_id]['subscriber_id'] or dProxies[proxy_id]['source'] != source:
                        dProxies[proxy_id]['title'] = ''
                        dProxies[proxy_id]['categs'] = ''
                        dProxies[proxy_id]['member'] = 'non'
                        dProxies[proxy_id]['job_id'] = False
                        dProxies[proxy_id]['contact_id'] = (contact.id, '')
                        dProxies[proxy_id]['subscriber_id'] = False
                        dProxies[proxy_id]['source'] = source
                        dirty = True
                    if dProxies[proxy_id]['courtesy_code'] != (contact.title and dCourtesies[contact.title]['shortcut'] or ''):
                        dProxies[proxy_id]['courtesy_code'] = contact.title and dCourtesies[contact.title]['shortcut'] or ''
                        dProxies[proxy_id]['courtesy_full1'] = contact.title and dCourtesies[contact.title]['other1'] or ''
                        dProxies[proxy_id]['courtesy_full2'] = contact.title and dCourtesies[contact.title]['other2'] or ''
                        dirty = True
                    if dirty:
                        dProxies[proxy_id]['dirty'] = True
                        return ('dirty', proxy_id)
                    else:
                        return ('undelete', proxy_id)
                else:
                    return ('same_email', proxy_id)
            else:
                if self._normalize_email(selected_email) not in added_emails:
                    new_data = {}
                    new_data['name'] = self._normalize_email(selected_email)
                    new_data['list_name'] = list_name
                    new_data['first_name'] = (contact.first_name or '').strip()
                    new_data['last_name'] = (contact.name or '').strip()
                    new_data['list_namecompany'] = ''
                    if contact.rdp_subscribe == 'never':
                        selected_area = 'none'
                    else:
                        if contact.rdp_forced_area == 'default':
                            if default_area == 'liege-namur':
                                # we choose between liege and namur following the zip code of linked address
                                # here, we don't have any linked address => default = 'liege'
                                selected_area = 'liege'
                            else:
                                selected_area = default_area
                        else:
                            selected_area = contact.rdp_forced_area
                    new_data['area_rdp'] = selected_area
                    new_data['title'] = ''
                    new_data['categs'] = ''
                    new_data['member'] = 'non'
                    new_data['job_id'] = False
                    new_data['contact_id'] = contact.id
                    new_data['subscriber_id'] = False
                    new_data['source'] = source
                    new_data['courtesy_code'] = contact.title and dCourtesies[contact.title]['shortcut'] or ''
                    new_data['courtesy_full1'] = contact.title and dCourtesies[contact.title]['other1'] or ''
                    new_data['courtesy_full2'] = contact.title and dCourtesies[contact.title]['other2'] or ''
                    new_data['dirty'] = True
                    new_proxy_id = self.env['mailchimp_proxy'].create(new_data)
                    added_emails.append(self._normalize_email(selected_email))
                    return ('add', new_proxy_id)
                else:
                    return ('same_email', 0)
        else:
            return ('None', 0)
        
    @api.model
    def _subscribe_job(self, job, list_name, dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_area, source, specific_email):
        if job.email or job.contact_id.email or specific_email:
            selected_email = self._normalize_email(specific_email or job.email or job.contact_id.email)
            if dProxyName2ID.has_key(selected_email):
                # there is an proxy with this email address and this proxy was not yet 'controlled'
                proxy_id = dProxyName2ID[selected_email]
                if dProxies[proxy_id]['todelete']:
                    dProxies[proxy_id]['todelete'] = False
                    # check if data have changed in partners data
                    dirty = False
                    if (dProxies[proxy_id]['first_name'] or '') != (job.contact_id.first_name or '').strip():
                        dProxies[proxy_id]['first_name'] = (job.contact_id.first_name or '').strip()
                        dirty = True
                    if (dProxies[proxy_id]['last_name'] or '') != (job.contact_id.name or '').strip():
                        dProxies[proxy_id]['last_name'] = (job.contact_id.name or '').strip()
                        dirty = True
                    company = job.address_id.partner_id.name.strip()
                    if job.address_id.name:
                        if job.address_id.name[0:2] == '- ' or job.address_id.name[0:3] == ' - ':
                            company = company + ' ' + job.address_id.name.strip()
                        else:
                            company = job.address_id.name.strip()
                    if dProxies[proxy_id]['company'] != company:
                        dProxies[proxy_id]['company'] = company
                        dirty = True
                    if job.contact_id.rdp_subscribe == 'never':
                        selected_area = 'none'
                    else:
                        if job.contact_id.rdp_forced_area == 'default':
                            if default_area == 'liege-namur':
                                selected_area = 'liege'
                                if job.address_id.zip_id and job.address_id.zip_id.name[0:1] == '5':
                                    selected_area = 'namur'
                            else:
                                selected_area = default_area
                        else:
                            selected_area = job.contact_id.rdp_forced_area
                    if (dProxies[proxy_id]['area_rdp'] or '') != selected_area:
                        dProxies[proxy_id]['area_rdp'] = selected_area
                        dirty = True
                    if (dProxies[proxy_id]['title'] or '') != (job.function_label or '').strip():
                        dProxies[proxy_id]['title'] = (job.function_label or '').strip()
                        dirty = True
                    if (dProxies[proxy_id]['categs'] or '') != (job.function_code_label or '').strip():
                        dProxies[proxy_id]['categs'] = (job.function_code_label or '').strip()
                        dirty = True
                    if (not dProxies[proxy_id]['job_id']) or (dProxies[proxy_id]['job_id'][0] != job.id):
                        dProxies[proxy_id]['job_id'] = (job.id, '')
                        dirty = True
                    if dProxies[proxy_id]['contact_id']:
                        dProxies[proxy_id]['contact_id'] = False
                        dirty = False
                    if dProxies[proxy_id]['subscriber_id']:
                        dProxies[proxy_id]['subscriber_id'] = False
                        dirty = False
                    if dProxies[proxy_id]['source'] != source:
                        dProxies[proxy_id]['source'] = source
                        dirty = True
                    if dProxies[proxy_id]['courtesy_code'] != (job.contact_id.title and dCourtesies[job.contact_id.title]['shortcut'] or ''):
                        dProxies[proxy_id]['courtesy_code'] = job.contact_id.title and dCourtesies[job.contact_id.title]['shortcut'] or ''
                        dProxies[proxy_id]['courtesy_full1'] = job.contact_id.title and dCourtesies[job.contact_id.title]['other1'] or ''
                        dProxies[proxy_id]['courtesy_full2'] = job.contact_id.title and dCourtesies[job.contact_id.title]['other2'] or ''
                        dirty = True
                    if dirty:
                        dProxies[proxy_id]['dirty'] = True
                        return ('dirty', proxy_id)
                    else:
                        return ('undelete', proxy_id)
                else:
                    return ('same_email', proxy_id)
            else:
                if selected_email not in added_emails:
                    new_data = {}
                    new_data['name'] = selected_email
                    new_data['list_name'] = list_name
                    new_data['first_name'] = (job.contact_id.first_name or '').strip()
                    new_data['last_name'] = (job.contact_id.name or '').strip()
                    company = job.address_id.partner_id.name.strip()
                    if job.address_id.name:
                        if job.address_id.name[0:2] == '- ' or job.address_id.name[0:3] == ' - ':
                            company = company + ' ' + job.address_id.name.strip()
                        else:
                            company = job.address_id.name.strip()
                    new_data['company'] = company
                    if job.contact_id.rdp_subscribe == 'never':
                        selected_area = 'none'
                    else:
                        if job.contact_id.rdp_forced_area == 'default':
                            if default_area == 'liege-namur':
                                selected_area = 'liege'
                                if job.address_id.zip_id and job.address_id.zip_id.name[0:1] == '5':
                                    selected_area = 'namur'
                            else:
                                selected_area = default_area
                        else:
                            selected_area = job.contact_id.rdp_forced_area
                    new_data['area_rdp'] = selected_area
                    new_data['title'] = (job.function_label or '').strip()
                    new_data['categs'] = (job.function_code_label or '').strip()
                    new_data['member'] = job.address_id.partner_id.membership_state in ['free', 'invoiced', 'paid']
                    new_data['job_id'] = job.id
                    new_data['contact_id'] = False
                    new_data['subscriber_id'] = False
                    new_data['source'] = source
                    new_data['courtesy_code'] = job.contact_id.title and dCourtesies[job.contact_id.title]['shortcut'] or ''
                    new_data['courtesy_full1'] = job.contact_id.title and dCourtesies[job.contact_id.title]['other1'] or ''
                    new_data['courtesy_full2'] = job.contact_id.title and dCourtesies[job.contact_id.title]['other2'] or ''
                    new_data['dirty'] = True
                    new_proxy_id = self.env['mailchimp_proxy'].create(new_data)
                    added_emails.append(selected_email)
                    return ('add', new_proxy_id)
                else:
                    return ('same_email', 0)
        else:
            return ('None', 0)
        return  True
    
    @api.model
    def _subscribe_special(self, subscriber, list_name, dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_area, source):
        dConvArea = {'1':'liege', '2':'namur', '3':'brabant_wallon', '4':'hainaut', '5':'wapi', '6':'rdpvl'}
        selected_email = self._normalize_email(subscriber.email)
        if dProxyName2ID.has_key(selected_email):
            proxy_id = dProxyName2ID[selected_email]
            if dProxies[proxy_id]['subscriber_id']:  # ## There is a subscriber ID => the email concern only special subscriber
                dProxies[proxy_id]['todelete'] = False
                # check if data have changed in cci_newletters data
                dirty = False
                if (dProxies[proxy_id]['first_name'] or '') != (subscriber.first_name or '').strip():
                    dProxies[proxy_id]['first_name'] = (subscriber.first_name or '').strip()
                    dirty = True
                if (dProxies[proxy_id]['last_name'] or '') != (subscriber.name or '').strip():
                    dProxies[proxy_id]['last_name'] = (subscriber.name or '').strip()
                    dirty = True
                if (dProxies[proxy_id]['company'] or '') != (subscriber.company_name or '').strip():
                    dProxies[proxy_id]['company'] = (subscriber.company_name or '').strip()
                    dirty = True
                if list_name == 'rdpvl':
                    final_area = 'vlanderen'
                else:
                    selected_area = subscriber.forced_area or subscriber.source_id.default_area
                    final_area = dConvArea[selected_area]
                if (dProxies[proxy_id]['area_rdp'] or '') != final_area:
                    dProxies[proxy_id]['area_rdp'] = final_area
                    dirty = True
                if (dProxies[proxy_id]['title'] or '') != '':
                    dProxies[proxy_id]['title'] = ''.strip()
                    dirty = True
                if (dProxies[proxy_id]['categs'] or '') != '':
                    dProxies[proxy_id]['categs'] = ''
                    dirty = True
                if dProxies[proxy_id]['job_id']:
                    dProxies[proxy_id]['job_id'] = False
                    dirty = True
                if dProxies[proxy_id]['contact_id']:
                    dProxies[proxy_id]['contact_id'] = False
                    dirty = False
                if dProxies[proxy_id]['source'] != source:
                    dProxies[proxy_id]['source'] = source
                    dirty = True
                if dProxies[proxy_id]['courtesy_code'] != '':
                    dProxies[proxy_id]['courtesy_code'] = ''
                    dProxies[proxy_id]['courtesy_full1'] = ''
                    dProxies[proxy_id]['courtesy_full2'] = ''
                    dirty = True
                if dirty:
                    dProxies[proxy_id]['dirty'] = True
                    return ('dirty', proxy_id)
                else:
                    return ('undelete', proxy_id)
            else:
                return ('same_email', proxy_id)
        else:
            if selected_email not in added_emails:
                new_data = {}
                new_data['name'] = selected_email
                new_data['list_name'] = list_name
                new_data['first_name'] = (subscriber.first_name or '').strip()
                new_data['last_name'] = (subscriber.name or '').strip()
                new_data['company'] = (subscriber.company_name or '').strip()
                if list_name == 'rdpvl':
                    final_area = 'none'
                else:
                    selected_area = subscriber.forced_area or subscriber.source_id.default_area
                    final_area = dConvArea[selected_area]
                new_data['area_rdp'] = final_area
                new_data['title'] = ''
                new_data['categs'] = ''
                new_data['member'] = False
                new_data['job_id'] = False
                new_data['contact_id'] = False
                new_data['subscriber_id'] = subscriber.id
                new_data['source'] = source
                new_data['courtesy_code'] = ''
                new_data['courtesy_full1'] = ''
                new_data['courtesy_full2'] = ''
                new_data['dirty'] = True
                new_proxy_id = self.env['mailchimp_proxy'].create(new_data)
                added_emails.append(selected_email)
                return ('add', new_proxy_id)
            else:
                return ('same_email', 0)
        return True
    
    @api.model
    def _get_courtesies(self):
        # we read all courtesy codes to translate them into full1 and full2
        courtesy_obj = self.env['res.partner.title']
        courtesy_ids = courtesy_obj.search([('domain', '=', 'contact')])
        courtesies = courtesy_ids.read(['name', 'shortcut', 'other1', 'other2'])
        dCourtesies = {}
        for courtesy in courtesies:
            dCourtesies[courtesy['shortcut']] = courtesy
        return dCourtesies
    
    @api.model
    def _record_change(self, dProxies, list_name, cronline_id):
        proxy_obj = self.env['mailchimp_proxy']
        # Undelete all determined
        count_delete = 0
        delete_ids = []
        deleted = []
        for (key, proxy) in dProxies.items():
            if proxy['todelete']:
                count_delete += 1
                delete_ids.append(proxy['id'])
                deleted.append(proxy['name'])
        delete_ids.write({'todelete':True})
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\n%s - Deleted : [%s]\n- ' % (list_name, str(count_delete)))
        if deleted:
            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n- '.join(deleted))

        # Write all dirties data to database and undelete them also
        count_dirty = 0
        modified = []
        for (key, proxy) in dProxies.items():
            if proxy['dirty']:
                count_dirty += 1
                new_data = {'first_name':proxy['first_name'],
                            'last_name':proxy['last_name'],
                            'company':proxy['company'],
                            'area_rdp':proxy['area_rdp'],
                            'title':proxy['title'],
                            'categs':proxy['categs'],
                            'courtesy_code':proxy['courtesy_code'],
                            'courtesy_full1':proxy['courtesy_full1'],
                            'courtesy_full2':proxy['courtesy_full2'],
                            'member':proxy['member'],
                            'job_id':proxy['job_id'] and proxy['job_id'][0] or False,
                            'contact_id':proxy['contact_id'] and proxy['contact_id'][0] or False,
                            'subscriber_id':proxy['subscriber_id'] and proxy['subscriber_id'][0] or False,
                            'source':proxy['source'],
                            'dirty':True}
                proxy_obj.write(proxy['id'], new_data)
                modified.append(proxy['name'])
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\n%s - Modified : [%s]\n- ' % (list_name, str(count_dirty)))
        if modified:
            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n- '.join(modified))
        return True
    
    @api.model
    def prepare_rdp(self, default_rdp, cronline_id):
        dCourtesies = self._get_courtesies()
        
        # We read all proxies to create a Dict 'email' -> proxy_id
        proxy_obj = self.env['mailchimp_proxy']
        proxy_ids = proxy_obj.search([('list_name', '=', 'rdp')])
        proxies = proxy_ids.read(['name', 'first_name', 'last_name', 'company', 'area_rdp', 'title', 'categs', 'courtesy_code', 'courtesy_full1', 'courtesy_full2', 'member', 'source', 'dirty', 'todelete', 'job_id', 'contact_id', 'subscriber_id'])
        dProxies = {}
        dProxyName2ID = {}
        dProxyContact2ID = {}
        for proxy in proxies:
            proxy['todelete'] = True
            dProxies[proxy['id']] = proxy
            dProxyName2ID[proxy['name']] = proxy['id']
            if proxy['contact_id']:
                dProxyContact2ID[proxy['contact_id']] = proxy['id']
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse - Current actives proxies : %s' % str(len(dProxies)))

        # We first set all active proxies as 'todelete' : this is done in the dProxies, not in the database
        # proxy_obj.write(cr,uid,proxy_ids,{'todelete':True})
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse - All deleted in first time')
        undelete = []
        dirty = []
        same = 0
        modified = 0
        added = 0
        doubles = 0
        added_emails = []
        
        parameter_obj = self.env['cci_parameters.cci_value']
        param_values = parameter_obj.get_value_from_names(['PremiumRDPMode'])
        if param_values.has_key('PremiumRDPMode') and "Subscription" in param_values['PremiumRDPMode']:
            # We extract all current Premium Subscriptions (if 'free' in mode)
            obj_sub_type = self.env['premium_subscription.type']
            type_ids = obj_sub_type.search([('code', '=', 'RDP')])
            if type_ids:
                this_day = datetime.datetime.today().strftime('%Y-%m-%d')
                close_message = "Auto End Date"
                obj_sub = self.env['premium_subscription']
                sub_ids = obj_sub.search([('state', '=', 'current'), ('type_id', 'in', type_ids), ('begin', '<=', this_day), ('end', '>=', this_day)])
                subs = sub_ids.read(['contact_id', 'end', 'specific_email'])
                dSubscribers = {}
                sub_contact_ids = []
                for subscription in subs:
                    if subscription['contact_id'] and subscription['contact_id'][0] not in sub_contact_ids:
                        dSubscribers[subscription['contact_id'][0]] = subscription
                        sub_contact_ids.append(subscription['contact_id'][0])
                contact_obj = self.env['res.partner']
                self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse - Count of premium Subscriptions : ' + str(len(sub_contact_ids)))
                sub_contacts = contact_obj.browse(sub_contact_ids)
                for contact in sub_contacts:
                    # search for the first 'en activité' linked job if jobs
                    if contact.job_ids:
                        jobs = []
                        for job in contact.job_ids:
                            jobs.append((job.sequence_contact, job))
                        sorted_jobs = sorted(jobs)
                        selected_job = False
                        for (sequence, job) in sorted_jobs:
                            if job.address_id and job.address_id.partner_id and job.address_id.partner_id.state_id.id == 1:
                                selected_job = job
                                break
                        if selected_job:
                            (state, proxy_id) = self._subscribe_job(selected_job, 'rdp', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_rdp, 'Premium Subscription Job', dSubscribers[contact.id]['specific_email'])
                            if state == 'undelete':
                                undelete.append(proxy_id)
                                same += 1
                            elif state == 'dirty':
                                dirty.append(proxy_id)
                                modified += 1
                            elif state == 'add':
                                added += 1
                            elif state == 'same_email':
                                doubles += 1
                        else:
                            # no need to search for an active job : if isolated contact has an email address, subscribe it, else forget it
                            if contact.email or dSubscribers[contact.id]['specific_email']:
                                (state, proxy_id) = self._subscribe_contact(contact, 'rdp', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_rdp, 'Premium Subscription Contact', dSubscribers[contact.id]['specific_email'])
                                if state == 'undelete':
                                    undelete.append(proxy_id)
                                    same += 1
                                elif state == 'dirty':
                                    dirty.append(proxy_id)
                                    modified += 1
                                elif state == 'add':
                                    added += 1
                                elif state == 'same_email':
                                    doubles += 1
                    else:
                        # no need to search for an active job : if isolated contact has an email address, subscribe it, else forget it
                        if contact.email or dSubscribers[contact.id]['specific_email']:
                            (state, proxy_id) = self._subscribe_contact(contact, 'rdp', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_rdp, 'Premium Subscription Contact', dSubscribers[contact.id]['specific_email'])
                            if state == 'undelete':
                                undelete.append(proxy_id)
                                same += 1
                            elif state == 'dirty':
                                dirty.append(proxy_id)
                                modified += 1
                            elif state == 'add':
                                added += 1
                            elif state == 'same_email':
                                doubles += 1
            self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse - Premium Subscriptions recorded : Same : %s - Modified : %s - Added : %s - Doubles : %s' % (str(same), str(modified), str(added), str(doubles)))

        if param_values.has_key('PremiumRDPMode') and "Free" in param_values['PremiumRDPMode']:
            search_tuples = ['|', ('rdp_subscribe', '=', 'always'), ('is_premium', '=', 'OUI')]
        else:
            search_tuples = [('rdp_subscribe', '=', 'always')]
        # We extract all 'forced_rdp' and all 'premium' (if 'free' in mode)
        contact_obj = self.env['res.partner']
        forced_contact_ids = contact_obj.search(search_tuples)
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse - Count of forced : ' + str(len(forced_contact_ids)))
        forced_contacts = contact_obj.browse(forced_contact_ids)
        for contact in forced_contacts:
            # search for the first 'en activité' linked job if jobs
            if contact.job_ids:
                jobs = []
                for job in contact.job_ids:
                    jobs.append((job.sequence_contact, job))
                sorted_jobs = sorted(jobs)
                selected_job = False
                for (sequence, job) in sorted_jobs:
                    if job.address_id and job.address_id.partner_id and job.address_id.partner_id.state_id.id == 1:
                        selected_job = job
                        break
                if selected_job:
                    (state, proxy_id) = self._subscribe_job(selected_job, 'rdp', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_rdp, 'Self Forced Job', False)
                    if state == 'undelete':
                        undelete.append(proxy_id)
                        same += 1
                    elif state == 'dirty':
                        dirty.append(proxy_id)
                        modified += 1
                    elif state == 'add':
                        added += 1
                    elif state == 'same_email':
                        doubles += 1
                else:
                    # no need to search for an active job : if isolated contact has an email address, subscribe it, else forget it
                    if contact.email:
                        (state, proxy_id) = self._subscribe_contact(contact, 'rdp', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_rdp, 'Self Forced Contact', False)
                        if state == 'undelete':
                            undelete.append(proxy_id)
                            same += 1
                        elif state == 'dirty':
                            dirty.append(proxy_id)
                            modified += 1
                        elif state == 'add':
                            added += 1
                        elif state == 'same_email':
                            doubles += 1
            else:
                # no need to search for an active job : if isolated contact has an email address, subscribe it, else forget it
                if contact.email:
                    (state, proxy_id) = self._subscribe_contact(contact, 'rdp', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_rdp, 'Self Forced Contact', False)
                    if state == 'undelete':
                        undelete.append(proxy_id)
                        same += 1
                    elif state == 'dirty':
                        dirty.append(proxy_id)
                        modified += 1
                    elif state == 'add':
                        added += 1
                    elif state == 'same_email':
                        doubles += 1
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse - Forced recorded : Same : %s - Modified : %s - Added : %s - Doubles : %s' % (str(same), str(modified), str(added), str(doubles)))
                        
        # We search all 'default' contacts with email address (on job or contact) linked to members
        same = 0
        modified = 0
        added = 0
        doubles = 0
        partner_obj = self.env['res.partner']
        partners = partner_obj.search([('membership_state', 'in', ['free', 'invoiced', 'paid']), ('state_id', '=', 1)])
        default_job_ids = []
        for partner in partners:
            if partner.address:
                for addr in partner.child_ids:
                    if addr.job_ids:
                        for job in addr.job_ids:
                            if job.contact_id and job.contact_id.active:
                                email_present = job.email or job.contact_id.email
                                if email_present and job.contact_id.rdp_subscribe == 'default':
                                    default_job_ids.append(job.id)
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse - Count of default : ' + str(len(default_job_ids)))
        job_obj = self.env['res.partner.job']
        default_jobs = job_obj.browse(default_job_ids)
        for job in default_jobs:
            (state, proxy_id) = self._subscribe_job(job, 'rdp', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_rdp, 'Default Job', False)
            if state == 'undelete':
                undelete.append(proxy_id)
                same += 1
            elif state == 'dirty':
                dirty.append(proxy_id)
                modified += 1
            elif state == 'add':
                added += 1
            elif state == 'same_email':
                doubles += 1
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse - Default Jobs : Same : %s - Modified : %s - Added : %s - Doubles : %s' % (str(same), str(modified), str(added), str(doubles)))
        
        # We add the additional email addresses from manual subscribers
        today = datetime.date.today().strftime('%Y-%m-%d')
        subs_same = 0
        subs_modified = 0
        subs_added = 0
        subs_doubles = 0
        # we extract the sources except those concerning flanders
        source_obj = self.env['cci_newsletter.source']
        source_ids = source_obj.search([('flanders', '=', False)])
        #
        subscriber_obj = self.env['cci_newsletter.subscriber']
        subscribers = subscriber_obj.search([('source_id', 'in', source_ids), '|', ('expire', '>=', today), ('expire', '=', False)])
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse - Additional Subscribers not expired : %s' % str(len(subscriber_ids)))
        for subscriber in subscribers:
            (state, proxy_id) = self._subscribe_special(subscriber, 'rdp', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, default_rdp, 'Subscriber ' + subscriber.source_id.name)
            if state == 'undelete':
                undelete.append(proxy_id)
                subs_same += 1
            elif state == 'dirty':
                dirty.append(proxy_id)
                subs_modified += 1
            elif state == 'add':
                subs_added += 1
            elif state == 'same_email':
                subs_doubles += 1
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse - Additional Subscribers : Same : %s - Modified : %s - Added : %s - Doubles : %s' % (str(subs_same), str(subs_modified), str(subs_added), str(subs_doubles)))
        self._record_change(dProxies, 'rdp', cronline_id)
        return added_emails
    
    @api.model
    def prepare_agenda(self, cronline_id):
        dCourtesies = self._get_courtesies()
        
        # We read all proxies to create a Dict 'email' -> proxy_id
        proxy_obj = self.env['mailchimp_proxy']
        proxy_ids = proxy_obj.search([('list_name', '=', 'agenda')])
        proxies = proxy_ids.read(['name', 'first_name', 'last_name', 'company', 'area_rdp', 'title', 'categs', 'courtesy_code', 'courtesy_full1', 'courtesy_full2', 'member', 'source', 'dirty', 'todelete', 'job_id', 'contact_id', 'subscriber_id'])
        dProxies = {}
        dProxyName2ID = {}
        dProxyContact2ID = {}
        for proxy in proxies:
            proxy['todelete'] = True
            dProxies[proxy['id']] = proxy
            dProxyName2ID[proxy['name']] = proxy['id']
            if proxy['contact_id']:
                dProxyContact2ID[proxy['contact_id']] = proxy['id']
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAgenda - Current actives proxies : %s' % str(len(dProxies)))
        
        # We first set all active proxies as 'todelete' : this is done in the dProxies, not in the database
        # proxy_obj.write(cr,uid,proxy_ids,{'todelete':True})
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAgenda - All deleted in first time')
        undelete = []
        dirty = []
        same = 0
        modified = 0
        added = 0
        doubles = 0
        added_emails = []
        
        # We extract all 'forced_agenda' (or premium)
        contact_obj = self.env['res.partner']
        forced_contact_ids = contact_obj.search(['|', ('agenda_subscribe', '=', 'always'), ('is_premium', '=', 'OUI')])
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAgenda - Count of forced : ' + str(len(forced_contact_ids)))
        forced_contacts = contact_obj.browse(forced_contact_ids)
        for contact in forced_contacts:
            # search for the first 'en activité' linked job if jobs
            if contact.job_ids:
                jobs = []
                for job in contact.job_ids:
                    jobs.append((job.sequence_contact, job))
                sorted_jobs = sorted(jobs)
                selected_job = False
                for (sequence, job) in sorted_jobs:
                    if job.address_id and job.address_id.partner_id and job.address_id.partner_id.state_id.id == 1:
                        selected_job = job
                        break
                if selected_job:
                    (state, proxy_id) = self._subscribe_job(selected_job, 'agenda', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'none', 'Self Forced Contact', False)
                    if state == 'undelete':
                        undelete.append(proxy_id)
                        same += 1
                    elif state == 'dirty':
                        dirty.append(proxy_id)
                        modified += 1
                    elif state == 'add':
                        added += 1
                    elif state == 'same_email':
                        doubles += 1
                else:
                    # no need to search for an active job : if isolated contact has an email address, subscribe it, else forget it
                    if contact.email:
                        (state, proxy_id) = self._subscribe_contact(contact, 'agenda', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'none', 'Self Forced Contact', False)
                        if state == 'undelete':
                            undelete.append(proxy_id)
                            same += 1
                        elif state == 'dirty':
                            dirty.append(proxy_id)
                            modified += 1
                        elif state == 'add':
                            added += 1
                        elif state == 'same_email':
                            doubles += 1
            else:
                # no need to search for an active job : if isolated contact has an email address, subscribe it, else forget it
                if contact.email:
                    (state, proxy_id) = self._subscribe_contact(contact, 'agenda', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'none', 'Self Forced Contact', False)
                    if state == 'undelete':
                        undelete.append(proxy_id)
                        same += 1
                    elif state == 'dirty':
                        dirty.append(proxy_id)
                        modified += 1
                    elif state == 'add':
                        added += 1
                    elif state == 'same_email':
                        doubles += 1
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAgenda - Forced recorded : Same : %s - Modified : %s - Added : %s - Doubles : %s' % (str(same), str(modified), str(added), str(doubles)))
                        
        # We search all 'default' contacts with email address (on job or contact) linked to members
        same = 0
        modified = 0
        added = 0
        doubles = 0
        partner_obj = self.env['res.partner']
        partner_ids = partner_obj.search([('membership_state', 'in', ['free', 'invoiced', 'paid']), ('state_id', '=', 1)])
        partners = partner_obj.browse(partner_ids)
        default_job_ids = []
        for partner in partners:
            if partner.address:
                for addr in partner.child_ids:
                    if addr.job_ids:
                        for job in addr.job_ids:
                            if job.contact_id and job.contact_id.active:
                                email_present = job.email or job.contact_id.email
                                if email_present and job.contact_id.rdp_subscribe == 'default':
                                    default_job_ids.append(job.id)
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAgenda - Count of default : ' + str(len(default_job_ids)))
        job_obj = self.env['res.partner.job']
        default_jobs = job_obj.browse(default_job_ids)
        for job in default_jobs:
            (state, proxy_id) = self._subscribe_job(job, 'agenda', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'none', 'Default Job', False)
            if state == 'undelete':
                undelete.append(proxy_id)
                same += 1
            elif state == 'dirty':
                dirty.append(proxy_id)
                modified += 1
            elif state == 'add':
                added += 1
            elif state == 'same_email':
                doubles += 1
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAgenda - Default Jobs : Same : %s - Modified : %s - Added : %s - Doubles : %s' % (str(same), str(modified), str(added), str(doubles)))
        self._record_change(dProxies, 'agenda', cronline_id)
        return added_emails
    
    @api.model
    def prepare_alterego(self, cronline_id):
        dCourtesies = self._get_courtesies()
        
        # We read all proxies to create a Dict 'email' -> proxy_id
        proxy_obj = self.env['mailchimp_proxy']
        proxy_ids = proxy_obj.search([('list_name', '=', 'alterego')])
        proxies = proxy_ids.read(['name', 'first_name', 'last_name', 'company', 'area_rdp', 'title', 'categs', 'courtesy_code', 'courtesy_full1', 'courtesy_full2', 'member', 'source', 'dirty', 'todelete', 'job_id', 'contact_id', 'subscriber_id'])
        dProxies = {}
        dProxyName2ID = {}
        dProxyContact2ID = {}
        for proxy in proxies:
            proxy['todelete'] = True
            dProxies[proxy['id']] = proxy
            dProxyName2ID[proxy['name']] = proxy['id']
            if proxy['contact_id']:
                dProxyContact2ID[proxy['contact_id']] = proxy['id']
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAlter Ego - Current actives proxies : %s' % str(len(dProxies)))

        # We first set all active proxies as 'todelete' : this is done in the dProxies, not in the database
        # proxy_obj.write(cr,uid,proxy_ids,{'todelete':True})
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAlter Ego - All deleted in first time')
        undelete = []
        dirty = []
        same = 0
        modified = 0
        added = 0
        doubles = 0
        added_emails = []
        
        # We extract all 'forced_alterego'
        contact_obj = self.env['res.partner']
        job_obj = self.env['res.partner']
        forced_contact_ids = contact_obj.search([('alterego_subscribe', '=', 'always')])
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAlter Ego - Count of forced : ' + str(len(forced_contact_ids)))
        forced_contacts = contact_obj.browse(forced_contact_ids)
        for contact in forced_contacts:
            # search for the first 'en activité' linked job if jobs
            if contact.job_ids:
                jobs = []
                for job in contact.job_ids:
                    jobs.append((job.sequence_contact, job))
                sorted_jobs = sorted(jobs)
                selected_job = False
                for (sequence, job) in sorted_jobs:
                    if job.address_id and job.address_id.partner_id and job.address_id.partner_id.state_id.id == 1:
                        selected_job = job
                        break
                if selected_job:
                    (state, proxy_id) = self._subscribe_job(selected_job, 'alterego', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'none', 'Self Forced Job', False)
                    if state == 'undelete':
                        undelete.append(proxy_id)
                        same += 1
                    elif state == 'dirty':
                        dirty.append(proxy_id)
                        modified += 1
                    elif state == 'add':
                        added += 1
                    elif state == 'same_email':
                        doubles += 1
            else:
                # no need to search for an active job : if isolated contact has an email address, subscribe it, else forget it
                if contact.email:
                    (state, proxy_id) = self._subscribe_contact(contact, 'alterego', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'none', 'Self Forced Contact', False)
                    if state == 'undelete':
                        undelete.append(proxy_id)
                        same += 1
                    elif state == 'dirty':
                        dirty.append(proxy_id)
                        modified += 1
                    elif state == 'add':
                        added += 1
                    elif state == 'same_email':
                        doubles += 1
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAlter Ego - Forced recorded : Same : %s - Modified : %s - Added : %s - Doubles : %s' % (str(same), str(modified), str(added), str(doubles)))

        # We search for all regular 'alter ego' customers not marked as 'never'
        parameter_obj = self.env['cci_parameters.cci_value']
        param_values = parameter_obj.get_value_from_names(['MailChimpAESynchro_ClubTypes', 'MailChimpAESynchro_ClubStates', 'MailChimpAESynchro_AddContacts'])
        if param_values.has_key('MailChimpAESynchro_ClubTypes') and param_values.has_key('MailChimpAESynchro_ClubStates') and param_values.has_key('MailChimpAESynchro_AddContacts'):
            club_obj = self.env['cci_club.club']
            clubs = club_obj.search([('type_id', 'in', param_values['MailChimpAESynchro_ClubTypes']), ('state', 'in', param_values['MailChimpAESynchro_ClubStates'])])
            if clubs:
                same = 0
                modified = 0
                added = 0
                doubles = 0
                for club in clubs:
                    for particip in club.participation_ids:
                        if particip.email and ('actif' in particip.state_id.name.lower() or 'active' in particip.state_id.name.lower()):
                            # Participation to publish : we search for a job corresponding to this participation
                            selected_job = False
                            if particip.partner_id and particip.partner_id.address:
                                for addr in particip.partner_id.address:
                                    if addr.job_ids:
                                        for job in addr.job_ids:
                                            if job.contact_id and job.contact_id.id == particip.contact_id.id and job.contact_id.alterego_subscribe != 'never':
                                                selected_job = job
                                                break
                                        if selected_job:
                                            break
                            if selected_job:
                                (state, proxy_id) = self._subscribe_job(selected_job, 'alterego', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'none', 'Part Alter Ego', False)
                                if state == 'undeladded_emails = ete':
                                    undelete.append(proxy_id)
                                    same += 1
                                elif state == 'dirty':
                                    dirty.append(proxy_id)
                                    modified += 1
                                elif state == 'add':
                                    added += 1
                                elif state == 'same_email':
                                    doubles += 1
                    if 'formative' in param_values['MailChimpAESynchro_AddContacts']:
                        # formative : we try to fond the job between school and formative; else we use only formative
                        selected_job = False
                        if club.school_id and club.school_id.address:
                            for addr in club.school_id.address:
                                if addr.job_ids:
                                    for job in addr.job_ids:
                                        if job.contact_id and job.contact_id.id == club.formative_id.id and club.formative_id.alterego_subscribe != 'never':
                                            selected_job = job
                                            break
                                    if selected_job:
                                        break
                        if selected_job:
                            (state, proxy_id) = self._subscribe_job(selected_job, 'alterego', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'none', 'Formative Alter Ego', False)
                            if state == 'undelete':
                                undelete.append(proxy_id)
                                same += 1
                            elif state == 'dirty':
                                dirty.append(proxy_id)
                                modified += 1
                            elif state == 'add':
                                added += 1
                            elif state == 'same_email':
                                doubles += 1
                        else:
                            if club.formative_id.email:
                                (state, proxy_id) = self._subscribe_contact(club.formative_id, 'alterego', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'none', 'Formative Alter Ego', False)
                                if state == 'undelete':
                                    undelete.append(proxy_id)
                                    same += 1
                                elif state == 'dirty':
                                    dirty.append(proxy_id)
                                    modified += 1
                                elif state == 'add':
                                    added += 1
                                elif state == 'same_email':
                                    doubles += 1
                    if 'responsible' in param_values['MailChimpAESynchro_AddContacts']:
                        if club.responsible_id and club.responsible_id.email:
                            job = job_obj.search([('email', '=', club.responsible_id.email)], limit=1)
                            if job:
                                (state, proxy_id) = self._subscribe_job(job, 'alterego', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'none', 'Responsible Alter Ego', False)
                                if state == 'undelete':
                                    undelete.append(proxy_id)
                                    same += 1
                                elif state == 'dirty':
                                    dirty.append(proxy_id)
                                    modified += 1
                                elif state == 'add':
                                    added += 1
                                elif state == 'same_email':
                                    doubles += 1
                self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAlter Ego - Normal customers : Same : %s - Modified : %s - Added : %s - Doubles : %s' % (str(same), str(modified), str(added), str(doubles)))
                self._record_change(dProxies, 'alterego', cronline_id)
            else:
                self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAlter Ego - No clubs defined as Alter Ego')
        else:
            self.env['cci_logs.cron_line']._addComment(cronline_id, '\nAlter Ego - No parameters to manage Alter Ego List => ignore this step [MailChimpAESynchro_ClubTypes,MailChimpAESynchro_ClubStates,MailChimpAESynchro_AddContacts]')
        return added_emails
    
    @api.model
    def prepare_rdpvl(self, cronline_id):
        dCourtesies = self._get_courtesies()
        
        # We read all proxies to create a Dict 'email' -> proxy_id
        proxy_obj = self.env['mailchimp_proxy']
        proxy_ids = proxy_obj.search([('list_name', '=', 'rdpvl')])
        proxies = proxy_ids.read(['name', 'first_name', 'last_name', 'company', 'area_rdp', 'title', 'categs', 'courtesy_code', 'courtesy_full1', 'courtesy_full2', 'member', 'source', 'dirty', 'todelete', 'job_id', 'contact_id', 'subscriber_id'])
        dProxies = {}
        dProxyName2ID = {}
        dProxyContact2ID = {}
        for proxy in proxies:
            proxy['todelete'] = True
            dProxies[proxy['id']] = proxy
            dProxyName2ID[proxy['name']] = proxy['id']
            if proxy['contact_id']:
                dProxyContact2ID[proxy['contact_id']] = proxy['id']
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse Vlanderen - Current actives proxies : %s' % str(len(dProxies)))

        # We first set all active proxies as 'todelete' : this is done in the dProxies, not in the database
        # proxy_obj.write(cr,uid,proxy_ids,{'todelete':True})
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse Vlanderen - All deleted in first time')
        undelete = []
        dirty = []
        same = 0
        modified = 0
        added = 0
        doubles = 0
        added_emails = []
                
        # We add the additional email addresses from manual subscribers
        today = datetime.date.today().strftime('%Y-%m-%d')
        subs_same = 0
        subs_modified = 0
        subs_added = 0
        subs_doubles = 0
        # we extract the source concerning flanders
        source_obj = self.env['cci_newsletter.source']
        source_ids = source_obj.search([('flanders', '=', True)])
        #
        subscriber_obj = self.env['cci_newsletter.subscriber']
        subscriber_ids = subscriber_obj.search([('source_id', 'in', source_ids), '|', ('expire', '>=', today), ('expire', '=', False)])
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse Vlanderen - Additional Subscribers not expired : %s' % str(len(subscriber_ids)))
        subscribers = subscriber_obj.browse(subscriber_ids)
        for subscriber in subscribers:
            (state, proxy_id) = self._subscribe_special(subscriber, 'rdpvl', dProxies, dProxyName2ID, dProxyContact2ID, dCourtesies, added_emails, 'vlanderen', 'Subscriber ' + subscriber.source_id.name)
            if state == 'undelete':
                undelete.append(proxy_id)
                subs_same += 1
            elif state == 'dirty':
                dirty.append(proxy_id)
                subs_modified += 1
            elif state == 'add':
                subs_added += 1
            elif state == 'same_email':
                subs_doubles += 1
        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nRevue de Presse Vlanderen - Additional Subscribers : Same : %s - Modified : %s - Added : %s - Doubles : %s' % (str(subs_same), str(subs_modified), str(subs_added), str(subs_doubles)))
        self._record_change(dProxies, 'rdp', cronline_id)
        return added_emails
    
    @api.model
    def prepare_update(self, default_rdp='liege-namur', sources=['rdp', 'agenda', 'alterego', 'rdp_vlanderen']):
        # start log 
        cronline_id = self.env['cci_logs.cron_line']._start('MailChimpPreparation')
        final_result = True
        
        # we validate asked sources
        correct_sources = []
        for source in sources:
            if source in ('rdp', 'agenda', 'alterego', 'rdp_vlanderen'):
                correct_sources.append(source)
            else:
                self.env['cci_logs.cron_line']._addComment(cronline_id, '\nWrong parameter : unknown source : %s' % source)

        if correct_sources:
            if 'rdp' in correct_sources:
                added_emails = self.prepare_rdp(default_rdp, cronline_id)
                self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\nRevue de Presse - Added Emails :\n')
                if added_emails:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n- '.join(added_emails))
                else:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, 'None')
            if 'agenda' in correct_sources:
                added_emails = self.prepare_agenda(cronline_id)
                self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\nAgenda - Added Emails :\n')
                if added_emails:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n- '.join(added_emails))
                else:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, 'None')
            if 'alterego' in correct_sources:
                added_emails = self.prepare_alterego(cronline_id)
                self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\nAlter Ego - Added Emails :\n')
                if added_emails:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n- '.join(added_emails))
                else:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, 'None')
            if 'rdp_vlanderen' in correct_sources:
                added_emails = self.prepare_rdpvl(cronline_id)
                self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\nRDP Vlanderen - Added Emails :\n')
                if added_emails:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n- '.join(added_emails))
                else:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, 'None')
        else:
            self.env['cci_logs.cron_line']._addComment(cronline_id, '\nNo correct source of extractions')

        # end log to show all is good
        final_result = True
        self.env['cci_logs.cron_line']._stop(cronline_id, final_result, '\n---end---')
        return True
    
    def send_updates(self, limit=100, lists=['rdp', ], other_sources=[], test_addresses=[]):
        # limit = nombre max de records à synchroniser en une seule commande 'batch_update'
        # lists = liste des identifiants de listes à uploader : rdp, agenda et alterego actuellement sont reconnus mais
        #         il est relativement facile d'en ajouter
        # other_sources = liste de sources de 'mailchimp_proxy' supplémentaires. Ces sources seront interrogées via xml-rpc.
        #    format : [{'url':...,'login':...,'pw':...,'db':...,'list_name':...,'source_prefix':...}, {...}] ### source-prefix ne sera sans doute pas utilisé
        # test_addresses : = liste des adresses emails supplémentaires avec la area_rdp = 'test'
        #    format : [{same name as mailchimp_proxy},{}]
    
        # start log 
        cronline_id = self.env['cci_logs.cron_line']._start('MailChimpSynchro')
        final_result = False

        if lists:
                
            # We get the API key
            parameter_obj = self.env['cci_parameters.cci_value']
            param_values = parameter_obj.get_value_from_names(['MailChimpAPIKey'])
            if param_values.has_key('MailChimpAPIKey'):

                # We create necessary MailChimp objects
                mailchimp_server = mailchimp.Mailchimp(param_values['MailChimpAPIKey'], False)
                mailchimp_lists = mailchimp.Lists(mailchimp_server)

                for list_name in lists:
                    param_list_values = parameter_obj.get_value_from_names(['MailChimp%sListID' % list_name.upper()])
                    if param_list_values.has_key('MailChimp%sListID' % list_name.upper()):

                        mailchimp_list_id = param_list_values['MailChimp%sListID' % list_name.upper()]
                        
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nStart of synchronisation of List %s' % list_name)
                        # We first manage all externals data sources
                        # so, if an email address exists on external data sources AND internal,
                        # the internal data will be used in last and supersede the external datas
                        if other_sources:
                            for data_source in other_sources:
                                if data_source['list_name'] == list_name:
                                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n Start of synchronisation of external source %s' % data_source['db'])
                                    sock = xmlrpclib.ServerProxy(data_source['url'] + '/object')
                                    sock3 = xmlrpclib.ServerProxy(data_source['url'] + '/common')
                                    external_uid = sock3.login(data_source['db'], data_source['login'], data_source['pw'])
                                    external_proxy_ids = sock.execute(data_source['db'], external_uid, data_source['pw'], 'mailchimp_proxy', 'search', [('list_name', '=', list_name), ('dirty', '=', True)])
                                    if external_proxy_ids:
                                        added = []
                                        changed = []
                                        offset = 0
                                        while(external_proxy_ids[offset:offset + limit]):
                                            external_proxies = sock.execute(data_source['db'], external_uid, data_source['pw'], 'mailchimp_proxy', 'read', external_proxy_ids[offset:offset + limit], ['id', 'name', 'area_rdp', 'first_name', 'last_name'])
                                            changes = []
                                            dProxyEMail2ID = {}
                                            for proxy in external_proxies:
                                                changes.append({'email':{'email':proxy['name']},
                                                                 'email_type':'html',
                                                                 'merge_vars':{'RDP':proxy['area_rdp'],
                                                                               'FNAME':proxy['first_name'] or '',
                                                                               'LNAME':proxy['last_name'] or '',
                                                                              }
                                                                })
                                                dProxyEMail2ID[proxy['name']] = proxy['id']
                                            result = mailchimp_lists.batch_subscribe(mailchimp_list_id, changes, double_optin=False, update_existing=True, replace_interests=False)
                                            # traitement du résultat
                                            if result['error_count'] > 0:
                                                # enregistrement des erreurs au fur et à mesure
                                                for error in result['errors']:
                                                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n    Erreur [%s] pour [%s] : %s' % (str(error['code']), error['email']['email'], error['error']))
                                            if result['add_count'] > 0:
                                                added_ids = []
                                                for add in result['adds']:
                                                    added.append(add['email'])
                                                    if dProxyEMail2ID.has_key(add['email']):
                                                        added_ids.append(dProxyEMail2ID[add['email']])
                                                sock.execute(data_source['db'], external_uid, data_source['pw'], 'mailchimp_proxy', 'write', added_ids, {'dirty':False})
                                            if result['update_count'] > 0:
                                                changed_ids = []
                                                for update in result['updates']:
                                                    changed.append(update['email'])
                                                    if dProxyEMail2ID.has_key(update['email']):
                                                        changed_ids.append(dProxyEMail2ID[update['email']])
                                                sock.execute(data_source['db'], external_uid, data_source['pw'], 'mailchimp_proxy', 'write', changed_ids, {'dirty':False})
                                            offset += limit

                                        # enregistrement de toutes les adresses ajoutées
                                        self.env['cci_logs.cron_line']._addComment(cronline_id, u'\n\n  Nouvelles adresses email ajoutées :\n- ')
                                        if added:
                                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  - '.join(added))
                                        else:
                                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  Aucune !')
                                        # enregistrement de toutes les adresses synchronisées
                                        self.env['cci_logs.cron_line']._addComment(cronline_id, u'\n\n  Adresses email mises à jour :\n- ')
                                        if changed:
                                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  - '.join(changed))
                                        else:
                                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  Aucune !')
                                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n End of synchronisation of external source %s' % data_source['db'])

                                    # We set 'inactive' all 'todelete' external proxies after unsubscribing them
                                    external_proxy_ids = sock.execute(data_source['db'], external_uid, data_source['pw'], 'mailchimp_proxy', 'search', [('list_name', '=', list_name), ('todelete', '=', True)])
                                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\n  External emails to unsubscribe : %s\n' % str(len(external_proxy_ids)))
                                    if external_proxy_ids:
                                        deleted = []
                                        offset = 0
                                        while(external_proxy_ids[offset:offset + limit]):
                                            # extract the needed data for the partners
                                            external_proxies = sock.execute(data_source['db'], external_uid, data_source['pw'], 'mailchimp_proxy', 'read', external_proxy_ids[offset:offset + limit], ['id', 'name'])
                                            changes = []
                                            dProxyEMail2ID = {}
                                            for proxy in external_proxies:
                                                changes.append({'email':proxy['name']})
                                                dProxyEMail2ID[proxy['name']] = proxy['id']
                                            result = mailchimp_lists.batch_unsubscribe(mailchimp_list_id, changes, delete_member=True, send_goodbye=False, send_notify=False)
                                            # traitement du résultat
                                            emails_not_deleted = []
                                            if result['error_count'] > 0:
                                                # enregistrement des erreurs au fur et à mesure
                                                self.env['cci_logs.cron_line']._addComment(cronline_id, u'\nErreurs :')
                                                for error in result['errors']:
                                                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\nErreur [%s] pour [%s] : %s' % (str(error['code']), error['email']['email'], error['error']))
                                                emails_not_deleted.append(error['email']['email'])
                                            tomarkasdeleted = []
                                            reallydeleted = []
                                            for change in changes:
                                                if (not emails_not_deleted) or (emails_not_deleted and change['email'] not in emails_not_deleted):
                                                    reallydeleted.append(change['email'])
                                                    tomarkasdeleted.append(dProxyEMail2ID[change['email']])
                                            if tomarkasdeleted:
                                                sock.execute(data_source['db'], external_uid, data_source['pw'], 'mailchimp_proxy', 'write', tomarkasdeleted, {'active':False})
                                            self.env['cci_logs.cron_line']._addComment(cronline_id, u'\n  Emails effacés :\n- ')
                                            if reallydeleted:
                                                self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  - '.join(reallydeleted))
                                            else:
                                                self.env['cci_logs.cron_line']._addComment(cronline_id, u'  Aucun')
                                            offset += limit

                        # We send new-modified records in Mailchimp proxies the marking them as 'no more dirty'
                        proxy_obj = self.env['mailchimp_proxy']
                        proxy_ids = proxy_obj.search([('dirty', '=', True), ('list_name', '=', list_name)])
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n Start of synchronisation of internal data')
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  New or modified internal emails to synchronize : %s\n' % str(len(proxy_ids)))
                        self.env['cci_logs.cron_line']._addComment(cronline_id, u'\n   Erreurs éventuelles :')
                        if proxy_ids:
                            added = []
                            changed = []
                            offset = 0
                            while(proxy_ids[offset:offset + limit]):
                                # extract the needed data for the partners
                                read_ids = proxy_ids[offset:offset + limit]
                                proxies = proxy_obj.read(read_ids, ['name', 'first_name', 'last_name', 'company', 'area_rdp', 'agenda', 'alterego', 'title', 'categs', 'courtesy_code', 'courtesy_full1', 'courtesy_full2', 'member'])
                                changes = []
                                dProxyEMail2ID = {}
                                for proxy in proxies:
                                    changes.append({'email':{'email':proxy['name']},
                                                     'email_type':'html',
                                                     'merge_vars':{'RDP':proxy['area_rdp'],
                                                                   'FNAME':proxy['first_name'] or '',
                                                                   'LNAME':proxy['last_name'] or '',
                                                                  }
                                                    })
                                    dProxyEMail2ID[proxy['name']] = proxy['id']
                                result = mailchimp_lists.batch_subscribe(mailchimp_list_id, changes, double_optin=False, update_existing=True, replace_interests=False)
                                # traitement du résultat
                                if result['error_count'] > 0:
                                    # enregistrement des erreurs au fur et à mesure
                                    for error in result['errors']:
                                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n    Erreur [%s] pour [%s] : %s' % (str(error['code']), error['email']['email'], error['error']))
                                if result['add_count'] > 0:
                                    added_ids = []
                                    for add in result['adds']:
                                        added.append(add['email'])
                                        if dProxyEMail2ID.has_key(add['email']):
                                            added_ids.append(dProxyEMail2ID[add['email']])
                                    proxy_obj.write(added_ids, {'dirty':False})
                                if result['update_count'] > 0:
                                    changed_ids = []
                                    for update in result['updates']:
                                        changed.append(update['email'])
                                        if dProxyEMail2ID.has_key(update['email']):
                                            changed_ids.append(dProxyEMail2ID[update['email']])
                                    proxy_obj.write(changed_ids, {'dirty':False})
                                offset += limit

                            # enregistrement de toutes les adresses ajoutées
                            self.env['cci_logs.cron_line']._addComment(cronline_id, u'\n\n  Nouvelles adresses email ajoutées :\n- ')
                            if added:
                                self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  - '.join(added))
                            else:
                                self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  Aucune !')
                            # enregistrement de toutes les adresses synchronisées
                            self.env['cci_logs.cron_line']._addComment(cronline_id, u'\n\n  Adresses email mises à jour :\n- ')
                            if changed:
                                self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  - '.join(changed))
                            else:
                                self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  Aucune !')
                                
                        # We set 'inactive' all 'todelete' proxies after unsubscribing them
                        proxy_obj = self.env['mailchimp_proxy']
                        proxy_ids = proxy_obj.search([('todelete', '=', True), ('list_name', '=', list_name)])
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\n  Internal emails to unsubscribe : %s\n' % str(len(proxy_ids)))
                        if proxy_ids:
                            deleted = []
                            offset = 0
                            while(proxy_ids[offset:offset + limit]):
                                # extract the needed data for the partners
                                read_ids = proxy_ids[offset:offset + limit]
                                proxies = proxy_obj.read(read_ids, ['name'])
                                changes = []
                                dProxyEMail2ID = {}
                                for proxy in proxies:
                                    changes.append({'email':proxy['name']})
                                    dProxyEMail2ID[proxy['name']] = proxy['id']
                                result = mailchimp_lists.batch_unsubscribe(mailchimp_list_id, changes, delete_member=True, send_goodbye=False, send_notify=False)
                                # traitement du résultat
                                emails_not_deleted = []
                                if result['error_count'] > 0:
                                    # enregistrement des erreurs au fur et à mesure
                                    self.env['cci_logs.cron_line']._addComment(cronline_id, u'\nErreurs :')
                                    for error in result['errors']:
                                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nErreur [%s] pour [%s] : %s' % (str(error['code']), error['email']['email'], error['error']))
                                    emails_not_deleted.append(error['email']['email'])
                                tomarkasdeleted = []
                                reallydeleted = []
                                for change in changes:
                                    if (not emails_not_deleted) or (emails_not_deleted and change['email'] not in emails_not_deleted):
                                        reallydeleted.append(change['email'])
                                        tomarkasdeleted.append(dProxyEMail2ID[change['email']])
                                if tomarkasdeleted:
                                    proxy_obj.write(tomarkasdeleted, {'active':False})
                                self.env['cci_logs.cron_line']._addComment(cronline_id, u'\n  Emails effacés :\n- ')
                                if reallydeleted:
                                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  - '.join(reallydeleted))
                                else:
                                    self.env['cci_logs.cron_line']._addComment(cronline_id, u'  Aucun')
                                offset += limit
                        final_result = True
                    else:
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\nParameters missing : [MailChimp%sListID] - No steps executed' % list_name.upper())
            else:
                self.env['cci_logs.cron_line']._addComment(cronline_id, '\nParameters missing : [MailChimpAPIKey] - No steps executed')
        else:
            self.env['cci_logs.cron_line']._addComment(cronline_id, '\nNo list to synchronise - nothing to do')
        # end log to show all is good
        self.env['cci_logs.cron_line']._stop(cronline_id, final_result, '\n---end---')
        return True
    
    def delete_email(self, emails_list, send2responsibles=False):
        # start log
        cronline_id = self.env['cci_logs.cron_line']._start('MailsDelete')
        final_result = False
        final_count = 0
        if emails_list:
            # create the list of source->responsible_email
            today = datetime.datetime.today().strftime('%Y-%m-%d')
            source_obj = self.env['cci_newsletter.source']
            source_ids = source_obj.search([])
            sources = source_obj.read(source_ids, ['name', 'followup_email'])
            dResponsibles = {}
            for source in sources:
                if source['followup_email']:
                    dResponsibles[source['followup_email']] = []
            self.env['cci_logs.cron_line']._addComment(cronline_id, 'Responsible emails for source follow-up : %s' % str(len(dResponsibles)))
            address_obj = self.env['res.partner']
            job_obj = self.env['res.partner']
            contact_obj = self.env['res.partner']
            subscriber_obj = self.env['cci_newsletter.subscriber']
            for email in emails_list:
                # We search for it on res.partner.address, res.partner.job, res.partner.contact, cci_newsletter.subscriber
                # If found on subscriber, warn by email the concerned follow-up responsible
                found = False
                address_ids = address_obj.search([('email', '=', email)])
                if address_ids:
                    addresses = address_obj.read(address_ids, ['email'])
                    corrected_ids = []
                    for addr in addresses:
                        if addr['email'] == email:  # we check for the exact correspondance because the search does an 'ilike' !
                            corrected_ids.append(addr['id'])
                    if corrected_ids:
                        corrected_ids.write({'email':False})
                        final_count += len(corrected_ids)
                        if not found:
                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n>%s<' % email)
                            found = True
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n - Address_ids : %s' % ','.join([str(x) for x in corrected_ids]))
                job_ids = job_obj.search([('email', '=', email)])
                if job_ids:
                    job_ids.read(['email'])
                    corrected_ids = []
                    for job in jobs:
                        if job['email'] == email:  # we check for the exact correspondance because the search does an 'ilike' !
                            corrected_ids.append(job['id'])
                    if corrected_ids:
                        corrected_ids.write({'email':False})
                        final_count += len(corrected_ids)
                        if not found:
                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n>%s<' % email)
                            found = True
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n - Job_ids : %s' % ','.join([str(x) for x in corrected_ids]))
                contact_ids = contact_obj.search([('email', '=', email)])
                if contact_ids:
                    contacts = contact_ids.read(['email'])
                    corrected_ids = []
                    for cont in contacts:
                        if cont['email'] == email:  # we check for the exact correspondance because the search does an 'ilike' !
                            corrected_ids.append(cont['id'])
                    if corrected_ids:
                        corrected_ids.write({'email':False})
                        final_count += len(corrected_ids)
                        if not found:
                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n>%s<' % email)
                            found = True
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n - Contacts_ids : %s' % ','.join([str(x) for x in corrected_ids]))
                subscriber_ids = subscriber_obj.search([('email', '=', email)])
                if subscriber_ids:
                    subscribers = subscriber_obj.browse(subscriber_ids)
                    corrected_ids = []
                    for subs in subscribers:
                        if subs.email == email:  # we check for the exact correspondance because the search does an 'ilike' !
                            corrected_ids.append(subs['id'])
                            if subs.source_id.followup_email and dResponsibles.has_key(subs.source_id.followup_email):
                                dResponsibles[subs.source_id.followup_email].append(email)
                    if corrected_ids:
                        subscriber_obj.write(corrected_ids, {'active':False, 'expire':today, 'comments':subs.comments and subs.comments + '\n\nHard-Bounce dans MailChimp' or 'Hard-Bounce dans Mailchimp'})
                        final_count += len(corrected_ids)
                        if not found:
                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n>%s<' % email)
                            found = True
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n - Subscriber_ids : %s' % ','.join([str(x) for x in corrected_ids]))
        # sending a report to responsibles of data sources if any corrections made on the subscribers'lists
        if send2responsibles:
            for (email, corrections) in dResponsibles.items():
                if email and corrections:
                    content = u"""<html><body><p>Voici les adresses email du jour ayant été effacées de la liste de diffusion de la Revue de Presse.</p>
                    <p>Elles ont été effacées parce que le serveur email ne répond pas durant un laps de temps certain ou parce qu'il répnd que l'adresse n'est plus correcte.<br/>
                    Merci de mettre à jour vos tables internes pour ne plus proposer d'envois vers cette adresse lors de votre prochaines mises à jour.</p>
                    <p>%s</p>
                    </body></html>
                    """ % '\n'.join(['%s<br/>\n' % x for x in corrections])
                    tools.email_send('info@ccilvn.be', [email], 'Hard Bounces du Jour', content, subtype='html')
        final_result = True
        self.env['cci_logs.cron_line']._stop(cronline_id, final_result, '\n---end---')
        return final_count
    
    @api.model
    def unsubscribe_email(self, emails_list, list_name, send2responsibles=False):
        # start log
        cronline_id = self.env['cci_logs.cron_line']._start('MailsUnsubscribe')
        final_result = False
        final_count = 0
        if emails_list:
            # create the list of source->responsible_email
            today = datetime.datetime.today().strftime('%Y-%m-%d')
            source_obj = self.env['cci_newsletter.source']
            source_ids = source_obj.search([])
            sources = source_obj.read(source_ids, ['name', 'followup_email'])
            dResponsibles = {}
            for source in sources:
                if source['followup_email']:
                    dResponsibles[source['followup_email']] = []
            self.env['cci_logs.cron_line']._addComment(cronline_id, 'Responsible emails for source follow-up : %s' % str(len(dResponsibles)))
            address_obj = self.env['res.partner']
            job_obj = self.env['res.partner']
            contact_obj = self.env['res.partner']
            subscriber_obj = self.env['cci_newsletter.subscriber']
            for email in emails_list:
                # We search for it on res.partner.contact and cci_newsletter.subscriber
                # If found on subscriber, warn by email the concerned follow-up responsible
                found = False
                # Caution : if we found the email on a job, we unsubscribe the linked contact if no email or same email on contact, else we don't unsubscribe this
                job_ids = job_obj.search([('email', '=', email)])
                if job_ids:
                    jobs = job_obj.browse(job_ids)
                    corrected_ids = []
                    for job in jobs:
                        if job.email == email and job.contact_id and job.contact_id.id not in corrected_ids:  # we check for the exact correspondance because the search does an 'ilike' !
                            if not job.contact_id.email or job.contact_id.email == email:
                                corrected_ids.append(job.contact_id.id)
                    if corrected_ids:
                        field_name = list_name + '_subscribe'
                        corrected_ids.write({field_name:'unsubscribed'})
                        final_count += len(corrected_ids)
                        if not found:
                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n>%s<' % email)
                            found = True
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n - Job_ids : %s' % ','.join([str(x) for x in corrected_ids]))
                contact_ids = contact_obj.search([('email', '=', email)])
                if contact_ids:
                    contacts = contact_ids.read(['email'])
                    corrected_ids = []
                    for cont in contacts:
                        if cont['email'] == email:  # we check for the exact correspondance because the search does an 'ilike' !
                            corrected_ids.append(cont['id'])
                    if corrected_ids:
                        field_name = list_name + '_subscribe'
                        corrected_ids.write({field_name:'unsubscribed'})
                        final_count += len(corrected_ids)
                        if not found:
                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n>%s<' % email)
                            found = True
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n - Contacts_ids : %s' % ','.join([str(x) for x in corrected_ids]))
                subscriber_ids = subscriber_obj.search([('email', '=', email)])
                if subscriber_ids and list_name == 'rdp':
                    subscribers = subscriber_obj.browse(subscriber_ids)
                    corrected_ids = []
                    for subs in subscribers:
                        if subs.email == email:  # we check for the exact correspondance because the search does an 'ilike' !
                            corrected_ids.append(subs['id'])
                            if subs.source_id.followup_email and dResponsibles.has_key(subs.source_id.followup_email):
                                dResponsibles[subs.source_id.followup_email].append(email)
                    if corrected_ids:
                        subscriber_obj.write(corrected_ids, {'active':False, 'expire':today, 'comments':subs.comments and subs.comments + '\n\nUnsubscribed dans MailChimp' or 'Unsubscribed dans Mailchimp'})
                        final_count += len(corrected_ids)
                        if not found:
                            self.env['cci_logs.cron_line']._addComment(cronline_id, '\n>%s<' % email)
                            found = True
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n - Subscriber_ids : %s' % ','.join([str(x) for x in corrected_ids]))
        # sending a report to responsibles of data sources if any corrections made on the subscribers'lists
        if send2responsibles:
            for (email, corrections) in dResponsibles.items():
                if email and corrections:
                    content = u"""<html><body><p>Voici les adresses email du jour ayant été désinscrites de la liste de diffusion de la Revue de Presse.</p>
                    <p>Elles ont été désinscrites parce que l'utlisateur s'est désinscrit via l'interface de MailChimp.<br/>
                    Merci de mettre à jour vos tables internes pour ne plus proposer d'envois vers cette adresse lors de votre prochaines mises à jour.</p>
                    <p>%s</p>
                    </body></html>
                    """ % '\n'.join(['%s<br/>\n' % x for x in corrections])
                    tools.email_send('info@ccilvn.be', [email], 'Mails Désinscrits du Jour', content, subtype='html')
        final_result = True
        self.env['cci_logs.cron_line']._stop(cronline_id, final_result, '\n---end---')
        return final_count
    
    @api.model
    def _correct_rdp_for_self_subscribers(self, lists2correct=[]):
        # start log
        cronline_id = self.env['cci_logs.cron_line']._start('CorrectRDPSelfSubscribers')
        final_result = True
        #
        # We get the API key
        parameter_obj = self.env['cci_parameters.cci_value']
        param_values = parameter_obj.get_value_from_names(['MailChimpAPIKey'])
        if param_values.has_key('MailChimpAPIKey'):
            if lists2correct:
                mailchimp_server = mailchimp.Mailchimp(param_values['MailChimpAPIKey'], False)
                mailchimp_lists = mailchimp.Lists(mailchimp_server)
                for list2corr in lists2correct:
                    self.env['cci_logs.cron_line']._addComment(cronline_id, '\n\nCorrect List : %s [%s] set RDP values to "%s"' % (list2corr['name'], list2corr['id'], list2corr['rdp_value']))
                    mailchimp_list_id = list2corr['id']
                    result = mailchimp_lists.members(mailchimp_list_id)
                    total = result['total']
                    page = 0
                    to_correct = []
                    while total > 0:
                        result = mailchimp_lists.members(mailchimp_list_id, 'subscribed', {'start':page})  # if you don't give the 'subscribed' status, you get always the same page !!!
                        page += 1
                        total = total - len(result['data'])
                        for member in result['data']:
                            if member['ip_signup'] and member['merges']['RDP'] != 'vlanderen':
                                to_correct.append(member['email'])
                    if to_correct:
                        corrections = []
                        for email in to_correct:
                            corrections.append({'email':{'email':email}, 'merge_vars':{'RDP':list2corr['rdp_value']}})
                        result = mailchimp_lists.batch_subscribe(mailchimp_list_id, corrections, double_optin=False, update_existing=True, replace_interests=False)
                        self.env['cci_logs.cron_line']._addComment(cronline_id, '\n  new emails corrected :\n    -%s\n' % ('\n    -'.join(to_correct)))
        self.env['cci_logs.cron_line']._stop(cronline_id, final_result, '\n---end---')
        return True
