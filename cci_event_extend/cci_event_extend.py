# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from openerp import tools
import urllib
import urllib2
from lxml import etree
from lxml import objectify
import re        
import pymysql
import datetime
from openerp import models, fields, api, _

def correct_phone(string):
    if 'conf' not in string:
        result = string.replace(' ', '').replace('/', '').replace('.', '').replace('-', '').replace('+', '00')
    else:
        result = ''
    return result
    
class event(models.Model):
    _inherit = 'event.event'
    _name = 'event.event'
    _description = 'event.event'

    site_id = fields.Integer('ID on WebSite')

    @api.model
    def copy(self, default=None):
        if not default:
            default = {}
        default.update({
            'code': self.env['ir.sequence'].get('event.event'),
            'state': 'draft',
        })
        new_id = super(event, self).copy(default)
        new_id.write({'site_id':False})
        return new_id
    
    @api.model
    def _update_from_website(self, address):
        # address="http://www.ccilvn.be//feed?post_type=event"
        # Start log
        cronline_id = self.env['cci_logs.cron_line']._start('EventsUpdateFromSite')
        final_result = True
        try:
            request = urllib2.Request(address, headers={'User-Agent' : "Magic Browser"})
            atomDoc = urllib2.urlopen(request)
        except Exception, err:
            self.env['cci_logs.cron_line']._addComment(cronline_id, 'Erreur de lecture du flux - ' + str(err))
            final_result = False
        if final_result:
            analytic_default_obj = self.env['account.analytic.default']
            event_obj = self.env['event.event']
            parameter_obj = self.env['cci_parameters.cci_value']
            param_values = parameter_obj.get_value_from_names(['EventDefaultProductID', 'EventImportManagers'])
            if param_values.has_key('EventDefaultProductID'):
                default_product_id = param_values['EventDefaultProductID']
            else:
                default_product_id = 0
            if param_values.has_key('EventImportManagers'):
                email_managers = param_values['EventImportManagers']
            else:
                email_managers = []
            #
            xml_content = atomDoc.read()
            root = etree.XML(xml_content)
            for item in root.iter('item'):
                type_name = ''
                event_name = ''
                resp_email = ''
                date_debut = ''
                heure_debut = ''
                heure_fin = ''
                prix_membre = 0.0
                prix_nmembre = 0.0
                id_on_site = 0
                event_errors = []
                for element in item.iter():
                    if element.tag == 'produitRelatif':
                        type_name = element.text
                    elif element.tag == 'title':
                        event_name = element.text.strip()
                    elif element.tag == 'contactEmail':
                        resp_email = element.text.strip()
                    elif element.tag == 'id':
                        id_on_site = int(element.text)
                    elif element.tag == 'dateDebut':
                        date_debut = element.text
                    elif element.tag == 'heureDebut':
                        heure_debut = element.text
                    elif element.tag == 'heureFin':
                        heure_fin = element.text
                    elif element.tag == 'tarifMembres':
                        prix_membre = float(element.text)
                    elif element.tag == 'tarifNonMembres':
                        prix_nmembre = float(element.text)
                if event_name and date_debut and id_on_site:
                    event_data = {}
                    event_data['state'] = 'draft'
                    event_data['active'] = True
                    event_data['site_id'] = id_on_site
                    event_data['name_on_site'] = event_name
                    event_data['name'] = event_name  # # will be replaced if we found an event.type and this event.type has an name_template value
                    event_data['reply_to'] = resp_email
                    event_data['date_begin'] = date_debut[0:4] + '-' + date_debut[4:6] + '-' + date_debut[6:]
                    event_data['date_end'] = event_data['date_begin']
                    if heure_debut:
                        if 'h' in heure_debut.lower():
                            elements = heure_debut.lower().split('h')
                        else:
                            elements = heure_debut.split(':')
                        if len(elements) > 1:
                            event_data['date_begin'] += ' ' + elements[0].rjust(2, '0')[0:2] + ':' + elements[1].rjust(2, '0')[0:2] + ':00'
                        else:
                            event_data['date_begin'] += ' ' + elements[0].rjust(2, '0')[0:2] + ':00:00'
                    else:
                        event_data['date_begin'] += ' 00:00:00'
                    if heure_fin:
                        if 'h' in heure_fin.lower():
                            elements = heure_fin.lower().split('h')
                        else:
                            elements = heure_fin.split(':')
                        if len(elements) > 1:
                            event_data['date_end'] += ' ' + elements[0].rjust(2, '0')[0:2] + ':' + elements[1].rjust(2, '0')[0:2] + ':00'
                        else:
                            event_data['date_end'] += ' ' + elements[0].rjust(2, '0')[0:2] + ':00:00'
                    else:
                        event_data['date_end'] += ' 00:00:00'
                    # we check if this event already exists in the ERP, to not create product for an already created event
                    current_id = 0
                    event_ids = event_obj.search([('site_id', '=', id_on_site)])
                    if event_ids and len(event_ids) == 1:
                        current_id = event_ids[0]
                    if type_name and not current_id:
                        type_ids = self.env['event.type'].search([('name_on_site', '=', type_name)])
                        if type_ids:
                            event_type = self.env['event.type'].browse([type_ids[0]])[0]
                            if event_type.default_auto_register:
                                event_data['mail_auto_registr'] = event_type.default_auto_register
                            if event_type.default_msg_register:
                                event_data['mail_registr'] = event_type.default_msg_register
                            if event_type.default_auto_confirm:
                                event_data['mail_auto_confirm'] = event_type.default_auto_confirm
                            if event_type.default_msg_confirm:
                                event_data['mail_confirm'] = event_type.default_msg_confirm
                            if event_type.name_template:
                                event_data['name'] = event_type.name_template.replace('{PERSO Date}', date_debut).replace('{PERSO Nom}', event_name)
                            if event_type.product_id:
                                product_name = event_data['name']
                                if event_type.product_name_template:
                                    product_name = event_type.product_name_template.replace('{PERSO Date}', date_debut).replace('{PERSO Nom}', event_name).replace('{PERSO FRDate}', date_debut[6:8] + '/' + date_debut[4:6] + '/' + date_debut[0:4]).replace('{PERSO FRMois}', date_debut[6:8] + '/' + date_debut[4:6])
                                prod_obj = self.env['product.product']
                                new_product_id = prod_obj.copy(event_type.product_id.id, {'name':product_name, 'list_price':prix_nmembre, 'member_price':prix_membre})
                                prod_obj.write([new_product_id], {'name':product_name}, {'lang':'de_DE'})
                                prod_obj.write([new_product_id], {'name':product_name}, {'lang':'nl_NL'})
                                prod_obj.write([new_product_id], {'name':product_name}, {'lang':'fr_FR'})
                                prod_obj.write([new_product_id], {'name':product_name}, {'lang':'fr_BE'})
                                event_data['product_id'] = new_product_id
                                # copy also the account.analytic.default linked to the original product
                                adef_ids = analytic_default_obj.search([('product_id', '=', event_type.product_id.id)])
                                if adef_ids:
                                    if len(adef_ids) > 1:
                                        event_errors.append(_(u'The product linked to the type of event has more than one analytic default value => only the first one has been used.'))
                                    analytic_default_obj.copy(adef_ids[0], {'product_id':new_product_id})
                                else:
                                    event_errors.append(_(u'The product linked to the type of event has no analytic default.'))
                            event_data['type'] = event_type.id
                    else:
                        if not current_id:
                            event_errors.append(_(u'Not possible to find the type of event => no default values for this event.'))
                            self.env['cci_logs.cron_line']._addComment(cronline_id, _(u'\nPas possible de retrouver le type de l\'event \'%s\' [%s]') % (event_name, str(id_on_site)))
                            final_result = False
                    if resp_email and event_data['date_begin'] > datetime.datetime.today().strftime('%Y-%m-%d'):
                        user_ids = self.env['res.users'].search([('email', '=', resp_email)])
                        if user_ids:
                            event_data['user_id'] = user_ids[0]
                        else:
                            self.env['cci_logs.cron_line']._addComment(cronline_id, _(u'\nPas possible de retrouver le responsable de l\'event \'%s\' [%s]') % (event_name, str(id_on_site)))
                            final_result = False
                    self.env['cci_logs.cron_line']._addComment(cronline_id, _(u'\n---------------\nEvent [%s] "%s" sur site - ERP [%s]') % (str(id_on_site), event_name, str(current_id)))
                    if current_id:
                        # this event is already in the ERP => just check if data have changed on site
                        event = event_obj.browse([current_id])[0]
                        if event_data.has_key('reply_to') and event_data['reply_to'] and event_data['reply_to'] != event.reply_to:
                            event_errors.append(_(u'Modified Reply To ? %s on site -> %s in OpenERP') % (event_data['reply_to'], event.reply_to or ''))
                        if event_data.has_key('date_begin') and event_data['date_begin'] != event.date_begin:
                            event_errors.append(_(u'Modified Date Begin ? %s on site -> %s in OpenERP') % (event_data['date_begin'], event.date_begin or ''))
                        if event_data.has_key('date_end') and event_data['date_end'] != event.date_end:
                            event_errors.append(_(u'Modified Date End ? %s on site -> %s in OpenERP') % (event_data['date_end'], event.date_end or ''))
                    else:
                        if not event_data.has_key('product_id') and default_product_id:
                            new_product_id = self.env['product.product'].copy(default_product_id, {'name':event_data['name'], 'list_price':prix_nmembre, 'member_price':prix_membre})
                            event_data['product_id'] = new_product_id
                            # copy also the account.analytic.default linked to the original product
                            adef_ids = analytic_default_obj.search([('product_id', '=', default_product_id)])
                            if adef_ids:
                                if len(adef_ids) > 1:
                                    event_errors.append(_(u'The product linked to the type of event has more than one analytic default value => only the first one has been used.'))
                                analytic_default_obj.copy(adef_ids[0], {'product_id':new_product_id})
                            else:
                                event_errors.append(_(u'The product linked to the type of event has no analytic default.'))
                        if event_data.has_key('product_id'):
                            # create this event in the ERP
                            self.pool.get('event.event').create(event_data)
                        else:
                            event_errors.append(_(u'no creation because no product id'))
                    if event_errors:
                        # there is some errors on the current event => sending an warning email to DefaultManagers and current event's responsible
                        email_title = _(u"Warning ! Import Event '%s' from WebSite [%s]") % (event_name, str(id_on_site))
                        email_content = _(u'<html><body>This event has some possible problems to check ASAP :<ul><li>%s</li></ul></body></html>') % '</li><li>'.join(event_errors)
                        email_dest = [x for x in email_managers]
                        if resp_email and resp_email not in email_dest:
                            email_dest.append(resp_email)
                        if email_dest:
                            tools.email_send(email_dest[0], email_dest, email_title, email_content, subtype='html')
                            # tools.email_send('philmer@ccilvn.be', ['philmer.vdm@gmail.com',], email_title, email_content, subtype='html')
                else:
                    self.pool.get('cci_logs.cron_line')._addComment(cronline_id, _(u'\nPas assez de données pour créer l\'event \'%s\' [%s]') % (event_name, str(id_on_site)))
                    final_result = False
        self.env['cci_logs.cron_line']._addComment(cronline_id, _('\n\n----------\nOriginal content:\n'))
        self.env['cci_logs.cron_line']._addComment(cronline_id, xml_content.decode('utf-8'))
        self.env['cci_logs.cron_line']._stop(cronline_id, final_result, '\n---end---')
        return True
    
    @api.model
    def convert_old_sector_ids_to_new_ids(self, dSectCode2ID):
        dResult = {}
        parameter_obj = self.env['cci_parameters.cci_value']
        param_values = parameter_obj.get_value_from_names(['ActivityCodeRootID'])
        if param_values.has_key('ActivityCodeRootID'):
            activityCodeRootID = param_values['ActivityCodeRootID']
            obj_categ = self.env['res.partner.category']
            old_len = 0
            categ_ids = [ activityCodeRootID ]
            while len(categ_ids) > old_len:
                new_ids = categ_ids[old_len:]  # ids of categories added last time
                old_len = len(categ_ids)  # the new frontier ...
                new_categs = obj_categ.read(cr, uid, new_ids, ['child_ids'])
                for categ in new_categs:
                    if categ['child_ids']:
                        categ_ids.extend(categ['child_ids'])
            categs = obj_categ.read(cr, uid, categ_ids, ['name'], {'lang':'fr_FR'})
            dCategs = {}
            for categ in categs:
                formated_name = categ['name']
                posA = formated_name.rfind('[')
                posB = formated_name.rfind(']')
                if posA >= 0 and posB > 0 and posA < posB:
                    code = formated_name[posA + 1:posB]
                    if dSectCode2ID.has_key(code):
                        dResult[categ['id']] = dSectCode2ID[code]
        return (dResult, categ_ids)
    
    
    def _export_popup(self):
        # Start log
        cronline_id = self.pool.get('cci_logs.cron_line')._start(cr, uid, 'PopupExport')
        final_result = True
        test = False
        parameter_obj = self.pool.get('cci_parameters.cci_value')
        param_values = parameter_obj.get_value_from_names(cr, uid, ['PopupEventsList', 'PopupExportSupervisors', 'PopupConnectionDict', 'CompanyFacebookURL', 'CompanyLinkedInURL', 'CompanyTwitterURL', 'PopupTest'])
        if param_values.has_key('PopupEventsList') and param_values.has_key('PopupExportSupervisors') and param_values.has_key('PopupConnectionDict'):
            events = param_values['PopupEventsList']  # ((154,1,2,4,0),(155,3,0,0),(156,2,3,10)) for example with 154 = event_id and 1 = type_stand in stand; 2 = max_part_expor for this type of stand; 4 = max_part_invit for this type of stand; 0 = screen (if 1) or not
            supervisor_emails = param_values['PopupExportSupervisors']  # list of emails
            connection = param_values['PopupConnectionDict']
            if param_values.has_key('CompanyFacebookURL'):
                question_fb_id = param_values['CompanyFacebookURL']
            else:
                question_fb_id = False
                self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nATTENTION pas de question ID sur Facebook définie')
            if param_values.has_key('CompanyLinkedInURL'):
                question_li_id = param_values['CompanyLinkedInURL']
            else:
                question_li_id = False
                self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nATTENTION pas de question ID sur LinkedIn définie')
            if param_values.has_key('CompanyTwitterURL'):
                question_tw_id = param_values['CompanyTwitterURL']
            else:
                question_tw_id = False
                self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nATTENTION pas de question ID sur Twitter définie')
            if param_values.has_key('PopupTest'):
                test = param_values['PopupTest']
            nom_table_secteur = test and 'secteurs_test' or 'secteurs'
            nom_table_stand = test and 'stand_test' or 'stand'
            #
            function_categs = [('G', u'DIRECTION GÉNÉRALE'), ('$', u'DIRECTION GÉNÉRALE'), ('K', u'DIRECTION'), ('D', u'DIRECTION'),
                               ('B', u'ADMINISTRATIF ET FINANCIER'), ('F', u'ADMINISTRATIF ET FINANCIER'), ('J', u'ADMINISTRATIF ET FINANCIER'),
                               ('A', u'ACHAT'), ('M', u'MARKETING ET COMMERCIAL'), ('C', u'MARKETING ET COMMERCIAL'),
                               ('U', u'COMMUNICATION'), ('P', u'COMMUNICATION'), ('R', u'COMMUNICATION'), ('E', u'RH'),
                               ('I', u'IT'), ('O', u'TECHNIQUE'), ('Q', u'TECHNIQUE'), ('T', u'TECHNIQUE'),
                               ('S', u'SECRETARIAT'), ('Z', u'LOGISTIQUE')]
            undefined_categ = u'Autres'
            # Connection to the external db
            try:
                con = pymysql.connect(host=connection['host'], port=connection['port'], user=connection['user'], passwd=connection['pw'], db=connection['db']);
                cur = con.cursor()
            except pymysql.err.Error, e:
                self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, 'Connection Error %d: %s' % (e.args[0], e.args[1]))
                final_result = False
                if cur:
                    cur.close()
                if con:
                    con.close()
            if final_result:
                changes = False
                email_problems = []
                # 1. Synchronise the secteur table and keep mysql-ids
                sector_obj = self.pool.get('res.partner.activsector')
                sector_ids = sector_obj.search(cr, uid, [])
                sectors = sector_obj.read(cr, uid, sector_ids, ['id', 'name', 'code'], {'lang':'fr_FR'})
                try:
                    sentence = "SELECT code, denomination, id FROM `%s`" % nom_table_secteur
                    cur.execute(sentence)
                except pymysql.err.Error, e:
                    self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, 'Connection Error %d: %s' % (e.args[0], e.args[1]))
                    final_result = False
                data = cur.fetchall()
                dSectors = {}
                dSectCode2ID = {}  # usefull to res.partner.category->id to res.partner.activsector->id
                for line in data:
                    dSectors[line[0]] = {'id':line[2], 'denomination':line[1]}
                    dSectCode2ID[line[0]] = line[2]
                # Table to convert res.partner.category->id to res.partner.activsector->id
                (dOldSect2New, old_categ_ids) = self.convert_old_sector_ids_to_new_ids(cr, uid, dSectCode2ID)  # table to convert id from res.partner_category to id in res.partner.activsector AND list of valid res.partner.category ids
                #
                dSectID_ERP_MYSQL = {}
                dSectCode_MYSQL = {}
                for sector in sectors:
                    if not dSectors.has_key(sector['code']):
                        sentence = "INSERT INTO `%s` ( code, denomination ) VALUES ( '%s', '%s')" % (nom_table_secteur, sector['code'], sector['name'].replace("'", "''").replace("\\", "\\\\"))
                        cur.execute(sentence)
                        new_id = cur.lastrowid
                        if new_id > 0:
                            changes = True
                            self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nInsertion du secteur %s reussie -> %s' % (str(sector['id']), str(new_id)))
                            dSectID_ERP_MYSQL[sector['id']] = new_id
                        else:
                            self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nInsertion du secteur %s ratee' % str(sector['id']))
                    else:
                        dSectID_ERP_MYSQL[sector['id']] = dSectors[sector['code']]['id']
                        if dSectors[sector['code']]['denomination'].decode('iso-8859-1') != sector['name']:
                            sentence = u"UPDATE `%s` SET denomination = '%s' WHERE code = '%s'" % (nom_table_secteur, sector['name'].replace("'", "''").replace("\\", "\\\\"), sector['code'])
                            cur.execute(sentence)
                            changes = True
                            # self.pool.get('cci_logs.cron_line')._addComment(cr,uid,cronline_id,'\nMise à jour du secteur [%s] reussie -> %s' % (str(dSectors[sector['code']]['id']),sector['name']) )
                if cur:
                    con.commit()
                    cur.close()
                # 2. Synchronise to MYSQL the events definies as popup recordings
                # TEMP
                # updates = []
                mySQL_reg_ids = []
                cur = con.cursor()
                try:
                    sentence = "SELECT id_stand, erp_reg_id FROM `%s`" % nom_table_stand
                    cur.execute(sentence)
                except pymysql.err.Error, e:
                    self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, 'Connection Error %d: %s' % (e.args[0], e.args[1]))
                    final_result = False
                data = cur.fetchall()
                dExistingStands = {}
                for line in data:
                    dExistingStands[line[1]] = line[0]
                    if line[1] and line[1] > 0:
                        mySQL_reg_ids.append(line[1])
                reg_obj = self.pool.get('event.registration')
                current_registration_ids = []
                for concerned_event in events:
                    event_id = concerned_event[0]
                    type_stand = concerned_event[1]
                    default_max_part_expo = concerned_event[2]
                    default_max_part_invit = concerned_event[3]
                    default_screen = concerned_event[4]
                    reg_ids = reg_obj.search(cr, uid, [('event_id', '=', event_id), ('state', 'in', ['open', 'done'])])
                    if reg_ids:
                        current_registration_ids.extend(reg_ids)
                        regs = reg_obj.browse(cr, uid, reg_ids, {'lang':'fr_FR'})
                        for reg in regs:
                            if not dExistingStands.has_key(reg.id):
                                # new registration to insert into mysql
                                if reg.contact_id and reg.partner_id:
                                    # search for the address and the job that links the reg.partner_id and reg.contact_id
                                    job = False
                                    current_sequence_contact = 999
                                    if reg.contact_id.job_ids:
                                        for possible_job in reg.contact_id.job_ids:
                                            if possible_job.address_id and possible_job.address_id.partner_id and possible_job.address_id.partner_id.id == reg.partner_id.id:
                                                if possible_job.sequence_contact < current_sequence_contact:
                                                    job = possible_job
                                    if job:
                                        address = job.address_id
                                        partner = address.partner_id
                                        contact = reg.contact_id
                                        if reg.badge_partner:
                                            partner_full_name = reg.badge_partner
                                        else:
                                            if address.name:
                                                if address.name[0:3] == ' - ':
                                                    partner_full_name = partner.name + address.name
                                                elif address.name[0:2] == '- ':
                                                    partner_full_name = partner.name + ' ' + address.name
                                                else:
                                                    partner_full_name = address.name
                                            else:
                                                partner_full_name = partner.name
                                        addr_fb = ''
                                        if question_fb_id:
                                            for answer in partner.answers_ids:
                                                if answer.question_id.id == question_fb_id:
                                                    addr_fb = answer.text or ''
                                        addr_li = ''
                                        if question_li_id:
                                            for answer in partner.answers_ids:
                                                if answer.question_id.id == question_li_id:
                                                    addr_li = answer.text or ''
                                        addr_tw = ''
                                        if question_tw_id:
                                            for answer in partner.answers_ids:
                                                if answer.question_id.id == question_tw_id:
                                                    addr_tw = answer.text or ''
                                        sector1 = 0
                                        sector2 = 0
                                        sector3 = 0
                                        if address.sector1:
                                            # we take the sectors from the address
                                            if dSectID_ERP_MYSQL.has_key(address.sector1.id):
                                                sector1 = dSectID_ERP_MYSQL[address.sector1.id]
                                            if address.sector2 and dSectID_ERP_MYSQL.has_key(address.sector2.id):
                                                sector2 = dSectID_ERP_MYSQL[address.sector2.id]
                                            if address.sector3 and dSectID_ERP_MYSQL.has_key(address.sector3.id):
                                                sector3 = dSectID_ERP_MYSQL[address.sector3.id]
                                        else:
                                            # we get them from the partner's categories
                                            new_sector_ids = []
                                            for category in partner.category_id:
                                                categ_id = category.id
                                                if categ_id in old_categ_ids and dOldSect2New.has_key(categ_id):
                                                    new_sector_ids.append(dOldSect2New[categ_id])
                                            if len(new_sector_ids) > 0:
                                                sector1 = new_sector_ids[0]
                                                if len(new_sector_ids) > 1:
                                                    sector2 = new_sector_ids[1]
                                                    if len(new_sector_ids) > 2:
                                                        sector3 = new_sector_ids[2]
                                        zip_code = address.zip_id and address.zip_id.name or ''
                                        if len(zip_code) > 12:
                                            zip_code = '0'
                                        user_phone = ''
                                        user_mobile = ''
                                        if job.phone and not 'conf' in job.phone:
                                            user_phone = job.phone
                                        if contact.mobile and not 'conf' in contact.mobile:
                                            user_mobile = contact.mobile
                                        function_categ = ''
                                        this_job_code_labels = (job.function_code_label or '')
                                        for (letter, fcateg) in function_categs:
                                            if letter in this_job_code_labels:
                                                function_categ = fcateg
                                                break
                                        if not function_categ:
                                            function_categ = undefined_categ
                                        sentence = """INSERT INTO `%s` ( user_level, user_mail, user_mdp, user_civ, user_nom, user_prenom, user_fonction, user_fonction_plus, user_tel, user_gsm, 
                                                          part_tva, part_nom, part_adresse, part_adresse_plus, part_adresse_cp, part_adresse_loca, part_adresse_pays, part_tel, part_email, 
                                                          part_site, part_linkedin, part_facebook, part_twitter, part_description, part_logo, part_s1, part_s2, part_s3, erp_partner_id, erp_reg_id, erp_type_stand, erp_adresse_id, 
                                                          erp_effectif_tot, max_part_expo, max_part_invit, last_action, stand_pos1, stand_pos2, stand_pos3, actif, screen ) 
                                                      VALUES ( 0, '%s', '', '%s', '%s', '%s', '%s', '%s', '%s', '%s',
                                                               '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s',
                                                               '%s', '%s', '%s', '%s', '%s', '%s', %i, %i, %i, %i, %i, %i, %i, 
                                                               %s, %i, %i, 0, '', '', '', 0, %i )""" % (nom_table_stand,
                                                                                     reg.email_from or '',
                                                                                     (contact.title or '').replace("'", "''").replace("\\", "\\\\"),
                                                                                     (contact.name or '').replace("'", "''").replace("\\", "\\\\"),
                                                                                     (contact.first_name or '').replace("'", "''").replace("\\", "\\\\"),
                                                                                     (function_categ).replace("'", "''").replace("\\", "\\\\"),
                                                                                     (reg.badge_title or job.function_label or '').replace("'", "''").replace("\\", "\\\\"),
                                                                                     user_phone,
                                                                                     user_mobile,
                                                                                     partner.vat or '',
                                                                                     (partner_full_name).replace("'", "''").replace("\\", "\\\\"),
                                                                                     (address.street or '').replace("'", "''").replace("\\", "\\\\"),
                                                                                     (address.street2 or '').replace("'", "''").replace("\\", "\\\\"),
                                                                                     zip_code,
                                                                                     (address.zip_id and address.zip_id.city or '').replace("'", "''").replace("\\", "\\\\"),
                                                                                     (address.country_id and address.country_id.name or 'Belgique'),
                                                                                     (correct_phone(address.phone or '')).replace("'", "''").replace("\\", "\\\\"),
                                                                                     (address.email or '').replace("'", "''").replace("\\", "\\\\"),
                                                                                     (partner.website or '').replace("'", "''").replace("\\", "\\\\"),
                                                                                     (addr_li).replace("'", "''").replace("\\", "\\\\"),
                                                                                     (addr_fb).replace("'", "''").replace("\\", "\\\\"),
                                                                                     (addr_tw).replace("'", "''").replace("\\", "\\\\"),
                                                                                     (address.activity_description or partner.activity_description or '').replace(u"’", "'").replace("'", "''").replace("\\", "\\\\"),
                                                                                     '',
                                                                                     sector1,
                                                                                     sector2,
                                                                                     sector3,
                                                                                     partner.id,
                                                                                     reg.id,
                                                                                     type_stand,
                                                                                     address.id,
                                                                                     str(partner.employee_nbr_total or 0),
                                                                                     default_max_part_expo,
                                                                                     default_max_part_invit,
                                                                                     default_screen)
                                        # TEMP only one time to updates 'gsm' fields forgotten in the first sending and not detected in first reviews from LK et VM
                                        # if contact.mobile and test:
                                        #    update_sentence = "UPDATE stand SET gsm = '%s' where erp_reg_id = %s;\n" % (contact.mobile,reg.id)
                                        #    print 'update_sentence'
                                        #    print update_sentence
                                        #    updates.append(update_sentence)
                                        try:
                                            cur.execute(sentence)
                                            changes = True
                                        except pymysql.err.Error, e:
                                            self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nConnection Error %d: %s' % (e.args[0], e.args[1]))
                                            self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\n' + sentence)
                                            final_result = False
                                        new_id = cur.lastrowid
                                        if new_id > 0:
                                            self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nInsertion inscription [%s] reussie -> %s' % (str(reg.id), str(new_id)))
                                        else:
                                            self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nInsertion inscription [%s] ratee' % str(reg.id))
                                            email_problems.append('<li>Insertion inscription [%s] echoue dans MySQL.</li>' % str(reg.id))
                                    else:
                                        self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nRegistration [%s] impossible to send to Mysql : no link between contact and partner' % str(reg.id))
                                        email_problems.append('<li>Impossible d\'envoyer l\'inscrit [%s] dans Mysql : pas de lien entre le partenaire et le contact.</li>' % str(reg.id))
                                else:
                                    self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nRegistration [%s] impossible to send to Mysql : no partner or no contact' % str(reg.id))
                                    email_problems.append('<li>Impossible d\'envoyer l\'inscrit [%s] dans Mysql : le partenaire ou le contact manque.</li>' % str(reg.id))
                            else:
                                self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nRegistration [%s] already existing' % str(reg.id))
                # end
                # final_result = test
                # TEMP
                # if test:
                #    output = open('updates_mobile.txt','w')
                #    output.writelines(updates)
                #    output.close()
                #
                if final_result and changes:
                    con.commit()
                if cur:
                    cur.close()
                if con:
                    con.close()
                # check if deleted or canceled registrations not still in MySQL
                for mySQL_id in mySQL_reg_ids:
                    if mySQL_id not in current_registration_ids:
                        self.pool.get('cci_logs.cron_line')._addComment(cr, uid, cronline_id, '\nRegistration ID [%s] still existing in MySQL while erased or canceled in ERP' % str(mySQL_id))
                        email_problems.append('<li>L\'inscription ID [%s] existe encore dans MySQL alors qu\'elle a ete effacee .</li>' % str(mySQL_id))
                # envoi de l'email au superviseur
                if email_problems and supervisor_emails:
                    if test:
                        supervisor_emails = ['philmer.vdm@gmail.com']
                    tools.email_send('noreply@ccilvn.be',
                                     supervisor_emails,
                                     u'Mise à jour exposants Pop Up',
                                     u'<p>La mise à jour de ce matin a eu quelques problèmes :</p><p><ul>%s</ul></p>' % ('\n'.join(email_problems)),
                                     subtype='html')
        else:
            self.env['cci_logs.cron_line']._addComment(cr, uid, cronline_id, '\nNothing done - some parameters were missing')
            final_result = False
        self.env['cci_logs.cron_line']._stop(cr, uid, cronline_id, final_result, '\n---end---')
        return True
    
