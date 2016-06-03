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

from openerp import fields, models, api, _
import time
from datetime import datetime
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
# import smtplib
import csv
from xlwt import *
import ftplib
import base64
from openerp import tools
import random
random.seed()

AREAS = [('1', 'Liège'), ('2', 'Namur'), ('3', 'Brabant wallon'), ('4', 'Hainaut'), ('5', 'Hainaut occidental'), ('6', 'Flandres')]

class res_partner_contact(models.Model):
    _inherit = "res.partner"
    _description = "res.partner"

    date_passwordsend = fields.Date('Date Sending Password', help="Date of sending of login-password by mail")

class cci_newsletter_source(models.Model):
    _name = "cci_newsletter.source"
    _description = "Source of manual subscriber for the CCI Newsletter"
    
    name = fields.Char('Name', required=True, size=64)
    default_area = fields.Selection(AREAS, string='Default Area')
    next_id = fields.Integer('Next ID', help='Next ID used for new subscriber in this source')
    flanders = fields.Boolean('List for flanders')
    
    @api.model
    def get_next_id(self, source_id):
        self.env.cr.execute('SELECT id, next_id FROM cci_newsletter_source WHERE id = %s FOR UPDATE' % source_id)
        res = self.env.cr.dictfetchone()
        if res:
            self.env.cr.execute('UPDATE cci_newsletter_source SET next_id = next_id + 1 WHERE id= %s' % source_id)
            if res['next_id']:
                return res['next_id']
            else:
                return 1
        return 1

class cci_newsletter_queue_new(models.Model):
    _name = "cci_newsletter.queue_new"
    _description = "New subscriber waiting one day before sending new login-pasword"
        
    date = fields.Date("Date of creation")
    send_date = fields.Date("Date of sending")
    mail = fields.Char("Email", size=250)
    name = fields.Char("Name of contact", size=64)
    first_name = fields.Char("First name of contact", size=64)
    login = fields.Char("Created login", size=64)
    password = fields.Char("Created password", size=64)
    token = fields.Char("Token", size=64)
    courtesy = fields.Char("Courtesy", size=20)
    function = fields.Char("Function", size=200)
    company = fields.Char("Company", size=200)
    user_id = fields.Many2one('res.users', 'Salesman')
    contact_id = fields.Many2one('res.partner', 'Linked Contact', domain=[('parent_id', '!=', False)])
    active = fields.Boolean("Active", default=True)

class cci_newsletter_log(models.Model):
    _name = "cci_newsletter.log"
    _description = "Log of synchronisation of sending to website"

    datetime = fields.Datetime("Date", readonly=True)
    short = fields.Text("In short", readonly=True)
    full = fields.Text("Details", readonly=True)
    count = fields.Integer("Count", readonly=True)

    _order = 'datetime desc'

