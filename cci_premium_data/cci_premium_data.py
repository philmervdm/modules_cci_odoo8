# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 CCI Connect ASBL. (http://www.cciconnect.be) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################
from openerp import models, fields, api , _
import datetime
from openerp import tools
import string
from operator import itemgetter
import random
import re

def convert_phone(string):
    if len(string) > 0:
        if len(string) == 9:
            if string[0:2] in ['02','03','04','09']:
                result = string[0:2] + "/" + string[2:5] + "." + string[5:7] + "." + string[7:]
            else:
                result = string[0:3] + "/" + string[3:5] + "." + string[5:7] + "." + string[7:]
        elif len(string) == 10:
            result = string[0:4] + "/" + string[4:6] + "." + string[6:8] + "." + string[8:]
        else:
            result = string
    else:
        result = ''
    return result

@api.multi
def personalize_texts(contact,tags,texts):
    full_texts = []
    for text in texts:
        for tag in tags.findall(text):
            tag_name = str(tag)
            if tag_name == '{PERSO cnp_contact}':
                text = text.replace(tag_name,( ( contact.title or '' ) + ' ' + contact.name + ' ' + ( contact.first_name or '' ) ).strip())
            elif tag_name == '{PERSO cpn_contact}':
                text = text.replace(tag_name,( ( contact.title or '' ) + ' ' + ( contact.first_name or '' ) + ' ' + contact.name ).strip().replace('  ',' '))
            elif tag_name == '{PERSO pn_contact}':
                text = text.replace(tag_name,( ( contact.first_name or '' ) + ' ' + contact.name ).strip())
            elif tag_name == '{PERSO np_contact}':
                text = text.replace(tag_name,( contact.name + ' ' + ( contact.first_name or '' ) ).strip())
            elif tag_name == '{PERSO n_contact}':
                text = text.replace(tag_name, contact.name.strip())
            elif tag_name == '{PERSO cn_contact}':
                text = text.replace(tag_name,( ( contact.title or '' ) + ' ' + contact.name ).strip())
            elif tag_name == '{PERSO p_contact}':
                text = text.replace(tag_name,( contact.first_name or '' ).strip())
            elif tag_name == '{PERSO p_id}':
                text = text.replace(tag_name,str(contact.id))
            elif tag_name == '{PERSO p_complex_id}':
                text = text.replace(tag_name,get_complex_id_from_id(contact.id))
            else:
                try:
                    text = text.replace(tag_name,str(eval(tag_name[7:-1])).strip())
                except Exception:
                    text = text.replace(tag_name,'??' + tag_name[7:-1] + '??')
        full_texts.append( text )
    return full_texts

