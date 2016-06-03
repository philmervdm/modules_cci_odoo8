# -*- encoding: utf-8 -*-

from openerp import api, fields, models, _
from openerp.exceptions import Warning
import datetime
from xlwt import *
import math

class res_partner(models.Model):
    _inherit = "res.partner"
    _description = "res.partner"

    date_lastcheck = fields.Date(string='Last Check', help="Date of the last check of full data")
    
    @api.model
    def correct_daily_partners(self):
        # this method can be launched daily to correct some data on partners records
        # with supercharging write method
        # It records results in logs
        # Today, it correct this :
        #  - if partner is not 'In activity', it add a warning
        #  - if the employee_nbr_total < employee_nbr, upgrade it to employee_nbr

        errors = []

        # 1. Partners not in activity without warning
        # get the parameter that gives the text to put in warnings
#         parameter_obj = self.pool.get('cci_parameters.cci_value')
#         param_values = parameter_obj.get_value_from_names(cr,uid,['DailyControlWarningText','DailyControlWarningEMails'])
        param_values = {}
        param_values['DailyControlWarningText'] = self.env['ir.config_parameter'].get_param('DailyControlWarningText')
        param_values['DailyControlWarningEMails'] = self.env['ir.config_parameter'].get_param('DailyControlWarningEMails')
        
        if param_values.get('DailyControlWarningText'):
            warning = param_values['DailyControlWarningText']
        else:
            warning = u'ATTENTION : ce partenaire n\'est plus en activité.\nSon état est : \'%s\' depuis le \'%s\'.'
            
        if param_values.get('DailyControlWarningEMails'):
            sEmails = param_values['DailyControlWarningEMails']
            sEmails = sEmails.replace(',',';')
            warning_emails = sEmails.split(';')
            warning_emails = [x.strip() for x in warning_emails]
        else:
            warning_emails = []
         # get list of state names
        obj_states = self.env['res.partner.state']
        state_ids = obj_states.search([])
        states = state_ids.read(['id','name'])
        dStates = {}
        for state in states:
            dStates[state['id']] = state['name']
        # extract partners not in activity and without warning
        obj_partner = self.env['res.partner']
        partner_ids = obj_partner.search([('state_id','<>',1),('alert_explanation','=',False)])
        warnings_added = len(partner_ids)
        partners = partner_ids.read(['id','state_id','name','write_date','write_uid'])
        # globalize them by state change to reduce the number of call to 'write'
        warning_list = []
        dChangedStates = {}
        for partner in partners:
            warning_list.append(u'Partenaire %s (%i) en état \'%s\' par %s le %s a reçu une \'alerte\' automatique' % (partner['name'],
                                                                                                                      partner['id'],
                                                                                                                      partner['state_id'][1],
                                                                                                                      partner['write_uid'][1],
                                                                                                                      partner['write_date']))
            if not dChangedStates.has_key( partner['state_id'][0] ):
                dChangedStates[partner['state_id'][0]] = [partner['id']]
            else:
                current = dChangedStates[partner['state_id'][0]]
                current.append(partner['id'])
                dChangedStates[partner['state_id'][0]] = current
        # write the new value of warning to these partners
        today = datetime.datetime.today().strftime('%d/%m/%Y')
        for (state_id,partner_ids) in dChangedStates.items():
            try:
                partner_ids.write({'alert_explanation':warning % (dStates[state_id],today),
                                                      'alert_advertising':True,
                                                      'alert_events':True,
                                                      'alert_legalisations':True,
                                                      'alert_others':True,
                                                     })
            except Exception, msg_error:
                rejected += 1
                errors.append( 'Problems writing changes to partners ids :[%s]' % ','.join(partner_ids))