class event_type(models.Model):
    _inherit = 'event.type'
    _description = 'Event type'

    product_id = fields.Many2one('product.product', 'Default Product', help='This product will be used as template for creating a precise product linked only to each event of this type')
    user_id = fields.Many2one('res.users', 'Default Responsible', help='The events of this type will be linked to this user when we can\'t find any user from the website user name.')
    name_template = fields.Char('Name Template', size=120, help='String with {PERSO Date} or {PERSO Nom} available to auto-format the event name')
    product_name_template = fields.Char('Product Name Template', size=120, help='String with {PERSO Date}, {PERSO Nom}, {PERSO FRDate} or {PERSO FRMois} available to auto-format the product name')
    name_on_site = fields.Char('Name on Site', size=50, help='Name of this type of events as defined on the side of the website to do the link')
    default_auto_register = fields.Boolean('Mail Auto Register', help='Check this box if you want to use the automatic mailing for new registration')
    default_auto_confirm = fields.Boolean('Mail Auto Confirm', help='Check this box if you want to use the automatic confirmation emailing or the reminder')
    default_msg_register = fields.Text('Registration Email', help='This email will be sent when someone subscribes to the event.')
    default_msg_confirm = fields.Text('Confirmation Email', help="This email will be sent when the event gets confirmed or when someone subscribes to a confirmed event.")
    active = fields.Boolean('Active', defalt=True)