class res_partner_contact(models.Model):
    _inherit = "res.partner"
    _description = "res.partner.contact"
    
    #pf_zip_code = fields.Char('Code Postal lieu résidence',size=50)
    #pf_facebook = fields.Boolean('Facebook')
    #pf_linkedin = fields.Boolean('LinkedIN')
    #pf_twitter = fields.Boolean('Twitter')
    #pf_facebook_freq = fields.Selection([('daily','1x/jour'),('daysbyweek','2 ou 3x/sem'),('weekly','1x/sem'),('few','- 1x/sem')],u'Fréquence Facebook')
    #pf_linkedin_freq = fields.Selection([('daily','1x/jour'),('daysbyweek','2 ou 3x/sem'),('weekly','1x/sem'),('few','- 1x/sem')],u'Fréquence LinkedIN')
    #pf_twitter_freq = fields.Selection([('daily','1x/jour'),('daysbyweek','2 ou 3x/sem'),('weekly','1x/sem'),('few','- 1x/sem')],u'Fréquence Twitter')
    #pf_smartphone = fields.Boolean(u'Possède Smartphone')
    #pf_smart_info = fields.Boolean(u'Lit infos sur SamrtPhone')
    #pf_tablet = fields.Boolean(u'Tablette')
    #pf_tablet_press = fields.Boolean(u'Lit infos sur tablette')
    #pf_app_pro = fields.Boolean(u'App professionnelles')
    #pf_invit_mail = fields.Boolean(u'Invit seulement par courriel')
    #pf_invit_network = fields.Boolean(u'Invit seulement par R.S')
    #pf_invit_post = fields.Boolean(u'Invitation postale')
    #pf_sms = fields.Boolean(u'Pas de SMS')
    #pf_ecustomer = fields.Boolean(u'eClient')
    #pf_pay_creditcard = fields.Boolean(u'Utilise carte de crédit')
    #pf_care_cci = fields.Boolean(u'Demande prise en charge par la CCI')
    #pf_use_language = fields.Boolean(u'Utilise des langues étrangères')
    #pf_eleccar = fields.Boolean(u'Voiture écolo')
    #pf_nighter = fields.Boolean(u'Sorteur en soirée')
    #pf_children = fields.Boolean(u'Enfants à la maison')
    #pf_want_invest = fields.Boolean(u'Investisseur déjà ou désireux')
    #pf_owner = fields.Boolean(u'Actionnaire ou propriétaire autres sociétés')
    #pf_cluber = fields.Boolean(u'Participe à des Business Clubs')
    #pf_club_cw = fields.Boolean(u'Cercle Wallonie')
    #pf_club_cl = fields.Boolean(u'Cercle du Lac')
    #pf_club_bni = fields.Boolean(u'BNI')
    #pf_club_apm = fields.Boolean(u'APM')
    #pf_club_gceq = fields.Boolean(u'Gr. C.E. du Québec')
    #pf_club_ypowpo = fields.Boolean(u'YPO/WPO')
    #pf_club_far = fields.Boolean(u'FAR')
    #pf_club_fce = fields.Boolean(u'FCE')
    #pf_club_new = fields.Boolean(u'NEW')
    #pf_club_zoning = fields.Boolean(u'Zoning')
    #pf_club_golf = fields.Boolean(u'Golf')
    #pf_club_sc = fields.Boolean(u'Service Club')
    #pf_club_other = fields.Boolean(u'Autre')
    #pf_club_other_names = fields.Char(u'Autres - Noms',size=120)
    #pf_networker = fields.Boolean(u'Networking')
    #pf_freq_network = fields.Selection([('often','Plusieurs x/sem'),('weekly','1 x/sem'),('monthly','1 ou 2 x/mois'),('quaterly','1 ou 2 x/trim'),('few','2 à 3 x/an')],u'Fréquence Networking')
    #pf_network_morning = fields.Boolean(u'Dispo networking matin')
    #pf_network_lunch = fields.Boolean(u'Dispo networking midi')
    #pf_network_dinner = fields.Boolean(u'Dispo networking diner')
    #pf_network_night = fields.Boolean(u'Dispo networking soirée')
    #pf_conf_8_10 = fields.Boolean(u'Dispo Conférence 8h-10h')
    #pf_conf_9_11 = fields.Boolean(u'Dispo Conférence 9h-11h')
    #pf_conf_10_12 = fields.Boolean(u'Dispo Conférence 10h-12h')
    #pf_conf_12_14 = fields.Boolean(u'Dispo Conférence 12h-14h')
    #pf_conf_14_16 = fields.Boolean(u'Dispo Conférence 14h-16h')
    #pf_conf_18_20 = fields.Boolean(u'Dispo Conférence 18h-20h')
    #pf_dispo_mon_morning = fields.Boolean(u'Dispo activ. lundi matin')
    #pf_dispo_mon_lunch = fields.Boolean(u'Dispo activ. lundi midi')
    #pf_dispo_mon_evening = fields.Boolean(u'Dispo activ. lundi soir')
    #pf_dispo_tue_morning = fields.Boolean(u'Dispo activ. mardi matin')
    #pf_dispo_tue_lunch = fields.Boolean(u'Dispo activ. mardi midi')
    #pf_dispo_tue_evening = fields.Boolean(u'Dispo activ. mardi soir')
    #pf_dispo_wed_morning = fields.Boolean(u'Dispo activ. mercredi matin')
    #pf_dispo_wed_lunch = fields.Boolean(u'Dispo activ. mercredi midi')
    #pf_dispo_wed_evening = fields.Boolean(u'Dispo activ. mercredi soir')
    #pf_dispo_thu_morning = fields.Boolean(u'Dispo activ. jeudi matin')
    #pf_dispo_thu_lunch = fields.Boolean(u'Dispo activ. jeudi midi')
    #pf_dispo_thu_evening = fields.Boolean(u'Dispo activ. jeudi soir')
    #pf_dispo_fri_morning = fields.Boolean(u'Dispo activ. vendredi matin')
    #pf_dispo_fri_lunch = fields.Boolean(u'Dispo activ. vendredi midi')
    #pf_dispo_fri_evening = fields.Boolean(u'Dispo activ. vendredi soir')
    #pf_dispo_sat_morning = fields.Boolean(u'Dispo activ. samedi matin')
    #pf_dispo_sat_lunch = fields.Boolean(u'Dispo activ. samedi midi')
    #pf_dispo_sat_evening = fields.Boolean(u'Dispo activ. samedi soir')
    #pf_dispo_sun_morning = fields.Boolean(u'Dispo activ. dimanche matin')
    #pf_dispo_sun_lunch = fields.Boolean(u'Dispo activ. dimanche midi')
    #pf_dispo_sun_evening = fields.Boolean(u'Dispo activ. dimanche soir')
    #pf_size_25 = fields.Boolean(u'-25 personnes')
    #pf_size_2550 = fields.Boolean(u'entre 25 et 50 personnes')
    #pf_size_50100 = fields.Boolean(u'entre 50 et 100 personnes')
    #pf_size_100 = fields.Boolean(u'+100 personnes')
    #pf_price_event = fields.Selection([('all-in','All-In'),('choice','A la carte')],u'Type prix pour events')
    premium_login = fields.Char('Login Premium',size=40)
    premium_mp = fields.Char('Mot de passe',size=40)

    @api.multi
    def send_new_login_form(self,contact_ids,template_id,force_existing,email_from,email_to=''):
        res_sended = []
        res_no_email = []
        res_existing = []
        #
        template_obj = self.env['email.template']