#         if warning_list and warning_emails and not errors:
#             tools.email_send('noreply@ccilvn.be', warning_emails, _('New Alerts put on Inactive Partners'), '<html><body><ul><li>%s</li></ul></body></html>' % '</li>\n<li>'.join(warning_list), subtype='html')
            
        # 2. Correct the employee_nbr_total to employee_nbr if unknown or lesser
        selection = """SELECT id from res_partner where employee_nbr IS NOT NULL AND (employee_nbr_total IS NULL OR employee_nbr_total < employee_nbr)"""
        self.env.cr.execute(selection)
        res = self.env.cr.fetchall()
        partner_ids = []
        partner_ids = [line[0] for line in res]
        employee_changed = len(partner_ids)
        partners = partner_ids.read(['id','employee_nbr'])
        for partner in partners:
            try:
                obj_partner.write([partner['id']],{'employee_nbr_total':partner['employee_nbr']})
            except Exception, msg_error:
                rejected += 1
                errors.append( 'Problems writing employee_nbr_total to partner id :[%s]' % str(partner['id']))

        # 3. Record ths changes in log file
#         log_obj = self.env['cci_logs.line']
#         if errors:
#             log_obj.create({'name':'Partners Daily Corrections ERRORS',
#                                    'datetime':datetime.datetime.now(),
#                                    'user_id':uid,
#                                    'message':'Errors while correcting some Partners :' % '\n'.join(errors),
#                                   })
#         else:
#             log_obj.create({'name':'Partners Daily Corrections',
#                                    'datetime':datetime.datetime.now(),
#                                    'user_id':uid,
#                                    'message':'Warning added : %s.\nEmployee_nbr_total corrected to employee_nbr : %s.' % (str(warnings_added),str(employee_changed)),
#                                   })
        return True
    
    @api.model
    def calculate_type_customer(self, excluded_accounts = [], additional_accounts = [], letters_range = [25,9], digits_range = [5000,1000,0], last_period_id = None ):
        return True
    
    @api.model
    def export_members_excel(self, category_id=False, ftp=False):
        # this method overwrites the method in cci_partner module because this last one is certified
        # this method correct a bug in sequence_yearbook -> sequence_directory
        def get_phone_country_prefix():
            result = []
            obj_country = self.env['cci.country']
            country_ids = obj_country.search([('phoneprefix','!=',False),('phoneprefix','!=',0)])
            if country_ids:
                countries = country_ids.read(['phoneprefix'])
                result = [str(x['phoneprefix']) for x in countries]
            return result
        def convert_phone(string,PHONE_COUNTRY_PREFIX):
            def only_digits(string):
                cleaned = ''
                for carac in string:
                    if carac in '0123456789':
                        cleaned += carac
                return cleaned
            result = ''
            string = only_digits(string)
            if len(string) > 0:
                if len(string) == 9:
                    if string[0:2] in ['02','03','04','09']:
                        result = string[0:2] + "/" + string[2:5] + "." + string[5:7] + "." + string[7:]
                    else:
                        result = string[0:3] + "/" + string[3:5] + "." + string[5:7] + "." + string[7:]
                elif len(string) == 10:
                    result = string[0:4] + "/" + string[4:6] + "." + string[6:8] + "." + string[8:]
                else:
                    # international number
                    if string[0:2] == '00':
                        # search after a country with this prefix
                        prefix = string[2:4]
                        if prefix not in PHONE_COUNTRY_PREFIX:
                            prefix = string[2:5]
                            if prefix not in PHONE_COUNTRY_PREFIX:
                                prefix = string[2:6]
                                if prefix not in PHONE_COUNTRY_PREFIX:
                                    prefix = ''
                        if prefix:
                            result = '+' + string[2:2+len(prefix)] + ' ' + string[2+len(prefix):4+len(prefix)]
                            rest = string[4+len(prefix):]
                            while len(rest) > 3:
                                result += '.' + rest[0:2]
                                rest = rest[2:]
                            result += '.' + rest
                        else:
                            result = 'International:'+string
            return result
        if category_id:
            # extract all ids of activity sector categories and remove '[303]' from name
            obj_categ = self.env['res.partner.category']
            old_len = 0
            categ_ids = [ category_id ]
            while len(categ_ids) > old_len:
                new_ids = categ_ids[old_len:] # ids of categories added last time
                old_len = len(categ_ids) # the new frontier ...
                new_categs = obj_categ.browse(new_ids).read(['child_ids'])
                for categ in new_categs:
                    if categ['child_ids']:
                        categ_ids.extend(categ['child_ids'])
            categs = obj_categ.browse(categ_ids).read(['name'])
            dCategs = {}
            for categ in categs:
                formated_name = categ['name']
                posA = formated_name.rfind('[')
                posB = formated_name.rfind(']')
                if posA > 0 and posB > 0 and posA < posB:
                    formated_name = formated_name[0:posA-1]
                dCategs[ categ['id'] ] = formated_name

        # extract all active members
        obj_partner = self.env['res.partner']
        partner_ids = obj_partner.search([('state_id','=',1),('membership_state','in',['paid','free','invoiced'])])
        partners = obj_partner.browse(partner_ids)
        wb = Workbook()
        ws = wb.add_sheet('liste')
        ws.write(0,0,u'Entreprise')
        ws.write(0,1,u'Adresse')
        ws.write(0,2,u'Adresse2')
        ws.write(0,3,u'CP')
        ws.write(0,4,u'Localité')
        ws.write(0,5,u'Tél')
        ws.write(0,6,u'Fax')
        ws.write(0,7,u'Fonction')
        ws.write(0,8,u'Nom')
        ws.write(0,9,u'Prénom')
        ws.write(0,10,u'Civilité')
        ws.write(0,11,u'Effectif')
        ws.write(0,12,u'TVA')
        if category_id:
            ws.write(0,13,u'Secteur')
        line = 1
        PREFIXES = get_phone_country_prefix()
        for partner in partners:
            ws.write(line,0,partner.name)
            for address in partner.child_ids:
                if address.type == 'default':
                    ws.write(line,1,address.street or '' )
                    ws.write(line,2,address.street2 or '' )
                    ws.write(line,3,address.zip or '' )
                    ws.write(line,4,address.city or '' )
                    ws.write(line,5,convert_phone(address.phone or '',PREFIXES) )
                    ws.write(line,6,convert_phone(address.fax or '',PREFIXES) )
                    min_seq = 999
                    id_min_seq = False
                    for job in address.other_contact_ids:
                        if job.sequence_directory and job.sequence_directory < min_seq and job.sequence_directory > 0:
                            min_seq = job.sequence_directory
                            id_min_seq = job.id
                    if not id_min_seq:
                        for job in address.other_contact_ids:
                            if job.sequence_partner and job.sequence_partner < min_seq and job.sequence_partner > 0:
                                min_seq = job.sequence_partner
                                id_min_seq = job.id
                    if id_min_seq:
                        selected_job_id = id_min_seq
                        for job in address.other_contact_ids:
                            if job.id == selected_job_id:
                                ws.write(line,7,job.function_label or '' )
                                if job.contact_id:
                                    ws.write(line,8,job.contact_id.name)
                                    ws.write(line,9,job.contact_id.first_name or '' )
                                    ws.write(line,10,job.contact_id.title.name or '' )
                    break
            ws.write(line,11,max(0,partner.employee_nbr or 0) or 'nc')
            ws.write(line,12,partner.vat or '' )
            if category_id:
                for categ in partner.category_id: ## category_id is, not like his name define, an array of category ids
                    if categ.id in categ_ids:
                        ws.write(line,13,dCategs[categ.id])
                        break
            line += 1
        wb.save('repertoire_des_membres_excel.xls')
        #wb.save('test.xls')
        wb = None

        # export to FTP
        if ftp:
            import ftplib
            FTP_HOST = '212.166.5.117'
            FTP_USER = 'ccilv_files'
            FTP_PW = 'hid5367cx'
            FTP_CWD = 'Repertoire_des_Membres'
            lFiles = []
            ftp = ftplib.FTP( FTP_HOST, FTP_USER, FTP_PW )
            ftp.getwelcome()
            ftp.pwd()
            ftp.retrlines('LIST')
            ftp.cwd( FTP_CWD )
            hFile = open( 'repertoire_des_membres_excel.xls' ,'rb')
            #hFile = open( 'test.xls' ,'rb')
            result = ftp.storbinary( 'STOR ' + 'repertoire_des_membres.xls', hFile )
            hFile.close()
            ftp.quit()
        # get the concerned accounts
        account_ids = self.env['account.account'].search([('code','like','7')]) # first screening to get all accounts with '7' inside
        accounts = account_ids.read(['code','id'])
    
    @api.constrains('vat')
    def check_vat_constrains(self):
        '''
        Check the VAT number depending of the country.
        http://sima-pc.com/nif.php
        '''
        ''' PHILMER : This method overwrite the method with the same name in 'base_vat' to check if vat number contains spaces or prohibited caracters '''
        for partner in self:
            if not partner.vat:
                continue    #FIXME return False? empty vat numbre is invalid?

            vat_country, vat_number = partner.vat[:2].lower(), partner.vat[2:]
            if vat_country in ['be','lu','nl','fr'] and (' ' in vat_number or '.' in vat_number): ## we must check this now, before the _check_vat_be receive the vat_number without spaces
                raise Warning(_(u"\nLe numéro de TVA semble incorrect (pas d'espaces, pas de ., 10 chiffres et les chiffres doivent répondre à quelques règles mathématiques).\n\nMerci de le re-vérifier."))