class event_registration(models.Model):
    _inherit = 'event.registration'
    _description = "event.registration"
    
    @api.model
    def personalize_text(self, tags, text, reg):
        ''' This method replace tags with content from registration browse object
            to personalize the mail sended to the registrated contacts
        '''
        for tag in tags.findall(text):
            tag_name = str(tag)
            if tag_name == '{PERSO nom_event}':
                text = text.replace(tag_name, reg.event_id.name)
            elif tag_name == '{PERSO nom_badge}':
                text = text.replace(tag_name, reg.badge_name or '')
            elif tag_name == '{PERSO partenaire_badge}':
                text = text.replace(tag_name, reg.badge_partner or '')
            elif tag_name == '{PERSO titre_badge}':
                text = text.replace(tag_name, reg.badge_title or '')
            elif tag_name == '{PERSO cnp_inscrit}':
                text = text.replace(tag_name, ((reg.contact_id.title or '') + ' ' + reg.contact_id.name + ' ' + (reg.contact_id.first_name or '')).strip())
            elif tag_name == '{PERSO cpn_inscrit}':
                text = text.replace(tag_name, ((reg.contact_id.title or '') + ' ' + (reg.contact_id.first_name or '') + ' ' + reg.contact_id.name).strip().replace('  ', ' '))
            elif tag_name == '{PERSO pn_inscrit}':
                text = text.replace(tag_name, ((reg.contact_id.first_name or '') + ' ' + reg.contact_id.name).strip())
            elif tag_name == '{PERSO np_inscrit}':
                text = text.replace(tag_name, (reg.contact_id.name + ' ' + (reg.contact_id.first_name or '')).strip())
            elif tag_name == '{PERSO n_inscrit}':
                text = text.replace(tag_name, (reg.contact_id.name).strip())
            elif tag_name == '{PERSO p_inscrit}':
                text = text.replace(tag_name, (reg.contact_id.first_name or '').strip())
            elif tag_name == '{PERSO cn_inscrit}':
                text = text.replace(tag_name, ((reg.contact_id.title or '') + ' ' + reg.contact_id.name).strip())
            elif tag_name == '{PERSO nomfact}':
                if reg.unit_price > 0.001:
                    value = u'<p>Aucune adresse de facturation définie</p>'
                    if reg.partner_invoice_id:
                        # search of the first 'invoice' address, else first 'default' address
                        if reg.partner_invoice_id.address:
                            good_address = False
                            for address in reg.partner_invoice_id.address:
                                if address.type == 'invoice':
                                    good_address = address
                                    break
                            if not good_address:
                                for address in reg.partner_invoice_id.address:
                                    if address.type == 'default':
                                        good_address = address
                                        break
                        if good_address:
                            value = u'<p>Sans contre avis de votre part, votre participation sera facturée à : '
                            if good_address.name:
                                if good_address.name[0:2] == '- ' or good_address.name[0:3] == ' - ':
                                    value += (reg.partner_invoice_id.name + ' ' + good_address.name.lstrip())
                                else:
                                    value += good_address.name
                            else:
                                value += reg.partner_invoice_id.name
                            value += ', ' + (good_address.street or '')
                            if good_address.street2:
                                value += (u' - ' + good_address.street2)
                            if good_address.zip_id:
                                value += (u', ' + good_address.zip_id.name + ' ' + good_address.zip_id.city)
                            elif good_address.zip:
                                value += (u', ' + good_address.zip + ' ' + good_address.city)
                            if not reg.partner_invoice_id.vat_subjected:
                                value += u', TVA : Non assujetti'
                            else:
                                if reg.partner_invoice_id.vat:
                                    value += (u', TVA : ' + reg.partner_invoice_id.vat)
                                else:
                                    value += u', TVA : inconnue'
                            # Insertion of a special text for ING but the solution is generic
                            if reg.partner_invoice_id and reg.partner_invoice_id.answers_ids:
                                special_msg = ''
                                parameter_obj = self.pool.get('cci_parameters.cci_value')
                                param_values = parameter_obj.get_value_from_names(cr, uid, ['msg_confirm_event'])
                                if param_values and param_values.has_key('msg_confirm_event'):
                                    SPECIAL_QUESTION_ID = param_values['msg_confirm_event']
                                    for answer in reg.partner_invoice_id.answers_ids:
                                        if answer.question_id and answer.question_id.id == SPECIAL_QUESTION_ID:
                                            special_msg = answer.text
                                    if special_msg:
                                        value += ('<br/><br/>' + special_msg)
                            value += '</p>'
                else:
                    value = ''
                text = text.replace(tag_name, value)
            elif tag_name == '{PERSO tu_nomfact}':
                if reg.unit_price > 0.001:
                    value = u'<p>Aucune adresse de facturation définie</p>'
                    if reg.partner_invoice_id:
                        # search of the first 'invoice' address, else first 'default' address
                        if reg.partner_invoice_id.address:
                            good_address = False
                            for address in reg.partner_invoice_id.address:
                                if address.type == 'invoice':
                                    good_address = address
                                    break
                            if not good_address:
                                for address in reg.partner_invoice_id.address:
                                    if address.type == 'default':
                                        good_address = address
                                        break
                        if good_address:
                            value = u'<p>Sans contre avis de ta part, ta participation sera facturée à : '
                            if good_address.name:
                                if good_address.name[0:2] == '- ' or good_address.name[0:3] == ' - ':
                                    value += (reg.partner_invoice_id.name + ' ' + good_address.name.lstrip())
                                else:
                                    value += good_address.name
                            else:
                                value += reg.partner_invoice_id.name
                            value += ', ' + (good_address.street or '')
                            if good_address.street2:
                                value += (u' - ' + good_address.street2)
                            if good_address.zip_id:
                                value += (u', ' + good_address.zip_id.name + ' ' + good_address.zip_id.city)
                            elif good_address.zip:
                                value += (u', ' + good_address.zip + ' ' + good_address.city)
                            if not reg.partner_invoice_id.vat_subjected:
                                value += u', TVA : Non assujetti'
                            else:
                                if reg.partner_invoice_id.vat:
                                    value += (u', TVA : ' + reg.partner_invoice_id.vat)
                                else:
                                    value += u', TVA : inconnue'
                            # Insertion of a special text for ING but the solution is generic
                            if reg.partner_invoice_id and reg.partner_invoice_id.answers_ids:
                                special_msg = ''
                                parameter_obj = self.pool.get('cci_parameters.cci_value')
                                param_values = parameter_obj.get_value_from_names(cr, uid, ['msg_confirm_event'])
                                if param_values and param_values.has_key('msg_confirm_event'):
                                    SPECIAL_QUESTION_ID = param_values['msg_confirm_event']
                                    for answer in reg.partner_invoice_id.answers_ids:
                                        if answer.question_id and answer.question_id.id == SPECIAL_QUESTION_ID:
                                            special_msg = answer.text
                                    if special_msg:
                                        value += ('<br/><br/>' + special_msg)
                            value += '</p>'
                else:
                    value = ''
                text = text.replace(tag_name, value)
            else:
                try:
                   text = text.replace(tag_name, str(eval(tag_name[7:-1])).strip())
                except Exception:
                    text = text.replace(tag_name, '??' + tag_name[7:-1] + '??')
        return text
    # this method overwrites the parent method to make it more adapted to CCI events
    # and more personalisable
    @api.multi
    def mail_user_confirm(self):
        tags = re.compile('{PERSO .*?}', re.IGNORECASE)
        for reg in self:
            # we re-format entirely the message for each registration because they can be of different event => the message change
            msg_mail = self.personalize_text(tags, reg.event_id.mail_confirm, reg)