#         templates = template_obj.browse(cr,uid,[template_id])
        if template_id:
            template = template_id
            tags = re.compile('{PERSO .*?}',re.IGNORECASE)
#             contact_obj = self.pool.get('res.partner.contact')
#             contacts = contact_obj.browse(cr,uid,contact_ids)
            for contact in self.browse(contact_ids):
                if contact.premium_login and contact.premium_mp and not force_existing:
                    res_existing.append(contact.id)
                else:
                    if not email_to:
                        # search the email_address for the sending : if perso, select first, else select first job email
                        if contact.email:
                            email_premium = contact.email
                        else:
                            email_premium = ''
                            if contact.other_contact_ids:
                                job_emails = []
                                for job in contact.other_contact_ids:
                                    if job.email:
                                        job_emails.append({'sequence':job.sequence_contact,'email':job.email})
                                if job_emails:
                                    job_emails = sorted(job_emails, key=lambda k: k['sequence'])
                                    email_premium = job_emails[0]['email']
                    else:
                        email_premium = email_to.strip()
                    # if email address for sending, compose texts
                    if email_premium:
                        full_texts = personalize_texts(contact,tags,[template.subject,template.body_html])
                        # sending of the email
                        tools.email_send(email_from, [email_premium,], full_texts[0], full_texts[1])
                        res_sended.append(email_premium)
                    else:
                        res_no_email.append(contact.id)
        return (res_sended,res_no_email,res_existing)
    
    @api.model
    def send_new_login_to_email(self,email_to_search):
        found_contact_id = False
        contact_obj = self.env['res.partner']
        contact_ids = contact_obj.search([('email','=',email_to_search.strip())])
        if contact_ids and len(contact_ids) == 1:
            found_contact_id = contact_ids[0]
        else:
            # search in jobs if jobs have this email address and design only one contact_id
            job_obj = self.env['res.partner']
            job_ids = job_obj.search([('email','=',email_to_search.strip())])
            if job_ids:
                jobs = job_ids.read(['contact_id'])
                if len(job_ids) == 1:
                    if jobs[0]['contact_id']:
                        found_contact_id = jobs[0]['contact_id'][0]
                else:
                    contact_ids = []
                    for job in jobs:
                        if job['contact_id']:
                            if job['contact_id'][0] not in contact_ids:
                                contact_ids.append(job['contact_id'][0])
                    if len(contact_ids) == 1:
                        found_contact_id = contact_ids[0]
        if found_contact_id:
            template_obj = self.env['email.template']
            template_ids = template_obj.search([('name','=','Template Login Password Premium')])
            if template_ids and len(template_ids) == 1:
                (sended,error_no_send,send_existing) = self.send_new_login_form([found_contact_id.id],template_ids[0],True,'philmer@ccilvn.be',email_to_search.strip())
                if len(sended) == 1:
                    result = True
                    message = 'OK'
                else:
                    result = False
                    message = 'Problem while sending of the email'
            else:
                result = False
                message = 'Problem to find the template in the OpenERP engine'
        else:
            result = False
            message = 'Impossible to retrieve one and one one contact with this email address'
        return (result,message)