#             check = getattr(self, 'check_vat_' + vat_country)
#             if not check(vat_number.replace(' ','') ):
#                 raise Warning(_(u"\nLe numéro de TVA semble incorrect (pas d'espaces, pas de ., 10 chiffres et les chiffres doivent répondre à quelques règles mathématiques).\n\nMerci de le re-vérifier."))

        return True

#class res_partner_zip(models.Model):
#    _name = "res.partner.zip"
#    _description = 'res.partner.zip'
#    _inherit = "res.partner.zip"
#
#    other_names = fields.Text(string='Other Names')
#    latitude = fields.Float(string='Latitude',digit=(7,2))
#    longitude = fields.Float(string='Longitude',digit=(7,2))
#
#    @api.model
#    def distance_in_kilometers(self,zip_id1,zip_id2):
#        result = False
#        # get the latidude/longitude of both zip code
#        if zip_id1 and zip_id2:
#            zip1 = self.env['res.partner.zip'].read(zip_id1,['latitude','longitude'])
#            zip2 = self.env['res.partner.zip'].read(zip_id2,['latitude','longitude'])
#            if zip1 and zip2 and zip1['latitude'] and zip2['latitude'] and zip1['longitude'] and zip2['longitude']:
#                lat1 = zip1['latitude']
#                long1 = zip1['longitude']
#                lat2 = zip2['latitude']
#                long2 = zip2['longitude']
#
#                # Convert latitude and longitude to 
#                # spherical coordinates in radians.
#                degrees_to_radians = math.pi/180.0
#                    
#                # phi = 90 - latitude
#                phi1 = (90.0 - lat1)*degrees_to_radians
#                phi2 = (90.0 - lat2)*degrees_to_radians
#                    
#                # theta = longitude
#                theta1 = long1*degrees_to_radians
#                theta2 = long2*degrees_to_radians
#                    
#                # Compute spherical distance from spherical coordinates.
#                    
#                # For two locations in spherical coordinates 
#                # (1, theta, phi) and (1, theta, phi)
#                # cosine( arc length ) = 
#                #    sin phi sin phi' cos(theta-theta') + cos phi cos phi'
#                # distance = rho * arc length
#                
#                cos = (math.sin(phi1)*math.sin(phi2)*math.cos(theta1 - theta2) + 
#                       math.cos(phi1)*math.cos(phi2))
#                arc = math.acos( cos )
#
#                # Remember to multiply arc by the radius of the earth 
#                # in your favorite set of units to get length.
#                
#                # * 6373 to get kilometers
#                # * 3960 to get miles
#                result = arc * 6373
#        return result