#             src = reg.event_id.reply_to or False
#             dest = []
#             if reg.email_from:
#                 dest += [reg.email_from]
#                 if reg.email_cc:
#                     dest += [reg.email_cc]
#             if dest and src:
#                 tools.email_send(src, dest, 'Infos pratiques ' + (reg.event_id.name_on_site and reg.event_id.name_on_site or reg.event_id.product_id.name), msg_mail, tinycrm=str(reg.case_id.id), subtype='html')
# 
#             if not src:
#                 raise osv.except_osv(_('Error!'), _('You must define a reply-to address in order to mail the participant. You can do this in the Mailing tab of your event. Note that this is also the place where you can configure your event to not send emails automaticly while registering'))
        return False

    # this method overwrites the parent method to make it more adapted to CCI events
    # and more personalisable
    @api.multi
    def mail_user(self):
        tags = re.compile('{PERSO .*?}', re.IGNORECASE)
#         for reg in self:
#             msg_mail = ''
#             if reg.event_id.state in ['confirm', 'running']:
#                 if reg.event_id.mail_auto_confirm:
#                     msg_mail = self.personalize_text(cr, uid, tags, reg.event_id.mail_confirm, reg)
#             else:
#                 if reg.event_id.mail_auto_registr:
#                     msg_mail = self.personalize_text(cr, uid, tags, reg.event_id.mail_registr, reg)
#             flag = ''
#             src = reg.event_id.reply_to or False
#             dest = []
#             if reg.email_from:
#                 dest += [reg.email_from]
#                 if reg.email_cc:
#                     dest += [reg.email_cc]
#             if (reg.event_id.mail_auto_confirm or reg.event_id.mail_auto_registr) and msg_mail:
#                 if dest and src:
#                     if (reg.event_id.state in ['confirm', 'running']) and reg.event_id.mail_auto_confirm :
#                         flag = 't'
#                         tools.email_send(src, dest, 'Infos pratiques ' + (reg.event_id.name_on_site and reg.event_id.name_on_site or reg.event_id.product_id.name), msg_mail, tinycrm=str(reg.case_id.id), subtype='html')
#                     if reg.event_id.state in ['draft', 'fixed', 'open', 'confirm', 'running'] and reg.event_id.mail_auto_registr and not flag:
#                         tools.email_send(src, dest, 'Confirmation inscription ' + (reg.event_id.name_on_site and reg.event_id.name_on_site or reg.event_id.product_id.name), msg_mail, tinycrm=str(reg.case_id.id), subtype='html')
#                 if not src:
#                     raise osv.except_osv(_('Error!'), _('You must define a reply-to address in order to mail the participant. You can do this in the Mailing tab of your event. Note that this is also the place where you can configure your event to not send emails automaticly while registering'))
        return False
    
    @api.model
    def get_member_data(self, data_event, partner_invoice_id):
        ctx = self.env.context.copy()
        if data_event.product_id:
            data = {}