class cci_newsletter_subscriber(models.Model):
    _name = 'cci_newsletter.subscriber'
    _description = 'Manual subscriber to the CCI newsletter'

    internal_id = fields.Integer('ID interne Computerland')
    name = fields.Char(string='Name of contact', size=64)
    first_name = fields.Char('First name of contact', size=64)
    forced_area = fields.Selection(AREAS, 'Forced Area')
    email = fields.Char('EMail', size=200, required=True)
    company_name = fields.Char('Company', size=200)
    login_name = fields.Char('Login', size=64)
    password = fields.Char('Password', size=64)
    token = fields.Char('Token', size=64)
    comments = fields.Text('Comments')
    expire = fields.Date('Expiration Date')
    active = fields.Boolean('Active', default=True)
    source_id = fields.Many2one('cci_newsletter.source', 'Source', required=True)

    @api.model
    def _get_id(self, source_id):
        obj_source = self.env['cci_newsletter.source']
        new_id = obj_source.get_next_id(source_id)
        return new_id

    @api.model
    def create(self, vals):
        # overwrite the create: if the internal_id, login, password or token is empty, complete them
        if not vals.has_key('internal_id') or not vals['internal_id']:
            vals['internal_id'] = self._get_id(vals['source_id'])
        if not vals.has_key('token') or not vals['token']:
            vals['token'] = self._create_unique_token()
        if not vals.has_key('login_name') or not vals['login_name']:
            vals['login_name'] = self._create_unique_login(vals['email'])
        if not vals.has_key('password') or not vals['password']:
            vals['password'] = self._create_password(vals['name'] or '', vals['first_name'] or '')
        return super(cci_newsletter_subscriber, self).create(vals)

    @api.model
    def extract_data(self, connection='data_compu', connection_ae='ae_files', send_ftp=True, send_new_login=True,
                           create_new_login=True, smtp_server='base', smtp_address='base',
                           include_prospects=True, include_all_others=False):
        # this method extract the files to update Computerland site mainly with readers of 'Revue de Presse'
        # result contains the text that will be show to the user if used via wizard
        def _clean_CR(string):
            return string.replace('\n', '')

        def _convert_html(string_or_boolean):
            if string_or_boolean:
                return string_or_boolean.replace(u"é", u"&eacute;").replace(u"è", u"&egrave;").replace(u"à", u"&agrave;").replace(u"â", u"&acirc;").replace(u"ê", u"&ecirc;").replace(u"î", u"&icirc;").replace(u"ô", u"&ocirc;").replace(u"ç", u"&ccedil;").replace(u"ä", u"&auml;").replace(u"ë", u"&euml;").replace(u"ï", u"&iuml;").replace(u"ö", u"&ouml;").replace(u"ü", u"&uuml;").replace(u"ù", u"&ugrave;").replace(u"°", u"&deg;").replace(u"\u2019", u"'").replace(u"\xc7", u"&Ccedil;").replace(u"Ë", u"&Euml;").replace(u"Â", u"&Acirc;").replace(u"É", u"&Eacute;").replace(u"Î", u"&Icirc;").replace(u"Ö", u"&Ouml;").replace(u"Ü", u"&Uuml;").replace(u"Ê", u"&Ecirc;").replace(u"È", u"&Egrave;").replace(u"û", u"&ugrave").replace(u"Ï", u"&Iuml;")
            else:
                return string_or_boolean

        def _convertCP850(string):
            string = string.replace(u'é', u'e').replace(u'è', u'e').replace(u'ê', u'e').replace(u'â', u'a').replace(u'à', u'a').replace(u'ù', u'u').replace(u'û', u'u')
            string = string.replace(u'ë', u'e').replace(u'ä', u'a').replace(u'ï', u'i').replace(u'ö', u'o').replace(u'ü', u'u').replace(u'Ï', u'I')
            string = string.replace(u'\u0153', "oe").replace(u'\u2013', "-").replace(u'\u2018', "'").replace(u'\u2019', "'").replace(u'\u2026', "...")
            string = string.replace(u'\u20ac', "euros").replace(u'\u201c', '"').replace(u'\u201d', '"')
            return string.encode("cp850")

        def _clean_locality(locality):
            if locality[0:7] == "manuel ":
                locality = locality[8:]
            return locality

        def _get_name_and_suffix(address_name, company_name):
            if address_name and address_name[0:2] == "- ":
                kept_name = company_name + " " + address_name
            elif address_name and address_name[0:3] == " - ":
                kept_name = company_name + address_name
            else:
                kept_name = address_name or company_name
            suffix = ''
            if kept_name.rfind(' (') > -1:
                suffix = kept_name[kept_name.rfind(' (') + 1:]
                if suffix and (suffix in SUFFIXES):
                    kept_name = kept_name[:kept_name.rfind(' (')]
                    suffix = "avec " + suffix
                else:
                    suffix = ''
            return (kept_name, suffix)
        
        def _add_log(string, type_log='full'):
            if string:
                full_log.append(string)
                if type_log == 'short':
                    simple_log.append(string)

        result = 'Start : ' + time.strftime("%Y-%m-%d %H:%M:%S") + '\n'
        count_events = 0
        count_users = 0
        count_new_users = 0
        simple_log = []
        full_log = []
        #
        # PART 1 : Sending to new created members (added to the list yesterday)
        #          their login-password by email
        # 
        sended_login_mails = 0
        if send_new_login:

            newly_created_obj = self.env['cci_newsletter.queue_new']
            res_partner_contact_obj = self.env['res.partner']
            newly_created_ids = newly_created_obj.search([('active', '=', True)])
            if newly_created_ids:
                strFrom = 'nepasrepondre@cciconnect.be'
                HTMLText = """
<meta http-equiv="Content-Language" content="fr-be">
<meta http-equiv="Content-Type" content="text/html; charset=windows-1252">
<title>Site internet de la CCI Connect - vos nouveaux codes d'acc&egrave;</title>
<body topmargin="0" leftmargin="0" bgcolor="#C0C0C0" style="font-family:'verdana','arial'; font-size:8px;">
  <center>
  <table border="0" width="900" bgcolor="#FFFFFF" cellpadding="0" cellspacing="0">
    <tr>
      <td width="885" valign="middle" height="179" background="http://la-revue-de-presse-de-la-cci.be/images/contenu/Layout_CCIMAG/fond_header.jpg">
        <p align="center" style="margin-left: 15px;"><a href="http://www.cciconnect.be"><img border="0" src="http://la-revue-de-presse-de-la-cci.be/images/contenu/Logos_ProdActivite/cciconnecton.jpg" width="289" height="70" align="left"></a></p>
      </td>
    </tr>
  <tr><td colspan="2">
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:12px;">%s %s</font>,</p>
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:12px;">Nous venons de vous identifier dans notre fichier des entreprises membres de la CCI en tant que '%s' au sein de l'entreprise '%s', avec l'adresse mail : %s.</p>
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:12px;">Il vous est maintenant possible d'acc&eacute;der &agrave; l'espace membre sur le site de la CCI : <a href="http://www.cciconnect.be">www.cciconnect.be</a>.</p>
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:12px;">Afin que vous puissiez b&eacute;n&eacute;ficier de toutes ses fonctionnalit&eacute;s, vous trouverez ci-dessous vos codes d'acc&egrave;s &agrave; votre espace personnel.</p>
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:12px;"><strong>votre identifiant</strong> ("login") : <strong>%s</strong></p>
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:12px;"><strong>votre mot de passe</strong> ("password") : <strong>%s</strong></p>
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:12px;">vous pouvez acc&eacute;der directement &agrave; votre espace via ce lien : <a href="%s">Espace Personnel</a></p>
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:12px;">Parmi les <strong>fonctionnalit&eacute;s</strong> :</p>
  <p style="margin-left: 75; margin-right: 25; font-family:'verdana','arial'; font-size:12px;">- personnalisation de votre propre page d'accueil<br />
- inscriptions aux activit&eacute;s<br />
- visualisation de la liste des participants des activit&eacute;s auxquelles vous &ecirc;tes inscrit(e)<br />
- t&eacute;l&eacute;chargement de la liste au format excel<br />
- possibilit&eacute; de contacter directement les autres participants&nbsp;<br />
- t&eacute;l&eacute;chargement de la liste des entreprises membres au format excel</p>
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:12px;">Afin de mieux vous (faire) conna&icirc;tre, compl&eacute;tez votre <strong>profil</strong>, 
  ajoutez votre <strong>photo</strong>, le <string>logo</strong> de votre entreprise !!</p>
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:12px;">&nbsp;&nbsp;Le d&eacute;partement MEDIAS</p>
  <p style="margin-left: 50; margin-right: 25; font-family:'verdana','arial'; font-size:10px;">* <em>Ce mail a &eacute;t&eacute; envoy&eacute; de mani&egrave;re automatique. Il n'est pas possible d'y r&eacute;pondre. Si vous avez des questions, n'h&eacute;sitez pas &agrave; la poser &agrave; %s</em>.
  <p>&nbsp;</p>
  </td>
  </table>
  </center>
</body>
"""

                TXTText = """
%s %s

Nous venons de vous identifier dans notre fichier des entreprises membres de la CCI en tant que '%s' au sein de l'entreprise '%s', avec l'adresse mail : %s.
Il vous est maintenant possible d'acceder a l'espace membre sur le site de la CCI : www.cciconnect.be.
Afin que vous puissiez beneficier de toutes ses fonctionnalites, vous trouverez ci-dessous vos codes d'acces a votre espace personnel.
- votre identifiant ("login") : %s
- votre mot de passe ("password") : %s
- vous pouvez acceder directement a votre espace via ce lien : %s
Parmi les fonctionnalites :
- personnalisation de votre propre page d'accueil
- inscriptions aux activites
- visualisation de la liste des participants des activites auxquelles vous etes inscrit(e)
- telechargement de la liste au format excel
- possibilite de contacter directement les autres participants
- telechargement de la liste des entreprises membres au format excel

Afin de mieux vous (faire) connaitre, completez votre profil, 
  ajoutez votre photo, le logo de votre entreprise !!
  
Le departement MEDIAS
Ce mail a ete envoye de maniere automatique. Il n'est pas possible d'y repondre. Si vous avez des questions, n'hesitez pas a la poser a %s.
"""

                newly_created = newly_created_ids.read(['id', 'mail', 'name', 'first_name', 'login', 'password', 'token', 'courtesy', 'function', 'company',
                                                               'contact_id', 'user_id'])

                # smtp = smtplib.SMTP()
                # smtp.connect('mail.infomaniak.ch',2525)
                # smtp.login('nepasrepondre@cciconnect.be', 'H4yk751E')

                for nuser in newly_created:
                    if nuser['mail']:
                        # translate the user_id
                        if nuser['user_id'] == '13':
                            commercial = u"Simon Micha - 0497/52.88.58 - <a href=\"mailto:sm@cciconnect.be\">sm@cciconnect.be</a>"
                            commercial_text = "Simon Micha - 0497/52.88.58 - sm@cciconnect.be"
                        elif nuser['user_id'] == '15':
                            commercial = u"Christophe Raymond - 0476/75.32.59 - <a href=\"mailto:cr@cciconnect.be\">cr@cciconnect.be</a>"
                            commercial_text = "Christophe Raymond - 0476/75.32.59 - cr@cciconnect.be"
                        elif nuser['user_id'] == '16':
                            commercial = u"Gilles Foret - 0478/25.06.38 - <a href=\"mailto:gf@cciconnect.be\">gf@cciconnect.be</a>"
                            commercial_text = "Gilles Foret - 0478/25.06.38 - gf@cciconnect.be<"
                        elif nuser['user_id'] == '17':
                            commercial = u"Sylvie del Rio - 0474/54.94.61 - <a href=\"mailto:sdr@cciconnect.be\">sdr@cciconnect.be</a>"
                            commercial_text = "Sylvie del Rio - 0474/54.94.61 - sdr@cciconnect.be"
                        else:
                            commercial = u"<a href=\"http://www.cciconnect.be/page.asp?id=125&langue=FR\">l'interlocuteur de votre choix</a> &agrave; la CCI"
                            commercial_text = "l'interlocuteur de votre choix a la CCI : http://www.cciconnect.be/page.asp?id=125&langue=FR"
                    
                        # Create the root message and fill in the from, to, and subject headers
                        msgRoot = None
                        msgRoot = MIMEMultipart('related')
                        msgRoot['Subject'] = u"Site Internet de la CCI Connect - vos nouveaux codes d'accès"
                        # msgRoot['From'] = strFrom
                        # msgRoot['To'] = _clean_CR(nuser['mail'])
                        msgRoot.preamble = 'This is a multi-part message in MIME format.'

                        # Encapsulate the plain and HTML versions of the message body in an
                        # 'alternative' part, so message agents can decide which they want to display.
                        msgAlternative = MIMEMultipart('alternative')
                        msgRoot.attach(msgAlternative)


                        fullText = _convert_html(HTMLText % (nuser['courtesy'], nuser['name'], nuser['function'], nuser['company'], _clean_CR(nuser['mail']), _clean_CR(nuser['login']), nuser['password'], nuser['token'], commercial))
                        # msgText = MIMEText( fullText, 'html')
                        # msgAlternative.attach(msgText)

                        # msgText = MIMEText( _convertCP850( TXTText % (nuser['courtesy'],nuser['name'],nuser['function'],nuser['company'],_clean_CR(nuser['mail']),_clean_CR(nuser['login']),nuser['password'],nuser['token'],commercial_text)) )
                        # msgAlternative.attach(msgText)

                        # Send the email
                        try:
                            tools.email_send('noreply@ccilvn.be', [_clean_CR(nuser['mail'])], u"Site Internet de la CCI Liège Verviers Namur - vos nouveaux codes d'accès", fullText, subtype='html')

                            # smtp.sendmail(strFrom, _clean_CR(nuser['mail']), msgRoot.as_string())
                            sended_login_mails += 1

                            # record the sended dynamic data in oldConfirms.csv
                            nuser = newly_created_obj.browse(nuser['id'])
                            nuser.write({'active':False, 'send_date':time.strftime("%Y-%m-%d")})

                            # record the date of sending in res.contact
                            if nuser['contact_id']:
                                nuser_contact = res_partner_contact_obj.browse(nuser['contact_id'][0])
                                nuser_contact.write({'date_passwordsend':time.strftime("%Y-%m-%d")})
                        except Exception, error:
                            # error in the sending, probably caused by an email address with accentuated caracters
                            # => continue with the next addresses
                            # we need to connect again to smtp because the error seems to lets some errors in smtp.sendmail
                            # for the following address
                            # smtp = smtplib.SMTP()
                            # smtp.connect('mail.infomaniak.ch',2525)
                            # smtp.login('nepasrepondre@cciconnect.be', 'H4yk751E')
                            _add_log(u'email incorrect => pas d\'envoi (%s) - erreur %s' % (_clean_CR(nuser['mail']), str(error)), 'full')
                # smtp.quit()
        _add_log(u'Emails pour donner des login-password envoyés aujourdhui : ' + str(sended_login_mails), 'short')

        #
        # PART 2 : Extract Data from OpenERP while creating new login-password-token for new users
        #
        SUFFIXES = ['(1)', '(2)', '(3)', '(4)', '(5)', '(6)', '(7)', '(8)', '(9)', '(10)', '(11)', '(12)', '(13)', '(14)', '(15)', '(16)', '(17)', '(18)', '(19)', '(20)']
        QUESTION_IDS = [75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 101, 102]
        EXCLUDED_LOGINS = ['autrezone', 'jamais', 'double_email']  # the Excluded login mark the contact we don't take into account for the cci connect automatic list
        ALTEREGOTYPES = [16]  # ID des types de clugbs à prendre en charge pour Alter Ego

        ftp_files = []

        # 2.1 : sending of predefined answers to some questions
        answer_obj = self.env['crm_profiling.answer']
        answer_ids = answer_obj.search([('question_id', 'in', QUESTION_IDS), ('name', '<>', '/')])
        _add_log(u"%s reponses precodees trouves" % str(len(answer_ids)))
        answers = answer_ids.read(['id', 'question_id', 'name'])
        hfOut = open('answers.csv', 'w')
        hfCSVAnswer = csv.writer(hfOut, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
        hfCSVAnswer.writerow(['question_id', 'answer_id', 'name'])
        for answer in answers:
            if answer['question_id']:
                csvrecord = []
                csvrecord.append(answer['question_id'][0])
                csvrecord.append(answer['id'])
                csvrecord.append(_clean_CR(answer['name'] or '-no name-').encode("cp1252"))
                hfCSVAnswer.writerow(csvrecord)
        hfOut.close()
        ftp_files.append('answers.csv')

        # 2.2 : sending of activity sectors
        cat_obj = self.env['res.partner.category']
        sector_ids = cat_obj.search([])
        sectors = sector_ids.with_context({'lang':'fr_FR'}).read(['id', 'complete_name', 'name'])
        hfOut = open('sectors.csv' , 'w')
        hfCSVSector = csv.writer(hfOut, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
        hfCSVSector.writerow(['category_id', 'complete_name', 'name'])
        len_sectors = 0
        for sector in sectors:
            if 'Secteur d\'activ' in sector['complete_name']:
                csvrecord = []
                cleaned_name = (sector['name'] or '')
                pos = cleaned_name.rfind(' [')
                if pos > -1:
                    cleaned_name = cleaned_name[0:pos]
                csvrecord.append(sector['id'])
                csvrecord.append(_clean_CR(sector['complete_name'] or '').encode('cp1252'))
                csvrecord.append(_clean_CR(cleaned_name).encode('cp1252'))
                hfCSVSector.writerow(csvrecord)
                len_sectors += 1
        hfOut.close()
        ftp_files.append('sectors.csv')
        _add_log(u"%s secteurs d'activites trouves" % len_sectors)
        
        # 2.3 Letters identifying functions
        function_obj = self.env['res.partner.function']
        codef_ids = function_obj.search([])
        codesf = codef_ids.read(['id', 'code', 'name'])
        hfOut = open('functions.csv' , 'w')
        hfCSVCodeF = csv.writer(hfOut, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
        hfCSVCodeF.writerow(['id', 'code', 'name'])
        for code in codesf:
            csvrecord = []
            csvrecord.append(code['id'])
            csvrecord.append(code['code'])
            csvrecord.append((code['name'] or '').encode('cp1252'))
            hfCSVCodeF.writerow(csvrecord)
        hfOut.close()
        ftp_files.append('functions.csv')
        _add_log(u"%s codes fonctions trouves" % len(codef_ids))

        # 2.4 Courtesies
        title_obj = self.env['res.partner.title']
        courtesy_ids = title_obj.search([('domain', '=', 'contact')])
        courtesies = courtesy_ids.read(['id', 'shortcut', 'name'])
        hfOut = open('courtesies.csv' , 'w')
        hfCSVCourtesy = csv.writer(hfOut, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
        hfCSVCourtesy.writerow(['id', 'shortcut', 'name'])
        for courtesy in courtesies:
            csvrecord = []
            csvrecord.append(courtesy['id'])
            csvrecord.append((courtesy['shortcut'] or '').encode('cp1252'))
            csvrecord.append((courtesy['name'] or '').encode('cp1252'))
            hfCSVCourtesy.writerow(csvrecord)
        hfOut.close()
        ftp_files.append('courtesies.csv')
        _add_log(u"%s civilites trouvees" % len(courtesy_ids))

        # 2.5 companies structures
        forme_ids = title_obj.search([('domain', '=', 'partner')])
        formes = forme_ids.read(['id', 'shortcut', 'name'])
        hfOut = open('formesjur.csv' , 'w')
        hfCSVForme = csv.writer(hfOut, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
        hfCSVForme.writerow(['id', 'shortcut', 'name'])
        for formejuridique in formes:
            csvrecord = []
            csvrecord.append(formejuridique['id'])
            csvrecord.append((formejuridique['shortcut'] or '').encode("cp1252"))
            csvrecord.append((formejuridique['name'] or '').encode("cp1252"))
            hfCSVForme.writerow(csvrecord)
        hfOut.close()    
        ftp_files.append('formesjur.csv')
        _add_log(u"%s formes juridiques trouvees" % len(forme_ids))

        # 2.6 we extract all events open/confirm/running with a valid date in the future
        today = datetime.now()
        event_obj = self.env['event.event']
        event_ids = event_obj.search([('date_end', '>=', today.strftime('%Y-%m-%d')), ('state', 'in', ['open', 'confirm', 'running'])])
        events = event_ids.read(['id', 'name', 'date_begin', 'date_end', 'note', 'type', 'product_id', 'name_on_site'])
        hfOut = open('events.csv' , 'w')
        hfCSVEvent = csv.writer(hfOut, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
        hfCSVEvent.writerow(['id', 'name', 'date_begin', 'date_end', 'note', 'type_name', 'type_interet', 'product_id'])
        types_of_event = []
        events_mi = []
        dEvents = {}
        for event in events:
            csvrecord = []
            current_name = ''
            csvrecord.append(event['id'])
            if event['name_on_site']:
                csvrecord.append(event['name_on_site'].encode('cp1252'))
                current_name = event['name_on_site']
            else:
                if event['product_id']:
                    csvrecord.append((event['product_id'][1] or '').encode('cp1252'))
                    current_name = event['product_id'][1]
                else:
                    csvrecord.append((event['name'] or '').encode('cp1252'))
                    current_name = (event['name'] or '')
            csvrecord.append(event['date_begin'] or '')
            csvrecord.append(event['date_end'] or '')
            csvrecord.append((event['note'] or '').replace('\n', '').replace('"', "'").encode('cp1252'))
            event_type = 0
            if event['type']:
                event_type = 2000 + event['type'][0]
                csvrecord.append((event['type'][1] or '').encode('cp1252'))
                csvrecord.append(event_type)
                if not (event['type'] in types_of_event):
                    types_of_event.append(event['type'])  # # pour ajout en tant que marque d'intérêt invisible
            else:
                csvrecord.append('')
                csvrecord.append(0)
            _add_log(current_name + '[' + str(event['id']) + ']')
            if event['product_id']:
                csvrecord.append(event['product_id'][0])
            else:
                csvrecord.append(0)
            hfCSVEvent.writerow(csvrecord)
            events_mi.append((csvrecord[0], csvrecord[1]))  # # pour ajout en tant que marque d'intérêt invisible
            if event_type > 0:
                dEvents[event['id']] = event_type
        hfOut.close()
        event_mi_ids = []
        for (id, name) in events_mi:
            event_mi_ids.append(id)
        type_event_ids = []
        for (id, name) in types_of_event:
            type_event_ids.append(id)
        _add_log(u"%s events a publier trouves" % len(event_ids), 'short')
        log_count_events = len(event_ids)
        ftp_files.append('events.csv')

        # 2.7 extraction of country codes
        country_obj = self.env['res.country']
        pays_ids = country_obj.search([])
        pays = pays_ids.read(['id', 'code', 'name'])
        hfOut = open('pays.csv' , 'w')
        hfCSVPays = csv.writer(hfOut, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
        hfCSVPays.writerow(['id', 'code', 'name'])
        for country in pays:
            csvrecord = []
            csvrecord.append(country['id'])
            csvrecord.append((country['code'] or '').encode('cp1252'))
            csvrecord.append((country['name'] or '').encode('cp1252'))
            hfCSVPays.writerow(csvrecord)
        hfOut.close()
        ftp_files.append('pays.csv')
        _add_log(u"%s pays trouves" % len(pays_ids))

        # 2.8 extraction of belgian zip codes
        # and recording in dictinnary for usage later in method
        zip_obj = self.env['res.partner.zip']
        zip_ids = zip_obj.search([])
        zips = zip_ids.read(['id', 'city', 'name', 'groups_id'])
        hfOut = open('zips.csv' , 'w')
        hfCSVZip = csv.writer(hfOut, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
        hfCSVZip.writerow(['id', 'code', 'loc'])
        dZips = {}
        for zip in zips:
            dZips[zip['id']] = zip
            if zip['groups_id'] and 48 in zip['groups_id']:
                csvrecord = []
                csvrecord.append(zip['id'])
                csvrecord.append(_clean_CR(zip['name'] or '').encode('cp1252'))
                csvrecord.append(_clean_CR(zip['city'] or '').encode('cp1252'))
                hfCSVZip.writerow(csvrecord)
        hfOut.close()
        ftp_files.append('zips.csv')
        _add_log(u"%s codes postaux belges trouves" % len(zip_ids))

        #
        # PART 3. Extraction from Partners
        #
        published_emails = []
        published_logins = []
        published_tokens = []
        published_ids = []
        partner_obj = self.env['res.partner']
        address_obj = self.env['res.partner']
        job_obj = self.env['res.partner']
        contact_obj = self.env['res.partner.contact']
        reg_obj = self.env['event.registration']
        subscriber_obj = self.env['cci_newsletter.subscriber']
        partner_ids = partner_obj.search([('membership_state', 'in', ['paid', 'invoiced', 'free']), ('state_id', '=', 1)])
        if partner_ids:
            _add_log(u"%s membres trouves" % str(len(partner_ids)))
            partners = partner_ids.read(['id', 'name', 'title', 'membership_state', 'address', 'vat', 'website', 'user_id'])

            # extraction of all linked addresses
            addr_ids = []
            dPartners = {}
            for partner in partners:
                dPartners[ partner['id'] ] = partner
                if partner['address']:
                    addr_ids.extend(partner['address'])
            _add_log(u"%s adresses liees" % str(len(addr_ids)))
            addresses = addr_ids.read(['id', 'active', 'name', 'phone', 'fax', 'email', 'street', 'street2', 'zip_id', 'job_ids', 'partner_id', 'sequence_partner', 'country_id', 'dir_show_name'])
    
            # extraction of all linked jobs
            job_ids = []
            dAddresses = {}
            for address in addresses:
                dAddresses[ address['id'] ] = address
                if address['active'] and address['job_ids']:
                    job_ids.extend(address['job_ids'])
            _add_log(u"%s fonctions liees" % str(len(job_ids)))
            jobs = job_ids.read(['id', 'active', 'fax', 'phone', 'email', 'function_label', 'contact_id', 'address_id', 'sequence_contact', 'sequence_partner', 'answers_ids'])
    
            # extraction of all linked contacts
            cont_ids = []
            dJobs = {}
            for job in jobs:
                dJobs[ job['id'] ] = job
                if job['active'] and job['contact_id'] and not (job['contact_id'][0] in cont_ids):
                    cont_ids.append(job['contact_id'][0])
            _add_log(u"%s personnes liees" % str(len(cont_ids)))
            contacts = cont_ids.read(['id', 'name', 'first_name', 'title', 'lang_id', 'active', 'email', 'mobile', 'login_name', 'token', 'password', 'birthdate', 'job_id', 'job_ids', 'answers_ids', 'job_ids', 'date_passwordsend'])
    
            # STEP SPECIAL : addition of contacts not linked to members mais with token or participating in alter ego
            # extraction of all contacts with forced login-password-token and not yet selected
            other_cont_ids = contact_obj.search([('token', '<>', False), ('forced_login', '=', True), ('id', 'not in', cont_ids)])
            # other_cont_ids = []
            _add_log(u"Nombre de contacts supplementaires (token forced only): %s" % len(other_cont_ids), 'short')

            # extraction of all contacts with emails linked to clubs Alter Ego
            # and also formator linked to the clubs
            club_obj = self.env['cci_club.club']
            participation_state_obj = self.env['cci_club.participation_state']
            participation_obj = self.env['cci_club.participation']
            ae_club_ids = club_obj.search([('type_id', 'in', ALTEREGOTYPES)])
            ae_state_ids = participation_state_obj.search([('name', 'like', '%ACTIVE%')])
            ae_part_all_ids = participation_obj.search([('group_id', 'in', ae_club_ids), ('state_id', 'in', ae_state_ids)])
            ae_parts = ae_part_all_ids.read(['id', 'contact_id', 'email', 'partner_id', 'group_id'])
            ae_cont_ids = []
            for part in ae_parts:
                if part['contact_id'] and len(part['email']) > 5:
                    ae_cont_ids.append(part['contact_id'][0])
                    if part['contact_id'][0] not in other_cont_ids:
                        other_cont_ids.append(part['contact_id'][0])
            ae_clubs = ae_club_ids.read(['formative_id', 'date_begin', 'date_end'])
            added_formatives = 0
            today = time.strftime("%Y-%m-%d")
            for club in ae_clubs:
                if club['date_begin'] and club['date_begin'] <= today and club['formative_id'] and club['formative_id'][0] not in ae_cont_ids:
                    lContinue = False
                    if (club['date_end'] and club['date_end'] > today) or (not club['date_end']):
                        lContinue = True
                    if lContinue:
                        # check if this formative has an personal ou professionnal address
                        format_email = False
                        contact = contact_obj.read([club['formative_id'][0]], ['id', 'email', 'job_ids'])[0]
                        if not contact['email']:
                            format_jobs = job_obj.read(contact['job_ids'], ['id', 'email'])
                            for job in format_jobs:
                                if job['email']:
                                    format_email = job['email']
                        if format_email:
                            ae_cont_ids.append(club['formative_id'][0])
                            added_formatives += 1
                            if club['formative_id'][0] not in other_cont_ids:
                                other_cont_ids.append(club['formative_id'][0])
            _add_log(u"AE: %s" % str(ae_cont_ids))
            _add_log(u"Nombre de contacts supplementaires (token force ou Alter Ego): %s" % len(other_cont_ids))
            _add_log(u"Nombre de formateurs en plus: %s" % added_formatives)
            
            if len(ae_parts) > 0:
                # creation of an excel file with some data and export of this file via FTP on Computerland web site
                # 1. extract of partner and address data
                # ae_clubs = sock.execute(dbname, uid, admin_passwd, 'cci_club.club', 'read', ae_club_ids, ['id','name'] )
                # dae_clubs = {}
                # for ae_club in ae_clubs:
                #    dae_clubs[club['id']] = club
                ae_partner_ids = []
                ae_addr_ids = []
                ae_job_ids = []
                ae_contacts_obj = contact_obj.browse(ae_cont_ids)
                ae_contacts = ae_contacts_obj.read(['id', 'name', 'first_name', 'title', 'job_ids'])
                dae_contacts = {}
                for cont in ae_contacts:
                    dae_contacts[cont['id']] = cont
                    ae_job_ids.extend(cont['job_ids'])

                ae_job_obj = job_obj.browse(ae_job_ids)
                ae_jobs = ae_job_obj.read(['id', 'function_label', 'contact_id', 'address_id'])
                dae_jobs = {}
                for job in ae_jobs:
                    dae_jobs[job['id']] = job
                for part in ae_parts:
                    if part['partner_id'] and not part['partner_id'][0] in ae_partner_ids:
                        ae_partner_ids.append(part['partner_id'][0])
                ae_partners = partner_obj.read(ae_partner_ids, ['id', 'name', 'address', 'activity_description'])
                dae_partners = {}
                for partner in ae_partners:
                    dae_partners[partner['id']] = partner
                    if partner['address']:
                        ae_addr_ids.extend(partner['address'])
                ae_addresses = address_obj.read(ae_addr_ids, ['id', 'street', 'street2', 'zip', 'city'])
                dae_addresses = {}
                for addr in ae_addresses:
                    dae_addresses[addr['id']] = addr
                # 2. output in excel
                wb = Workbook()
                ws = wb.add_sheet('Participants')
                ws.write(0, 0, u'Civilité')
                ws.write(0, 1, u'Nom')
                ws.write(0, 2, u'Prénom')
                ws.write(0, 3, u'Fonction')
                ws.write(0, 4, u'Entreprise')
                ws.write(0, 5, u'Rue')
                ws.write(0, 6, u'Rue2')
                ws.write(0, 7, u'CodePostal')
                ws.write(0, 8, u'Localité')
                ws.write(0, 9, u'Activité')
                ws.write(0, 10, u'Groupe')
                index = 1
                for participant in ae_parts:
                    if participant['contact_id'] and participant['partner_id'] and dae_contacts.has_key(participant['contact_id'][0]) and dae_partners.has_key(participant['partner_id'][0]):
                        # search of the connected address and job
                        contact = dae_contacts[participant['contact_id'][0]]
                        partner = dae_partners[participant['partner_id'][0]]
                        job = address = False
                        if contact['job_ids'] and partner['address']:
                            for job_id in contact['job_ids']:
                                if dae_jobs.has_key(job_id):
                                    job = dae_jobs[job_id]
                                    if job['address_id'] and job['address_id'][0] in partner['address'] and dae_addresses.has_key(job['address_id'][0]):
                                        address = dae_addresses[job['address_id'][0]]
                                        break
                        ws.write(index, 0, contact['title'] or '')
                        ws.write(index, 1, contact['name'] or '')
                        ws.write(index, 2, contact['first_name'] or '')
                        if job:
                            ws.write(index, 3, job['function_label'] or '')
                        ws.write(index, 4, partner['name'] or '')
                        if address:
                            ws.write(index, 5, address['street'] or '')
                            ws.write(index, 6, address['street2'] or '')
                            ws.write(index, 7, address['zip'] or '')
                            ws.write(index, 8, address['city'] or '')
                        ws.write(index, 9, partner['activity_description'] or '')
                        ws.write(index, 10, participant['group_id'][1])
                        index += 1
                wb.save('participants_ae.xls')
                wb = None
                lFiles = ['participants_ae.xls']
                # 3. sending via FTP
                if send_ftp:
                    # FTP_HOST = '212.166.5.117'
                    # FTP_USER = 'ccilv_files'
                    # FTP_PW = 'hid5367cx'
                    # FTP_CWD = 'Alter_Ego'
                    # lFiles = ['participants_ae.xls']
                    # lFiles = []
                    # ftp = ftplib.FTP( FTP_HOST, FTP_USER, FTP_PW )
                    # _add_log('sending of excel file of participer in Alter Ego')
                    # _add_log('------------------------------------------------')
                    # _add_log(ftp.getwelcome())
                    # _add_log(ftp.pwd())
                    # _add_log(ftp.retrlines('LIST'))
                    # _add_log(ftp.cwd( FTP_CWD ))
                    # _add_log(u"Répertoire de placement : " + ftp.pwd())
                    # lErrors = False
                    # for xlsfile in lFiles:
                    #    hFile = open( xlsfile ,'rb')
                    #    result = ftp.storbinary( 'STOR ' + xlsfile, hFile )
                    #    _add_log(result)
                    #    if result[0:3] == '226':
                    #        _add_log(u"Fichier '%s' envoyé correctement" % xlsfile)
                    #        pass
                    #    else:
                    #        lErrors = True
                    #        _add_log(u"Fin de l'envoi - Erreurs : " + result)
                    #        break;
                    #    hFile.close()
                    # if not lErrors:
                    #    _add_log(u"Fin de l'envoi - Tout s'est correctement exécuté")
                    #    pass
                    # ftp.quit()
                    _add_log('sending of excel file of participer in Alter Ego')
                    _add_log('------------------------------------------------')
                    obj_connection = self.env['ftp_connection']
                    ids = obj_connection.search([('internal_code', '=', connection_ae)])
                    if ids and len(ids) == 1:
                        ftp_connection_id = ids[0]
                        ftpserver = obj_connection.connect(ftp_connection_id)
                        if ftpserver:
                            for xlsfile in lFiles:
                                result = obj_connection.upload(ftpserver, xlsfile, xlsfile)
                                _add_log(result)
                            obj_connection.close(ftpserver)
                        else:
                            _add_log(u"Pas de connection FTP possible")
                    else:
                        _add_log(u"Connection inexistante")

            # addition of the others contacts to main contacts
            other_contacts = other_cont_ids.read(['id', 'name', 'first_name', 'title', 'lang_id', 'active', 'email', 'mobile', 'login_name', 'token', 'password', 'birthdate', 'job_id', 'job_ids', 'answers_ids', 'job_ids', 'date_passwordsend'])
            contacts.extend(other_contacts)
            _add_log("Others contact:")

            # extraction of all linked jobs to these others contacts
            other_job_ids = []
            for contact in other_contacts:
                if contact['job_id'] and contact['job_id'][0] not in job_ids:
                    other_job_ids.append(contact['job_id'][0])
            _add_log(u"%s fonctions liees" % str(len(other_job_ids)))
            other_jobs = other_job_ids.read(['id', 'active', 'fax', 'phone', 'email', 'function_label', 'contact_id', 'address_id', 'sequence_contact', 'sequence_partner', 'answers_ids'])
            other_addr_ids = []
            for job in other_jobs:
                dJobs[ job['id'] ] = job
                if job['address_id'] and job['address_id'][0] not in addr_ids:
                    other_addr_ids.append(job['address_id'][0])
            # extraction of all linked addresses
            _add_log(u"%s adresses liees" % str(len(other_addr_ids)))
            other_addresses = other_addr_ids.read(['id', 'active', 'name', 'phone', 'fax', 'email', 'street', 'street2', 'zip_id', 'job_ids', 'partner_id', 'sequence_partner', 'country_id', 'dir_show_name'])
            other_partner_ids = []
            for address in other_addresses:
                dAddresses[ address['id'] ] = address
                if address['partner_id'] and address['partner_id'][0] not in other_partner_ids:
                    other_partner_ids.append(address['partner_id'][0])
            # extraction of linked partners
            _add_log(u"%s partenaires lies" % str(len(other_partner_ids)))
            partners = other_partner_ids.read(['id', 'name', 'title', 'membership_state', 'address', 'vat', 'website', 'user_id'])
            for partner in partners:
                dPartners[ partner['id'] ] = partner

            # extraction of all contact tags for the extraction of the frequency of sending the press review
            # ansd extraction of all private addresses linked to these contacts
            answer_ids = []
            for contact in contacts:
                if contact['answers_ids']:
                    answer_ids.extend(contact['answers_ids'])
            #
            answers = answer_ids.read(['id', 'text', 'question_id'])
            dAnswers = {}
            for answer in answers:
                dAnswers[ answer['id'] ] = answer
            #
            private_address_ids = address_obj.search(['|', ('partner_id', '=', 2), ('partner_id', '=', False)])
            private_addresses = private_address_ids.read(['id', 'street', 'street2', 'zip_id', 'phone', 'fax', 'job_ids', 'country_id', 'dir_show_name'])
            _add_log(u"%s adresses privees" % len(private_address_ids))

            dictPrivateAddresses = {}
            private_job_ids = []
            for address in private_addresses:
                if address['job_ids']:
                    dictPrivateAddresses[ address['id'] ] = address
                    private_job_ids.extend(address['job_ids'])
            private_jobs = private_job_ids.read(['id', 'address_id'])
            dictPrivateJobs = {}
            for job in private_jobs:
                dictPrivateJobs[ job['id'] ] = job
            _add_log(u"%s jobs prives lies" % len(private_job_ids))
            # view the collected data
            actives = 0
            emails = 0
            logins = 0
            for contact in contacts:
                if contact['active']:
                    actives += 1
                    if contact['email']:
                        emails += 1
                        if contact['login_name']:
                            logins += 1
            _add_log(u"Sur ces personnes, %s sont actives" % actives)
            _add_log(u"Sur ces %s personnes actives, %s ont une adresse email" % (actives, emails))
            _add_log(u"Sur ces %s personnes actives et avec emails, %s ont deja un login" % (emails, logins))
            
            if create_new_login:
                # CREATION OF LOGIN/PASSWORD/TOKEN IF EMPTY LOGIN_NAME
                queue_obj = self.env['cci_newsletter.queue_new']
                iNewData = 0
                for contact in contacts:
                    # Recherche de l'adresse email qui sera utilisée
                    # search the first linked job with email to a member in order of sequence_contact
                    first_id = 0
                    first_seq = 9999
                    for job_id in contact['job_ids']:
                        if dJobs.has_key(job_id):
                            job = dJobs[ job_id ]
                        else:
                            job = job_obj.read([job_id], ['id', 'active', 'fax', 'phone', 'email', 'function_label', 'contact_id', 'address_id', 'sequence_contact', 'sequence_partner', 'answers_ids'])[0]
                            dJobs[ job_id ] = job
                        if (job['contact_id'][0] == contact['id']) and job['email'] and (job['sequence_contact'] < first_seq):
                            if job['address_id'] and dAddresses.has_key(job['address_id'][0]):
                                addr = dAddresses[ job['address_id'][0] ]
                                if addr['partner_id'] and dPartners.has_key(addr['partner_id'][0]):
                                    first_id = job['id']
                                    first_seq = job['sequence_contact']
                    if first_id > 0:
                        job = dJobs[ first_id ]
                        lJob = True
                    else:
                        lJob = False
                    if not lJob:
                        # search the first linked job with email in order of sequence_contact
                        first_id = 0
                        first_seq = 9999
                        for job in jobs:
                            if (job['contact_id'][0] == contact['id']) and job['email'] and (job['sequence_contact'] < first_seq):
                                first_id = job['id']
                                first_seq = job['sequence_contact']
                        if first_id > 0:
                            job = dJobs[ first_id ]
                            # get the address and partner data
                            if job['address_id'] and not dAddresses.has_key(job['address_id'][0]):
                                newaddr = address_obj.read([job['address_id'][0]], ['id', 'active', 'name', 'phone', 'fax', 'email', 'street', 'street2', 'zip_id', 'job_ids', 'partner_id', 'sequence_partner', 'country_id', 'dir_show_name'])
                                dAddresses[ job['address_id'][0] ] = newaddr[0]
                                if newaddr['partner_id'] and not dPartners.has_key(newaddr['partner_id'][0]):
                                    newpartner = partner.read([newaddr['partner_id'][0]], ['id', 'name', 'title', 'membership_state', 'address', 'vat', 'website', 'user_id'])
                                    dPartners[ newaddr['partner_id'][0] ] = newpartner[0]
                            lJob = True
                        else:
                            lJob = False
                    current_email = ''
                    if lJob:
                        # construction of the used email
                        if job['email'] and job['email'].lower().strip() not in published_emails:
                            current_email = job['email'].lower().strip()
                            email_source = 'job'
                        else:
                            if contact['email'] and contact['email'].lower().strip() not in published_emails:
                                current_email = contact['email'].lower().strip()
                                email_source = 'contact'
                            else:
                                current_email = ''
                                email_source = 'none'
                                lJob = False
                    else:
                        if contact['email'] and contact['email'].lower().strip() not in published_emails:
                            current_email = contact['email'].lower().strip()
                            email_source = 'contact'
                        else:
                            current_email = ''
                            email_source = 'none'
                    login_created = False
                    if current_email and not contact['login_name']:
                        current_try = 0
                        both_ok = False
                        while not both_ok:
                            if current_try == 0:
                                contact['login_name'] = current_email
                            else:
                                _add_log(u"Login ou token déjà existant, je réessayes un autre ... (%s)" % str(current_try))
                                contact['login_name'] = current_email + "_" + str(current_try)
                            if contact['name'] and contact['first_name']:
                                contact['password'] = _convertCP850(contact['name'][0:2].lower() + str(int(random.random() * 1000000)).rjust(6, '0') + contact['first_name'][0:2].lower())
                            else:
                                if contact['name'] and len(contact['name']) > 3:
                                    contact['password'] = _convertCP850(contact['name'][0:2].lower() + str(int(random.random() * 1000000)).rjust(6, '0') + contact['name'][2:4].lower())
                                else:
                                    contact['password'] = _convertCP850(contact['name'][0:2].lower() + str(int(random.random() * 1000000)).rjust(6, '0') + 'am')
                            if not contact['password'].isalpha():
                                contact['password'] = contact['password'].replace('.', '_').replace('-', '_')
                            contact['token'] = hex(random.getrandbits(128))[2:34]
                            # vérification que ce token et ce login n'existent pas déjà dans la base de données
                            # pour ne pas créer de doublons
                            verif_ids = contact_obj.search(['|', ('login_name', '=', contact['login_name']), ('token', '=', contact['token'])])
                            verif2_ids = subscriber_obj.search(['|', ('login_name', '=', contact['login_name']), ('token', '=', contact['token'])])
                            both_ok = (len(verif_ids) == 0 and len(verif2_ids) == 0)
                            current_try += 1 
                        
                        # recording of this new data in the database
                        newvalues = {'login_name':contact['login_name'], 'password':contact['password'], 'token':contact['token']}
                        result = contact_obj.write(contact['id'], newvalues)
                        iNewData += 1
                        login_created = True

                        # in the list of jobs, check if a job is linked to a private address
                        # private_address = False
                        # if contact['job_ids']:
                        #    for job_id in contact['job_ids']:
                        #        if dictPrivateJobs.has_key( job_id ):
                        #            if dictPrivateAddresses.has_key( dictPrivateJobs[ job_id ]['address_id'][0] ):
                        #                private_address = dictPrivateAddresses[ dictPrivateJobs[ job_id ]['address_id'][0] ]
                        #                print u"Adresse privee trouvee"

                    if current_email and (login_created or not contact['date_passwordsend']):
                        if lJob:
                            if job['address_id']:
                                if not dAddresses.has_key(job['address_id'][0]):
                                    address = addressobj.read([job['address_id'][0]], ['id', 'active', 'name', 'phone', 'fax', 'email', 'street', 'street2', 'zip_id', 'job_ids', 'partner_id', 'sequence_partner', 'country_id', 'dir_show_name'])[0]
                                    dAddresses[ job['address_id'][0] ] = address
                                else:
                                    address = dAddresses[ job['address_id'][0] ]
                                if address['partner_id']:
                                    if not dPartners.has_key(address['partner_id'][0]):
                                        partner = partnerobj.read([address['partner_id'][0]], ['id', 'name', 'title', 'membership_state', 'address', 'vat', 'website', 'user_id'])[0]
                                        dPartners[ address['partner_id'][0] ] = partner
                                    else:
                                        partner = dPartners[ address['partner_id'][0] ]
                                else:
                                    partner = False
                            else:
                                address = False
                                partner = False
                        newrecord = {}
                        newrecord['date'] = datetime.now().strftime("%Y-%m-%d")
                        newrecord['mail'] = _clean_CR(current_email)
                        newrecord['name'] = contact['name'] or ''
                        newrecord['first_name'] = contact['first_name'] or ''
                        newrecord['login'] = _clean_CR(contact['login_name'] or '')
                        newrecord['password'] = contact['password'] or ''
                        newrecord['token'] = contact['token'] or ''
                        newrecord['courtesy'] = (contact['title'] or 'Monsieur')
                        if lJob:
                            newrecord['function'] = job['function_label'] or ''
                            if partner:
                                newrecord['company'] = partner['name'] or ''
                                if partner['user_id']:
                                    newrecord['user_id'] = partner['user_id'][0]
                        newrecord['contact_id'] = contact['id']
                        newrecord['active'] = True
                        queue_obj.create(newrecord)
                        # _add_log(u"New Token : '%s'" % contact['token'])
                if iNewData > 0:
                    _add_log(u"Nous avons donc cree %s logins-passwords-tokens." % (str(iNewData)), 'short')
                    pass
                else:
                    _add_log(u"Aujourd'hui, nous n'avons cree aucun nouveau logins-passwords-tokens", 'short')
                    pass
                log_count_new_users = iNewData

            # reading of tables zipcodes and countries
            # code_ids = zip_obj.search(cr,uid,[])
            # _add_log(u"%s codes postaux trouves" % str(len(code_ids)))
            # zips = zip_obj.read(cr,uid,code_ids,['id','name','city'])
            # dZipCodes = {}
            # for zip in zips:
            #    dZipCodes[ zip['id'] ] = zip
            #
            code_ids = country_obj.search([])
            _add_log(u"%s pays trouves" % str(len(code_ids)))
            countries = country_obj.read(code_ids, ['id', 'code'])
            dCountries = {}
            for country in countries:
                dCountries[ country['id'] ] = country

            # Creation of cvs file
            # job_obj = self.pool.get('res.partner.job')
            done = 0
            hfUser = open('users.csv' , 'w')
            hfCSV = csv.writer(hfUser, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
            hfCSV.writerow(['contact_id', 'job_id', 'address_id', 'partner_id', 'language', 'courtesy_transl', 'name', 'firstname', 'login', 'password', 'token', 'email', 'birthdate', 'phone_contact', 'fax_contact', 'mobile_contact', 'function', 'addr_contact', 'zipcode_contact', 'city_contact', 'country_contact', 'area', 'right_modify', 'company', 'phone_company', 'fax_company', 'email_company', 'website', 'num_entrep', 'addr_company', 'zipcode_company', 'city_company', 'country_company', 'rdp1', 'rdp2', 'rdp3', 'rdp4', 'rdp5', 'source_email', 'member'])
            #
            hfOut = open('interests.csv' , 'w')
            hfCSVInt = csv.writer(hfOut, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
            hfCSVInt.writerow(['id', 'name', 'visible'])
            for type in types_of_event:
                csvrecord = []
                csvrecord.append(2000 + type[0])
                csvrecord.append(('Type of Event - ' + (type[1] or '')).encode("cp1252"))
                csvrecord.append(0)
                hfCSVInt.writerow(csvrecord)
            for event_mi in events_mi:
                csvrecord = []
                csvrecord.append(3000 + event_mi[0])
                csvrecord.append(('Event - ' + (event_mi[1] or '')))  # # déjà encodé 1252
                csvrecord.append(0)
                hfCSVInt.writerow(csvrecord)
            hfCSVInt.writerow([4000, 'Participants Alter Ego'.encode('cp1252'), 0])
            hfOut.close()
            #
            hfOut = open('links.csv' , 'w')
            hfCSVLink = csv.writer(hfOut, delimiter=";", quotechar='"', quoting=csv.QUOTE_NONNUMERIC, lineterminator='\n')
            hfCSVLink.writerow(['contact_id', 'interest_id'])
            for contact in contacts:
                if contact['active'] and contact['id'] not in published_ids:
                    if contact['token'] and contact['token'] not in published_tokens:
                        if contact['login_name'] and contact['login_name'].lower().strip() not in EXCLUDED_LOGINS and contact['login_name'] not in published_logins:
                            
                            # search the first linked job to a member in order of sequence_contact
                            first_id = 0
                            first_seq = 9999
                            for job_id in contact['job_ids']:
                                if dJobs.has_key(job_id):
                                    job = dJobs[ job_id ]
                                else:
                                    job_rec = job_obj.browse(job_id)
                                    job = job_rec.read(['id', 'active', 'fax', 'phone', 'email', 'function_label', 'contact_id', 'address_id', 'sequence_contact', 'sequence_partner', 'answers_ids'])
                                    dJobs[ job_id ] = job
                                if (job['contact_id'][0] == contact['id']) and (job['sequence_contact'] < first_seq):
                                    if job['address_id'] and dAddresses.has_key(job['address_id'][0]):
                                        addr = dAddresses[ job['address_id'][0] ]
                                        if addr['partner_id'] and dPartners.has_key(addr['partner_id'][0]):
                                            partner = dPartners[addr['partner_id'][0]]
                                            if partner['membership_state'] in ['free', 'invoiced', 'paid']:
                                                first_id = job_id
                                                first_seq = job['sequence_contact']
                            if first_id > 0:
                                job = dJobs[ first_id ]
                                lJob = True
                            else:
                                lJob = False
                            if not lJob:
                                # search the first linked job, address, partner in order of sequence_contact
                                first_id = 0
                                first_seq = 9999
                                for job_id in contact['job_ids']:
                                    if dJobs.has_key(job_id):
                                        job = dJobs[ job_id ]
                                    else:
                                        job = job_obj.read([job_id], ['id', 'active', 'fax', 'phone', 'email', 'function_label', 'contact_id', 'address_id', 'sequence_contact', 'sequence_partner', 'answers_ids'])[0]
                                        dJobs[ job_id ] = job[0]
                                    if job['sequence_contact'] < first_seq:
                                        if job['address_id']:
                                            if not dAddresses.has_key(job['address_id'][0]):
                                                newaddr = address_obj.read([job['address_id'][0]], ['id', 'active', 'name', 'phone', 'fax', 'email', 'street', 'street2', 'zip_id', 'job_ids', 'partner_id', 'sequence_partner', 'country_id', 'dir_show_name'])[0]
                                                dAddresses[ job['address_id'][0] ] = newaddr
                                            else:
                                                newaddr = dAddresses[job['address_id'][0]]
                                            if newaddr['partner_id']:
                                                if not dPartners.has_key(newaddr['partner_id'][0]):
                                                    newpartner = partner_obj.read([newaddr['partner_id'][0]], ['id', 'name', 'title', 'membership_state', 'address', 'vat', 'website', 'user_id'])[0]
                                                    dPartners[ newaddr['partner_id'][0] ] = newpartner
                                                first_id = job_id
                                                first_seq = job['sequence_contact']
                                if first_id > 0:
                                    job = dJobs[ first_id ]
                                    # get the address and partner data
                                    if job['address_id'] and not dAddresses.has_key(job['address_id'][0]):
                                        newaddr = address_job.read([job['address_id'][0]], ['id', 'active', 'name', 'phone', 'fax', 'email', 'street', 'street2', 'zip_id', 'job_ids', 'partner_id', 'sequence_partner', 'country_id', 'dir_show_name'])[0]
                                        dAddresses[ job['address_id'][0] ] = newaddr
                                        if newaddr['partner_id'] and not dPartners.has_key(newaddr['partner_id'][0]):
                                            newpartner = partner_obj.read([newaddr[0]['partner_id'][0]], ['id', 'name', 'title', 'membership_state', 'address', 'vat', 'website', 'user_id'])[0]
                                            dPartners[ newaddr['partner_id'][0] ] = newpartner
                                    lJob = True
                                else:
                                    lJob = False
                            if lJob:
                                # construction of the used email
                                if job['email'] and job['email'].lower().strip() not in published_emails:
                                    current_email = job['email'].lower().strip()
                                    email_source = 'job'
                                else:
                                    if contact['email'] and contact['email'].lower().strip() not in published_emails:
                                        current_email = contact['email'].lower().strip()
                                        email_source = 'contact'
                                    else:
                                        lJob = False
                            if lJob:
                                # in the list of jobs, check if a job is linked to a private address
                                private_address = False
                                if contact['job_ids']:
                                    for job_id in contact['job_ids']:
                                        if dictPrivateJobs.has_key(job_id):
                                            if dictPrivateAddresses.has_key(dictPrivateJobs[ job_id ]['address_id'][0]):
                                                private_address = dictPrivateAddresses[ dictPrivateJobs[ job_id ]['address_id'][0] ]
                                if job['address_id'] and dAddresses.has_key(job['address_id'][0]):
                                    address = dAddresses[ job['address_id'][0] ]
                                    if address['partner_id'] and dPartners.has_key(address['partner_id'][0]):
                                        partner = dPartners[ address['partner_id'][0] ]
                                        csvrecord = []
                                        csvrecord.append(contact['id'])
                                        published_ids.append(contact['id'])
                                        csvrecord.append(job['id'])
                                        csvrecord.append(address['id'])
                                        csvrecord.append(partner['id'])
                                        if contact['lang_id']:
                                            if contact['lang_id'][0] == 3:
                                                # NL
                                                csvrecord.append(2)
                                            elif contact['lang_id'][0] == 2:
                                                # DE
                                                csvrecord.append(4)
                                            elif contact['lang_id'][0] == 1:
                                                # EN
                                                csvrecord.append(3)
                                            else:
                                                # FR
                                                csvrecord.append(1)
                                        else:
                                            # FR
                                            csvrecord.append(1)
                                        csvrecord.append((contact['title'] or '.').encode("cp1252"))
                                        csvrecord.append((contact['name'] or '(inconnu)').encode("cp1252"))
                                        csvrecord.append((contact['first_name'] or '(inconnu)').encode("cp1252"))
                                        csvrecord.append(_clean_CR(contact['login_name'] or '').encode("cp1252"))
                                        published_logins.append(contact['login_name'])
                                        csvrecord.append((contact['password'] or '').encode("cp1252"))
                                        csvrecord.append((contact['token'] or '').encode("cp1252"))
                                        published_tokens.append(contact['token'])
                                        csvrecord.append(_clean_CR(current_email).encode("cp1252"))
                                        published_emails.append(current_email)
                                        if contact['birthdate']:
                                            csvrecord.append(contact['birthdate'].replace('-', '').encode("cp1252"))
                                        else:
                                            csvrecord.append('')
                                        csvrecord.append(_clean_CR(job['phone'] or '').encode("cp1252"))
                                        csvrecord.append(_clean_CR(job['fax'] or '').encode("cp1252"))
                                        csvrecord.append(_clean_CR(contact['mobile'] or '').encode("cp1252"))
                                        csvrecord.append(_clean_CR(job['function_label'] or '').encode("cp1252"))
                                        if private_address:
                                            csvrecord.append((_clean_CR(private_address['street'] or '') + " " + _clean_CR(private_address['street2'] or '')).encode("cp1252"))
                                            if private_address['zip_id']:
                                                private_zip_code = dZips[ private_address['zip_id'][0] ]
                                                csvrecord.append((private_zip_code['name'] or '').encode("cp1252"))
                                                csvrecord.append((private_zip_code['city'] or '').encode("cp1252"))
                                            else:
                                                csvrecord.append('')
                                                csvrecord.append('')
                                            if private_address['country_id']:
                                                csvrecord.append((dCountries[ private_address['country_id'][0] ]['code'] or '').encode("cp1252"))
                                            else:
                                                csvrecord.append('')
                                        else:
                                            csvrecord.append('')
                                            csvrecord.append('')
                                            csvrecord.append('')
                                            csvrecord.append('')
                                        if address['zip_id'] and address['zip_id'][1][0:1] == '5':
                                            csvrecord.append(2)
                                        else:
                                            csvrecord.append(1)
                                        # # 0 = False; 1 =True
                                        if job['answers_ids'] and 4922 in job['answers_ids']:
                                            csvrecord.append(1) 
                                        else:
                                            csvrecord.append(0)
                                        if address['dir_show_name']:
                                            full_name = address['dir_show_name']
                                        else:
                                            full_name = _get_name_and_suffix(address['name'] or '' , partner['name'] or '')[0]
                                        csvrecord.append(full_name.encode("cp1252"))
                                        csvrecord.append(_clean_CR(address['phone'] or '').encode("cp1252"))
                                        csvrecord.append(_clean_CR(address['fax'] or '').encode("cp1252"))
                                        csvrecord.append(_clean_CR(address['email'] or '').lower().strip().encode("cp1252"))
                                        csvrecord.append(_clean_CR(partner['website'] or '').encode("cp1252"))
                                        csvrecord.append(_clean_CR(partner['vat'] or '').encode("cp1252"))
                                        if address['street'] and address['street2']:
                                            csvrecord.append(_clean_CR(address['street'] + ' - ' + address['street2']).encode("cp1252"))
                                        elif address['street']:
                                            csvrecord.append(_clean_CR(address['street']).encode("cp1252"))
                                        else:
                                            csvrecord.append(_clean_CR(address['street2'] or '').encode("cp1252"))
                                        if address['zip_id'] and dZips.has_key(address['zip_id'][0]):
                                            csvrecord.append((dZips[ address['zip_id'][0] ]['name'] or '').encode("cp1252"))
                                            csvrecord.append((dZips[ address['zip_id'][0] ]['city'] or '').encode("cp1252"))
                                        else:
                                            csvrecord.append('')
                                            csvrecord.append('')
                                        if address['country_id'] and dCountries.has_key(address['country_id'][0]):
                                            csvrecord.append((dCountries[ address['country_id'][0] ]['code'] or '').encode("cp1252"))
                                        else:
                                            csvrecord.append('BE')
                                        #
                                        frequency = '11111'
                                        for answer_id in contact['answers_ids']:
                                            if dAnswers.has_key(answer_id):
                                                if dAnswers[ answer_id ]['question_id'][0] == 88:
                                                    frequency = dAnswers[ answer_id ]['text'] and (dAnswers[ answer_id ]['text'].ljust(5, '0')) or '00000'
                                        csvrecord.append(frequency[0])
                                        csvrecord.append(frequency[1])
                                        csvrecord.append(frequency[2])
                                        csvrecord.append(frequency[3])
                                        csvrecord.append(frequency[4])
                                        csvrecord.append(email_source)
                                        if partner['membership_state'] in ['free', 'invoiced', 'paid']:
                                            csvrecord.append(1)
                                        else:
                                            csvrecord.append(0)
                                        hfCSV.writerow(csvrecord)
                                        
                                        # mark the registration of this user in events and event_types as marks of interest
                                        user_event_types = []
                                        part_event_ids = reg_obj.search([('contact_id', '=', contact['id']), ('event_id', 'in', event_mi_ids)])
                                        if part_event_ids:
                                            part_events = reg_obj.read(part_event_ids, ['event_id'])
                                            for part_event in part_events:
                                                hfCSVLink.writerow([contact['id'], 3000 + part_event['event_id'][0]])
                                                if dEvents.has_key(part_event['event_id'][0]):
                                                    type_of_event_id = dEvents[part_event['event_id'][0]]
                                                    if type_of_event_id not in user_event_types:
                                                        hfCSVLink.writerow([contact['id'], type_of_event_id])
                                        # mark the participation of this contact in alter ego clubs
                                        if contact['id'] in ae_cont_ids:
                                            hfCSVLink.writerow([contact['id'], 4000])
                                        done += 1
                        else:
                            if contact['login_name'] and not (contact['login_name'].lower().strip() in EXCLUDED_LOGINS):
                                _add_log(u"Login en double dans OpenERP : " + contact['login_name'], 'short')
                                pass
                    else:
                        if contact['token']:
                            _add_log(u"Token en double dans OpenERP : " + contact['token'], 'short')
                            pass

            # get back other CCIs data
            sub_source_obj = self.env['cci_newsletter.source']
            sub_source_ids = sub_source_obj.search([])
            sub_sources = sub_source_ids.read(['id', 'default_area'])
            dSubSources = {}
            for sub_source in sub_sources:
                dSubSources[sub_source['id']] = sub_source['default_area']
            subscriber_ids = subscriber_obj.search(['|', ('expire', '>', time.strftime('%Y-%m-%d')), ('expire', '=', False)])
            subscribers = subscriber_ids.read(['internal_id', 'name', 'first_name', 'forced_area', 'email', 'company_name', 'login_name', 'password', 'token', 'source_id'])
            for line in subscribers:
                if line['email'] and line['email'].lower().strip() not in published_emails:
                    if line['token'] and line['token'] not in published_tokens:
                        if line['login_name'] and line['login_name'] not in published_logins:
                            csvrecord = []
                            csvrecord.append(line['internal_id'])
                            csvrecord.append(0)
                            csvrecord.append(0)
                            csvrecord.append(0)
                            csvrecord.append(1)  # lang
                            csvrecord.append('.')
                            csvrecord.append((line['name'] or '(inconnu)').encode('cp1252'))
                            csvrecord.append((line['first_name'] or '(inconnu)').encode('cp1252'))
                            csvrecord.append((line['login_name'] or '').encode('cp1252'))
                            published_logins.append(line['login_name'])
                            csvrecord.append((line['password'] or 'nopassword').encode('cp1252'))
                            csvrecord.append((line['token'] or '').encode('cp1252'))
                            published_tokens.append(line['token'])
                            csvrecord.append((line['email'].lower().strip() or '').encode('cp1252'))
                            published_emails.append(line['email'].lower().strip())
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            if line['forced_area']:
                                csvrecord.append(line['forced_area'])
                            else:
                                if line['source_id'] and dSubSources.has_key(line['source_id'][0]) and dSubSources[line['source_id'][0]]:
                                    csvrecord.append(dSubSources[line['source_id'][0]])
                                else:
                                    csvrecord.append(0)
                            csvrecord.append(0)
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('BE')
                            frequency = '11111'
                            csvrecord.append(frequency[0])
                            csvrecord.append(frequency[1])
                            csvrecord.append(frequency[2])
                            csvrecord.append(frequency[3])
                            csvrecord.append(frequency[4])
                            if line['source_id']:
                                csvrecord.append(line['source_id'][1].encode('cp1252'))
                            else:
                                csvrecord.append('Inscrits sans source'.encode('cp1252'))
                            csvrecord.append(0)
                            hfCSV.writerow(csvrecord)
                            done += 1
                        else:
                            _add_log(u"Login en double dans 'inscrits' : " + line['login_name'], 'short')
                            pass
                    else:
                        _add_log(u"Token en double dans 'inscrits' : " + line['token'], 'short')
                        pass
                else:
                    _add_log(u"Email en double dans 'inscrits' : " + line['email'].lower().strip(), 'short')
                    pass

            if include_prospects:
                # PART 4 : Extraction of current prospects for the duration of the prospection
                #          Askey by Pierre Neuray on June 2012
                # Extraction of current_prospects creaated by the wizard get_ppi.py of module cci_magazine
                # the prospects are considered asking for a daily 'revue de presse'
                # By default, we send them the 'revue de presse' daily, but it's possible to manage
                # that default personaly throught OpenERP
                CURRENT_PROSPECT = 'Prospect en cours'
                DEFAULT_SUBSCRIPTION_FREQ = '11111'
                # the prospects can exists in job or address, we extract first jobs because there are more 'precise'
                # than addresses, on 'personal' data and we can extract the data in case of same email address
                # on address than on job
                selection = """SELECT contact.id, job.id, address.id, partner.id, contact.title, contact.name, contact.first_name, 
                                      contact.login_name, contact.password, contact.token, contact.email, contact.birthdate,
                                      job.phone, job.fax, contact.mobile, job.function_label, partner.name, address.phone,
                                      address.fax, address.email, partner.website, partner.vat, address.name, 
                                      address.street, address.street2, address.zip_id, contact.lang_id, job.email, 
                                      address.dir_show_name, address.country_id
                                FROM res_partner_job as job, res_partner_contact as contact,
                                     res_partner_address as address, res_partner as partner
                                WHERE job.active and job.magazine_subscription_source = 'Prospect en cours'
                                      and job.email is not null
                                      and job.contact_id = contact.id and job.address_id = address.id 
                                      and address.partner_id = partner.id and contact.active 
                                      and address.active  and partner.active
                            """
                cr.execute(selection)
                jobs = cr.fetchall()
                if jobs:
                    # reading of all possible specific daily subscription for these prospects
                    # these daily subscription must be recorded manually in OpenERP
                    # because the prospects don't have access to thier profile in Web Site
                    # but this is possible
                    contact_ids = []
                    for job in jobs:
                        contact_ids.append(str(job[0]))
                    str_contact_ids = ','.join(contact_ids)
                    selection = """SELECT rel.contact, answer.text 
                                    FROM contact_question_rel as rel, crm_profiling_answer as answer
                                    WHERE answer.question_id = 88 and rel.answer = answer.id and contact in (%s);""" % str_contact_ids
                    cr.execute(selection)
                    answers = cr.fetchall()
                    dAnswers = {}
                    for answer in answers:
                        dAnswers[answer[0]] = answer[1]
                    obj_subscriber = self.env['cci_newsletter.subscriber']
                    obj_contact = self.env['res.partner.contact']
                    count_prospects = 0
                    for job in jobs:

                        current_email = False
                        if job[10]:
                            current_email = job[10]
                        else:
                            if job[27]:
                                current_email = job[27]
                        if current_email and current_email not in published_emails:
                            # we check if we must create login, token or password for the linked contact
                            current_login = job[7]
                            current_pw = job[8]
                            current_token = job[9]
                            new_value_contact = {}
                            if not job[7]:  # pas de login_name unique
                                exists = True
                                current_try = 0
                                while exists:
                                    if current_try == 0:
                                        new_login = current_email
                                    else:
                                        new_login = current_email + "_" + str(current_try)
                                    # check if this login already exist in this table or in res.partner.contact
                                    search_result = obj_subscriber.search([('login_name', '=', new_login)])
                                    if not search_result:
                                        search_result = obj_contact.search([('login_name', '=', new_login)])
                                        if not search_result:
                                            exists = False
                                    current_try += 1
                                new_value_contact['login_name'] = new_login
                                current_login = new_login
                            if not job[8]:  # pas de password
                                if job[5] and job[6]:
                                    new_pw = _convertCP850(job[5][0:2].lower() + str(int(random.random() * 1000000)).rjust(6, '0') + job[6][0:2].lower())
                                else:
                                    if job[5] and len(job[5]) > 3:
                                        new_pw = _convertCP850(job[5][0:2].lower() + str(int(random.random() * 1000000)).rjust(6, '0') + job[5][2:4].lower())
                                    else:
                                        new_pw = _convertCP850(job[5][0:2].lower() + str(int(random.random() * 1000000)).rjust(6, '0') + 'am')
                                if not new_pw.isalpha():
                                    new_pw = new_pw.replace('.', '_').replace('-', '_').replace("'", "_")
                                new_value_contact['password'] = new_pw
                                current_pw = new_pw
                            if not job[9]:  # pas de token unique
                                exists = True
                                while exists:
                                    new_token = hex(random.getrandbits(128))[2:34]
                                    # check if this login already exist in this table or in res.partner.contact
                                    search_result = obj_subscriber.search([('token', '=', new_token)])
                                    if not search_result:
                                        search_result = obj_contact.search([('token', '=', new_token)])
                                        if not search_result:
                                            exists = False
                                new_value_contact['token'] = new_token
                                current_token = new_token
                            if new_value_contact:
                                obj_contact.write(job[0], new_value_contact)
                            # writing of this prospect in users.csv
                            if current_token not in published_tokens and current_login not in published_logins:
                                csvrecord = []
                                csvrecord.append(job[0])
                                published_ids.append(job[0])
                                csvrecord.append(job[1])
                                csvrecord.append(job[2])
                                csvrecord.append(job[3])
                                if job[26]:
                                    if job[26] == 3:
                                        # NL
                                        csvrecord.append(2)
                                    elif job[26] == 2:
                                        # DE
                                        csvrecord.append(4)
                                    elif job[26] == 1:
                                        # EN
                                        csvrecord.append(3)
                                    else:
                                        # FR
                                        csvrecord.append(1)
                                else:
                                    # FR
                                    csvrecord.append(1)
                                csvrecord.append((job[4] or '.').encode("cp1252"))
                                csvrecord.append((job[5] or '(inconnu)').encode("cp1252"))
                                csvrecord.append((job[6] or '(inconnu)').encode("cp1252"))
                                csvrecord.append(_clean_CR(current_login or '').encode("cp1252"))
                                published_logins.append(current_login)
                                csvrecord.append((current_pw or '').encode("cp1252"))
                                csvrecord.append((current_token or '').encode("cp1252"))
                                published_tokens.append(current_token)
                                csvrecord.append(_clean_CR(current_email).encode("cp1252"))
                                published_emails.append(current_email)
                                if job[11]:
                                    csvrecord.append(job[11].replace('-', '').encode("cp1252"))
                                else:
                                    csvrecord.append('')
                                csvrecord.append(_clean_CR(job[12] or '').encode("cp1252"))
                                csvrecord.append(_clean_CR(job[13] or '').encode("cp1252"))
                                csvrecord.append(_clean_CR(job[14] or '').encode("cp1252"))
                                csvrecord.append(_clean_CR(job[15] or '').encode("cp1252"))
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                # HERE
                                current_zip = False
                                if job[25] and job[25] in dZips:
                                    current_zip = dZips[job[25]]
                                    if current_zip['name'][0:1] == '5':
                                        csvrecord.append(2)
                                    else:
                                        csvrecord.append(1)
                                else:
                                    csvrecord.append(1)
                                csvrecord.append(0)
                                if job[28]:
                                    full_name = job[28]
                                else:
                                    full_name = _get_name_and_suffix(job[22] or '' , job[16] or '')[0]
                                csvrecord.append(full_name.encode("cp1252"))
                                csvrecord.append(_clean_CR(job[17] or '').encode("cp1252"))
                                csvrecord.append(_clean_CR(job[18] or '').encode("cp1252"))
                                csvrecord.append(_clean_CR(job[19] or '').lower().strip().encode("cp1252"))
                                csvrecord.append(_clean_CR(job[20] or '').encode("cp1252"))
                                csvrecord.append(_clean_CR(job[21] or '').encode("cp1252"))
                                if job[23] and job[24]:
                                    csvrecord.append(_clean_CR(job[23] + ' - ' + job[24]).encode("cp1252"))
                                elif job[23]:
                                    csvrecord.append(_clean_CR(job[23]).encode("cp1252"))
                                else:
                                    csvrecord.append(_clean_CR(job[24] or '').encode("cp1252"))
                                if current_zip:
                                    csvrecord.append((current_zip['name'] or '').encode("cp1252"))
                                    csvrecord.append((current_zip['city'] or '').encode("cp1252"))
                                else:
                                    csvrecord.append('')
                                    csvrecord.append('')
                                if job[29] and dCountries.has_key(job[29]):
                                    csvrecord.append((dCountries[ job[29] ]['code'] or '').encode("cp1252"))
                                else:
                                    csvrecord.append('BE')
                                #
                                if dAnswers.has_key(job[0]):
                                    frequency = dAnswers[ job[0] ]
                                    if len(frequency) < 5:
                                        frequency = frequency.rjust(5, '0')
                                else:
                                    frequency = DEFAULT_SUBSCRIPTION_FREQ
                                csvrecord.append(frequency[0])
                                csvrecord.append(frequency[1])
                                csvrecord.append(frequency[2])
                                csvrecord.append(frequency[3])
                                csvrecord.append(frequency[4])
                                csvrecord.append('prospect_job')
                                csvrecord.append(0)
                                hfCSV.writerow(csvrecord)
                                count_prospects += 1
                # the prospects can exists in job or address, we extract first jobs because there are more 'precise'
                # than addresses, on 'personal' data and we can extract the data in case of same email address
                # on address than on job
                selection = """SELECT address.id, partner.id, partner.name, address.phone,
                                      address.fax, address.email, partner.website, partner.vat, address.name, 
                                      address.street, address.street2, address.zip_id, address.dir_show_name, address.country_id
                                FROM res_partner_address as address, res_partner as partner
                                WHERE address.magazine_subscription_source = 'Prospect en cours'
                                      and address.email is not null and address.partner_id = partner.id
                                      and address.active
                            """
                cr.execute(selection)
                addrs = cr.fetchall()
                if addrs:
                    obj_subscriber = self.env['cci_newsletter.subscriber']
                    obj_contact = self.env['res.partner.contact']
                    for addr in addrs:

                        current_email = False
                        if addr[5]:
                            current_email = addr[5]
                        if current_email and current_email not in published_emails:
                            # we create temporary unique login, token or password for the linked email
                            current_login = False
                            current_pw = False
                            current_token = False
                            # temporary unique login_name
                            exists = True
                            current_try = 0
                            while exists:
                                if current_try == 0:
                                    new_login = current_email
                                else:
                                    new_login = current_email + "_" + str(current_try)
                                # check if this login already exist in this table or in res.partner.contact
                                search_result = obj_subscriber.search([('login_name', '=', new_login)])
                                if not search_result:
                                    search_result = obj_contact.search([('login_name', '=', new_login)])
                                    if not search_result:
                                        exists = False
                                current_try += 1
                            current_login = new_login
                            # temporary password
                            current_pw = 'temporary'
                            # temporary unique token
                            exists = True
                            while exists:
                                new_token = hex(random.getrandbits(128))[2:34]
                                # check if this token already exist in this table or in res.partner.contact
                                search_result = obj_subscriber.search([('token', '=', new_token)])
                                if not search_result:
                                    search_result = obj_contact.search([('token', '=', new_token)])
                                    if not search_result:
                                        exists = False
                            current_token = new_token
                            # writing of this prospect in users.csv
                            if current_token not in published_tokens and current_login not in published_logins:
                                csvrecord = []
                                csvrecord.append(0)
                                csvrecord.append(0)
                                csvrecord.append(addr[0])
                                csvrecord.append(addr[1])
                                csvrecord.append(1)
                                csvrecord.append('.')
                                csvrecord.append('(inconnu)')
                                csvrecord.append('(inconnu)')
                                csvrecord.append(_clean_CR(current_login or '').encode("cp1252"))
                                published_logins.append(current_login)
                                csvrecord.append((current_pw or '').encode("cp1252"))
                                csvrecord.append((current_token or '').encode("cp1252"))
                                published_tokens.append(current_token)
                                csvrecord.append(_clean_CR(current_email).encode("cp1252"))
                                published_emails.append(current_email)
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                current_zip = False
                                if addr[11] and addr[11] in dZips:
                                    current_zip = dZips[addr[11]]
                                    if current_zip['name'][0:1] == '5':
                                        csvrecord.append(2)
                                    else:
                                        csvrecord.append(1)
                                else:
                                    csvrecord.append(1)
                                csvrecord.append(0)
                                if addr[12]:
                                    full_name = addr[12]
                                else:
                                    full_name = _get_name_and_suffix(addr[8] or '' , addr[2] or '')[0]
                                csvrecord.append(full_name.encode("cp1252"))
                                csvrecord.append(_clean_CR(addr[3] or '').encode("cp1252"))
                                csvrecord.append(_clean_CR(addr[4] or '').encode("cp1252"))
                                csvrecord.append(_clean_CR(addr[5] or '').lower().strip().encode("cp1252"))
                                csvrecord.append(_clean_CR(addr[6] or '').encode("cp1252"))
                                csvrecord.append(_clean_CR(addr[7] or '').encode("cp1252"))
                                if addr[9] and addr[10]:
                                    csvrecord.append(_clean_CR(addr[9] + ' - ' + addr[10]).encode("cp1252"))
                                elif addr[9]:
                                    csvrecord.append(_clean_CR(addr[9]).encode("cp1252"))
                                else:
                                    csvrecord.append(_clean_CR(addr[10] or '').encode("cp1252"))
                                if current_zip:
                                    csvrecord.append((current_zip['name'] or '').encode("cp1252"))
                                    csvrecord.append((current_zip['city'] or '').encode("cp1252"))
                                else:
                                    csvrecord.append('')
                                    csvrecord.append('')
                                if addr[13] and dCountries.has_key(addr[13]):
                                    csvrecord.append((dCountries[ addr[13] ]['code'] or '').encode("cp1252"))
                                else:
                                    csvrecord.append('BE')
                                #
                                frequency = DEFAULT_SUBSCRIPTION_FREQ
                                csvrecord.append(frequency[0])
                                csvrecord.append(frequency[1])
                                csvrecord.append(frequency[2])
                                csvrecord.append(frequency[3])
                                csvrecord.append(frequency[4])
                                csvrecord.append('prospect_address')
                                csvrecord.append(0)
                                hfCSV.writerow(csvrecord)
                                count_prospects += 1
                    _add_log(u"Prospects en cours ajoutés : " + str(count_prospects), 'short')
            
            # end if include_prospects

            if include_all_others:
                # PART 5: extraction of all emails, with their usage in synchronised extractions
                #        These emails doesn't have the right to receveive the 'revue de presse'
                DEFAULT_SUBSCRIPTION_FREQ = '00000'
            # end if include_others
            hfOut.close()
            hfUser.close()

            ftp_files.append('users.csv')
            ftp_files.append('links.csv')
            ftp_files.append('interests.csv')

        # PART : Sending of csv files to internet site
        obj_connection = self.env['ftp_connection']
        ids = obj_connection.search([('internal_code', '=', connection)])
        if ids and len(ids) == 1:
            ftp_connection_id = ids[0]
            ftpserver = obj_connection.connect(ftp_connection_id)
            if ftpserver:
                for csvfile in ftp_files:
                    result = obj_connection.upload(ftpserver, csvfile, csvfile)
                    _add_log(result)
                obj_connection.close(ftpserver)
            else:
                _add_log(u"Pas de connection FTP possible")
        else:
            _add_log(u"Connection inexistante")
        
        # record of the log
        short = '\n'.join(simple_log)
        full = '\n'.join(full_log)
        send_log_obj = self.env['cci_newsletter.log']
        log_id = send_log_obj.create({'datetime':time.strftime('%Y-%m-%d %H:%M:%S'), 'short':short, 'full':full, 'count':done })

        # attach the users.csv file to the log
        input_file = open('users.csv', 'rb').read()
        newvalue = {}
        newvalue['res_model'] = 'cci_newsletter.log'
        newvalue['res_id'] = log_id
        newvalue['datas_fname'] = 'users.csv'
        newvalue['datas'] = base64.encodestring(input_file)
        newvalue['name'] = 'Users.csv'
        attach_obj = self.env['ir.attachment']
        attach_obj.create(newvalue)
        return (short, done)