#class res_partner_job(models.Model):
#    _inherit = "res.partner"
#    _description = "res.partner.job"
    
    #personal_statut = fields.Selection([('employee','Employee'),('ind_physical','Independent'),('ind_manager','Dirigeant d\'entreprise'),('ind_management','Société de management'),('ind_professional','Profession libérale'),('student',u'Etudiant'),('unemployed',u'En Recherche d\'emploi')],'Personal Status')
    #main_direction = fields.Boolean(u'Poste au sein de la direction générale')
    #type_direction = fields.Selection([('onlydir',u'Patron propriétaire'),('majority','Patron majoritaire'),('associated',u'Patron associé'),('number1','Numéro 1')],u'Direction générale')
    #type_purchase = fields.Selection([('creator',u'Créé son entreprise'),('laterparticiper',u'Acquis des patrs en cours de route'),('buyer',u'Repris une entreprise')],u'Patron qui a')
    #year_purchase =  fields.Char(u'Année arrivée',size=4)
    #from_purchase = fields.Selection([('family',u'Membre de la famille'),('boss',u'Ancien patron'),('company',u'Tiers')],'Acquise auprès de')
    #shareholder_count = fields.Selection([('2','2'),('3','3'),('4','4'),('5+','5 et +'),('stock_exchange',u'Société cotée en Bourse')],'Nbre actionnaires')
    #share_invest = fields.Boolean(u'Présence Invest')
    #share_investor = fields.Boolean(u'Présence investisseur ou Business Angel')
    #share_crowdfund = fields.Boolean(u'Crowfunding')
    #share_family = fields.Boolean(u'Membres de la famille')
    #executive_committee = fields.Boolean(u'Membre du comité de direction')
    #decision_level = fields.Selection([('direction',u'Direction'),('cadre',u'Cadre'),('employee',u'Employé')],u'Niveau de décision')
    #others_name = fields.Char(u'Autre département',size=50)

#class res_partner_address(models.Model):
#    _inherit = "res.partner"
#    _description = "res.partner.address"

    #zoning = fields.Boolean('Situated in Zoning')

#class res_partner(models.Model):
#    _inherit = "res.partner"
#    _description = "res.partner"
#    
#    can_check_formation = fields.Selection([('null',u'Ne sais pas'),('yes',u'OUI'),('no',u'Non')],'Can Use Checks Formation')
#    international_company = fields.Boolean('Work Internationaly')
#    formation_priority = fields.Boolean('Priority to formation')
#    formation_invest = fields.Boolean('Invest in formation')
#    equal_representation = fields.Char('Equal Representation',size=10)
#    employee_slice = fields.Selection([('1','1'),('2-5','2-5'),('6-9','6-9'),('10-19','10-19'),('20-49','20-49'),('50-99','50-99'),('100-249','100-249'),('250-499','250-499'),('500+','500+')],'Employees\' Slice')