#             if contact_id:
#                 data_contact = self.pool.get('res.partner.contact').browse(cr, uid, contact_id)
#             else:
#                 data_contact = False
            if not partner_invoice_id:
                data['training_authorization'] = False
                if data_contact and data_contact.is_premium:
                    ctx['force_member'] = True
                data['unit_price'] = data_event.product_id.price_get(ptype='member_price')[data_event.product_id.id]
                if ctx.has_key('force_member'):
                    ctx['force_member'] = False
                return data
            data_partner = self.env['res.partner'].browse(partner_invoice_id)
            context.update({'partner_id': data_partner and data_partner.id})
            if data_contact and data_contact.is_premium:
                ctx['force_member'] = True
            data['unit_price'] = data_event.with_context(ctx).product_id.price_get(ptype='member_price')[data_event.product_id.id]
            if ctx.has_key('force_member'):
                ctx['force_member'] = False
            return data
        else:
            return {'unit_price' : False, 'invoice_label' : False}
    
    @api.multi
    def onchange_event2(self, event_id, partner_id):
        if not event_id:
            return {'value':{'unit_price' : False , 'invoice_label' : False }}
        data_event = self.env['event.event'].browse(event_id)
        data = self.get_member_data(data_event, partner_id)
        if data_event and data_event.product_id:
            data['invoice_label'] = data_event.product_id.name
        else:
            data['invoice_label'] = '' 
        return {'value':data}
    
    @api.multi
    def onchange_partner_id2(self, partner_id, event_id, email=False):
        data = {}
#         data['badge_partner'] = data['contact_id'] = data['partner_invoice_id'] = data['email_from'] = data['badge_title'] = data['badge_name'] = False
        if not partner_id:
            return {'value':data}
        # raise an error if the partner cannot participate to event.
        badge_part = False
        warning = False
        if partner_id:
            data_partner = self.env['res.partner'].browse(partner_id)
            if data_partner.alert_events:
                warning = {
                    'title': "Warning:",
                    'message': data_partner.alert_explanation or 'Partner is not valid but there is no explanation on partner, only the \'event warning\' selected'
                }
#             if data_partner.badge_partner:
#                 badge_part = data_partner.badge_partner
#         data['partner_invoice_id'] = partner_id
        # this calls onchange_partner_invoice_id
#         d = self.onchange_partner_invoice_id2(cr, uid, ids, partner_invoice_id, event_id, partner_id, contact_id)
        # this updates the dictionary
#         data.update(d['value'])
        addr = data_partner.address_get(['default','invoice'])
        if addr:
            if addr.has_key('default'):
                job_ids = self.env['res.partner'].search([('contact_id', '=', addr['default'])])
                if job_ids:
                    data['contact_id'] = job_ids[0].contact_id.id
                    d = self.onchange_contact_id2(data['contact_id'], event_id, partner_id, partner_invoice_id)
                    data.update(d['value'])
        partner_data = self.env['res.partner'].browse(partner_id)
        data['badge_partner'] = partner_data.name
        data = {'value':data}
        if badge_part:
            data['value']['badge_partner'] = badge_part
        if warning:
            data['warning'] = warning
        return data
    
    @api.multi
    def onchange_partner_invoice_id2(self, event_id, partner_id):
        data = {}
        data['training_authorization'] = data['unit_price'] = False
        if partner_invoice_id:
            data_partner = self.env['res.partner'].browse(partner_invoice_id)
            data['training_authorization'] = data_partner.training_authorization
        if not event_id:
            return {'value':data}
        data_event = self.env['event.event'].browse(event_id)
        data = self.get_member_data(data_event, partner_id)
        return {'value': data}
    
    @api.multi
    def onchange_contact_id2(self, contact_id, event_id, partner_id, partner_invoice_id):
        data = {}
        data['email_from'] = ''
        if not contact_id:
            data['badge_name'] = ''
            data['badge_title'] = ''
            d = self.onchange_badge_name(data['badge_name'])
            if d:
                data.update(d['value'])
            data_event = self.env['event.event'].browse(event_id)
            data.update(data_event.get_member_data(partner_invoice_id or partner_id, contact_id))
        else:
            contact = self.env['res.partner'].browse(contact_id)
            data['badge_name'] = contact.badge_name and contact.badge_name or (contact.name + ' ' + (contact.first_name or '')).strip()
            data['badge_title'] = contact.badge_title and contact.badge_title or contact.title
            if partner_id:
                partner_addresses = self.env['res.partner'].search([('parent_id', '=', partner_id)])
                job_ids = self.env['res.partner'].search([('contact_id', '=', contact_id), ('parent_id', 'in', partner_addresses)])
                if job_ids:
                    data['email_from'] = job_ids[0].email or ''#self.pool.get('res.partner.job').browse(cr, uid, job_ids[0]).email
                    data['badge_title'] = job_ids[0].function_label or '' #self.pool.get('res.partner.job').browse(cr, uid, job_ids[0]).function_label or ''
            if not data['email_from'] and contact.email:
                data['email_from'] = contact.email
            d = self.onchange_badge_name(data['badge_name'])
            data.update(d['value'])
            data_event = self.env['event.event'].browse(event_id)
            data.update(data_event.get_member_data(partner_invoice_id or partner_id, contact_id))
        return {'value':data}
    
    @api.model
    def create(self, vals):
        if vals['name'] == 'Registration:' or vals['name'] == 'Registration':
            vals['name'] = False  # to be sure to have the contact name with 'Registration'
        if vals.has_key('comments') and vals['comments']:
            vals['comments'] = vals['comments'].decode('utf-8')  # # to prevent a bug in cci_event module wich we can't modify because it is certified
        return super(event_registration, self).create(vals)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
