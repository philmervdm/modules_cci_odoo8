# -*- coding: utf-8 -*-
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
from openerp import models , fields , api , _
import datetime
import base64
import csv

#PRESSE AVANT DEMANDE DE CELINE LE 17/5 : [146,143] -> [133]
TAG_ADD_EXCLUE = 5065
PARTI_QUESTION_ID = 48
JOB_ADDIT_INFO_ID = 114
CHAPTERS = [
{'id':1,'name':u"Chambres de Commerce et d'Industrie de Liège Verviers Namur",'filebase':'annu_ccilvn','max_contacts':15,'subs':[
                    {'sub_name':u"",'categ_ids':[301]},
                                             ]},
{'id':2,'name':u"Chambres de Commerce Belges",'filebase':'annu_cci','max_contacts':4,'subs':[
                    {'sub_name':u"Associations & Fédérations de CCI",'categ_ids':[122]},
                    {'sub_name':u"Chambres de Commerce de Bruxelles",'categ_ids':[118]},
                    {'sub_name':u"Chambres de Commerce Wallonnes",'categ_ids':[116]},
                    {'sub_name':u"Chambres de Commerce Flamandes",'categ_ids':[117]},
                                             ]},
{'id':3,'name':u"Relations Internationales",'filebase':'annu_relint','max_contacts':4,'subs':[
                    {'sub_name':u"CCI belges à l'étranger",'categ_ids':[119]},
                    {'sub_name':u"CCI étrangères en Belgique",'categ_ids':[120]},
                    {'sub_name':u"Ambassades étrangères en Belgique",'categ_ids':[53]},
                    {'sub_name':u"Ambassades Belges à l'étranger",'categ_ids':[52]},
                    {'sub_name':u"Consulats",'categ_ids':[124]},
                                             ]},
{'id':4,'name':u"AWEX",'filebase':'annu_awex','max_contacts':4,'subs':[
                    {'sub_name':u"AWEX Centres régionaux",'categ_ids':[289]},
                                             ]},
{'id':5,'name':u"Exécutifs Régionaux et Communautaires",'filebase':'annu_executifs','max_contacts':4,'subs':[
                    {'sub_name':u"Communauté Française",'categ_ids':[272]},
                    {'sub_name':u"Région Wallonne",'categ_ids':[61]},
                    {'sub_name':u"Région Bruxelles-Capitale",'categ_ids':[73]},
                    {'sub_name':u"Région Flamande",'categ_ids':[67]},
                    {'sub_name':u"Communauté Germanophone",'categ_ids':[297]},
                                             ]},
{'id':6,'name':u"Centres de recherche",'filebase':'annu_centre_recherche','max_contacts':4,'subs':[
                    {'sub_name':u"Centres de recherche belges",'categ_ids':[128]},
                    {'sub_name':u"Cellule de liaison Entreprises-Universités/Hautes Ecoles",'categ_ids':[291]},
                    {'sub_name':u"Autres adresses utiles",'categ_ids':[292]},
                    {'sub_name':u"Pôles de compétitivité",'categ_ids':[299]},
                    {'sub_name':u"Clusters",'categ_ids':[300]},
                                             ]},
{'id':7,'name':u"Médiateurs",'filebase':'annu_mediateurs','max_contacts':4,'subs':[
                    {'sub_name':u"Médiateurs",'categ_ids':[262]},
                                             ]},
{'id':8,'name':u"Justice",'filebase':'annu_justice','max_contacts':4,'subs':[
                    {'sub_name':u"Juridiction du commerce",'categ_ids':[45]},
                                             ]},
{'id':9,'name':u"Provinces",'filebase':'annu_provinces','max_contacts':4,'subs':[
                    {'sub_name':u"",'categ_ids':[290]},
                                             ]},
{'id':10,'name':u"Bourgmestres et Communes de la Province de Liège",'filebase':'annu_communes_lg','max_contacts':4,'subs':[
                    {'sub_name':u"",'categ_ids':[263,270]},
                                             ]},
{'id':11,'name':u"Bourgmestres et Communes de la Province de Namur",'filebase':'annu_communes_nam','max_contacts':4,'subs':[
                    {'sub_name':u"",'categ_ids':[264,271]},
                                             ]},
{'id':12,'name':u"Etablissements d'enseignement supérieur de la Province de Liège",'filebase':'annu_enseignement_lg','max_contacts':4,'subs':[
                    {'sub_name':u"Etablissements d'enseignements supérieur",'categ_ids':[293]},
                    {'sub_name':u"Autres organismes de formation",'categ_ids':[317]},
                                             ]},
{'id':13,'name':u"Etablissements d'enseignement supérieur de la Province de Namur",'filebase':'annu_enseignement_nam','max_contacts':4,'subs':[
                    {'sub_name':u"Etablissements d'enseignements supérieur",'categ_ids':[294]},
                    {'sub_name':u"Autres organismes de formation",'categ_ids':[318]},
                                             ]},
{'id':14,'name':u"Organismes économiques",'filebase':'annu_organismes_eco_wallon','max_contacts':4,'subs':[
                    {'sub_name':u"A répartir par province après extraction",'categ_ids':[108]},
                                             ]},
{'id':15,'name':u"Organismes économiques",'filebase':'annu_organismes_eco_lg','max_contacts':4,'subs':[
                    {'sub_name':u"Province de Liège",'categ_ids':[111]},
                                             ]},
{'id':16,'name':u"Organismes économiques",'filebase':'annu_organismes_eco_nam','max_contacts':4,'subs':[
                    {'sub_name':u"Province de Namur",'categ_ids':[295]},
                                             ]},
{'id':17,'name':u"Presse",'filebase':'annu_presse','max_contacts':4,'subs':[
                    {'sub_name':u"",'categ_ids':[133]},
                    {'sub_name':u"Agences",'categ_ids':[281]},
                    {'sub_name':u"Ecrite - Quotidiens",'categ_ids':[147]},
                    {'sub_name':u"Ecrite - Hebdomadaires",'categ_ids':[148]},
                    {'sub_name':u"Ecrite - Bimensuels",'categ_ids':[149]},
                    {'sub_name':u"Ecrite - Mensuels",'categ_ids':[150]},
                    {'sub_name':u"Ecrite - Trimestriels",'categ_ids':[152]},
                    {'sub_name':u"En ligne",'categ_ids':[280]},
                    {'sub_name':u"Toutes boîtes",'categ_ids':[322]},
                    {'sub_name':u"Audiovisuelle - Radios",'categ_ids':[144]},
                    {'sub_name':u"Audiovisuelle - Télévisions",'categ_ids':[145]},
                    {'sub_name':u"Photographes",'categ_ids':[302]},
                                             ]},
{'id':18,'name':u"Presse Namuroise",'filebase':'annu_presse_nam','max_contacts':4,'subs':[
                    {'sub_name':u"",'categ_ids':[278]},
                                             ]},
{'id':19,'name':u"Presse Liégeoise",'filebase':'annu_presse_lg','max_contacts':4,'subs':[
                    {'sub_name':u"",'categ_ids':[138]},
                                             ]},
{'id':20,'name':u"Ministères et Cabinets Fédéraux",'filebase':'annu_federal_lg','max_contacts':4,'subs':[
                    {'sub_name':u"",'categ_ids':[43]},
                                             ]},
]

def extract_categ_ids(self ,parent_ids):
    obj_categ = self.env['res.partner.category']
    result_ids = parent_ids
    next_id = 0
    while next_id < len(result_ids):
        read_ids = result_ids[next_id:]
        next_id = len(result_ids)
        read_categs = obj_categ.read(read_ids,['id','child_ids'])
        for categ in read_categs:
            if categ['child_ids']:
                for id in categ['child_ids']:
                    if id not in result_ids:
                        result_ids.append( id )
    return result_ids

def get_address_name(string):
    if string:
        if string[0] == '-':
            return ' ' + string
        else:
            return string
    else:
        return ''

def convert_phone(PHONE_COUNTRY_PREFIX,string):
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
                        result+= '.' + rest[0:2]
                        rest = rest[2:]
                    result += rest
                else:
                    result = 'Error:'+string
    return result

def get_phone_country_prefix(self):
    result = []
    country_obj = self.env['cci.country']
    countries = country_obj.search([('phoneprefix','!=',False)])
#     countries = country_obj.browse(country_ids)
    for country in countries:
        result.append(str(country.phoneprefix))
    return result

def only_digits(string):
    cleaned = ''
    for carac in string:
        if carac in '0123456789':
            cleaned += carac
    return cleaned

def cmp_contacts(a,b):
    if a['sequence_yearbook'] < b['sequence_yearbook']:
        result = -1
    elif a['sequence_yearbook'] > b['sequence_yearbook']:
        result = 1
    else:
        result = 0
    return result

@api.multi
def get_partis(self,question_id):
    answer_obj = self.env['crm_profiling.answer']
    answer_rec = answer_obj.search([('question_id','=',question_id)])
    answers = answer_rec.read(['name'])
    partis= {}
    for answer in answers:
        partis[answer['id']] = answer['name']
    return (answer_rec.ids,partis)

@api.multi
def get_info_supp(self,question_id):
    answer_obj = self.env['crm_profiling.answer']
    answer_rec = answer_obj.search([('question_id','=',question_id)])
    answers = answer_rec.read(['text'])
    data= {}
    for answer in answers:
        data[answer['id']] = answer['text']
    return (answer_rec.ids,data)

class wizard_extract_chapters(models.TransientModel):

    _name = 'cci.yearbook.extract.chapters'
    
    chapter1 =  fields.Boolean(string = 'CCILVN')
    chapter2 = fields.Boolean(string = 'CCI Belges')
    chapter3 = fields.Boolean(string = 'Relations internationales')
    chapter4 = fields.Boolean(string = 'AWEX')
    chapter5 = fields.Boolean(string = 'Exécutifs Régionaux et Communautaires')
    chapter6 = fields.Boolean(string = 'Centres de recherche')
    chapter7 = fields.Boolean(string = 'Médiateurs')
    chapter8 = fields.Boolean(string = 'Justice')
    chapter9 = fields.Boolean(string = 'Province')
    chapter10 = fields.Boolean(string = 'Bourgmestres et Communes de la Province de Liège')
    chapter11 = fields.Boolean(string = 'Bourgmestres et Communes de la Province de Namur')
    chapter12 = fields.Boolean(string = 'Etablissements d\'enseignement supérieur de la Province de Liège')
    chapter13 = fields.Boolean(string = 'Etablissements d\'enseignement supérieur de la Province de Namur')
    chapter14 = fields.Boolean(string = 'Organismes économiques multi-province')
    chapter15 = fields.Boolean(string = 'Organismes économiques Liège')
    chapter16 = fields.Boolean(string = 'Organismes économiques Namur')
    chapter17 = fields.Boolean(string = 'Presse')
    chapter18 = fields.Boolean(string = 'Presse Namuroise')
    chapter19 = fields.Boolean(string = 'Presse Liégeoise')
    chapter20 = fields.Boolean(string = 'Ministères et Cabinets Fédéraux')
    
    @api.multi
    def extract_chapters(self):
        ctx = self.env.context.copy()
        PHONE_COUNTRY_PREFIXES = get_phone_country_prefix(self)
        (PARTI_IDS,PARTIS) = get_partis(self,PARTI_QUESTION_ID)
        (INFOSUPP_IDS,INFOSUPP_VALUES) = get_info_supp(self,JOB_ADDIT_INFO_ID)
        for chapter in CHAPTERS:
            # we create the ouput file, and set the headers
            filename = chapter['filebase']
            hfFile = open(filename,'w')
            hfCSV = csv.writer(hfFile,delimiter=";",quotechar='"',quoting=csv.QUOTE_NONNUMERIC,lineterminator='\n')
            headers = ['partner_id','address_id','category_id','chapter','subchapter','categ','company','country_expert','web_site','status','address_name','street','street2','zip_code','city','country','address_email','address_phone','address_fax']
            for iCont in range(0,chapter['max_contacts']):
                headers.append('job_id' + str(iCont+1))
                headers.append('contact_id' + str(iCont+1))
                headers.append('contact_courtesy' + str(iCont+1))
                headers.append('contact_name' + str(iCont+1))
                headers.append('contact_first_name' + str(iCont+1))
                headers.append('contact_email' + str(iCont+1))
                headers.append('job_email' + str(iCont+1))
                headers.append('contact_title' + str(iCont+1))
                headers.append('contact_seq' + str(iCont+1))
                headers.append('contact_infosup' + str(iCont+1))
                headers.append('parti' + str(iCont+1))
            headers.append('special')
            hfCSV.writerow(headers)
            if self.read(['chapter' + str(chapter['id'])]):
                # we record data if selected chapter
                #hfCSV.writerow([chapter['name'].encode('cp1252'),])
                chapter_categs = {}
                for sub in chapter['subs']:
                    sub_categ_ids = extract_categ_ids(self, sub['categ_ids'])
                    for sub_id in sub_categ_ids:
                        chapter_categs[ sub_id ] = sub['sub_name']
                categ_ids = chapter_categs.keys()
                if categ_ids:
                    selection = """SELECT DISTINCT(rp.id) from res_partner as rp, res_partner_res_partner_category_rel as rel
                                       WHERE rel.category_id in (%s) and rel.partner_id = rp.id AND rp.active""" % ','.join([str(x) for x in categ_ids])
                    self.env.cr.execute(selection)
                    res = self.env.cr.fetchall()
                    partner_ids = [x[0] for x in res]
                    partners = self.env['res.partner'].browse(partner_ids)
                    for partner in partners:
                        record = []
                        # calculations made in each case : partner with addresses or not
                        ## search for the first choice category owned by this partner
                        categ_id_found = 0
                        for categ in partner.category_id:
                            if chapter_categs.has_key( categ.id ):
                                categ_id_found = categ.id
                                break
                        # extract of expertise country
                        country_expertise = ''
                        if partner.country_relation:
                            for country_rel in partner.country_relation:
                                if country_rel.type == 'expert':
                                    country_expertise = country_rel.country_id.name
                                    break
                        # for each partner in categories, we extract all GOOD address; if a partner has addresses, but no good addresses,
                        # we don't export it; BUT if a partner has no address at all, we export it to show it and complete its data ASAP
                        if partner.child_ids:
                            for addr in partner.child_ids:
                                bGoodAddress = True
                                if addr.notdelivered or ( addr.answers_ids and TAG_ADD_EXCLUE in [x.id for x in addr.answers_ids] ):
                                    bGoodAddress = False
                                if bGoodAddress:
                                    # we export only addresses not marked as 'bad' and not excluded
                                    # search all contacts to extract from this address
                                    sel_contacts = []
                                    for job in addr.other_contact_ids:
                                        if job.sequence_yearbook > 0 and job.contact_id:
                                            info_supp = ''
                                            parti = ''
                                            # we try to extract a parti
                                            if job.contact_id.answers_ids:
                                                for answer in job.contact_id.answers_ids:
                                                    if answer.id in PARTI_IDS:
                                                        parti = PARTIS[answer.id]
                                                        break
                                            # we try to extract an additionnal info
                                            if job.answers_ids:
                                                for answer in job.answers_ids:
                                                    if answer.id in INFOSUPP_IDS:
                                                        info_supp = INFOSUPP_VALUES[answer.id]
                                            cont = {}
                                            cont['job_id'] = job.id
                                            cont['contact_id'] = job.contact_id.id
                                            cont['title'] = job.contact_id.title or ''
                                            cont['name'] = job.contact_id.name
                                            cont['first_name'] = job.contact_id.first_name or ''
                                            cont['contact_email'] = job.contact_id.email or ''
                                            cont['job_email'] = job.email or ''
                                            cont['function_label'] = job.function_label or ''
                                            cont['sequence_yearbook'] = job.sequence_yearbook
                                            cont['info_class wizard_extract_chapters(models.TransientModel):sup'] = info_supp
                                            cont['parti'] = parti
                                            sel_contacts.append(cont)
                                    #
                                    csvrecord = []
                                    csvrecord.append(partner.id)
                                    csvrecord.append(addr.id)
                                    csvrecord.append(categ_id_found)
                                    csvrecord.append(chapter['name'].encode('cp1252'))
                                    csvrecord.append(chapter_categs[categ_id_found].encode('cp1252'))
                                    csvrecord.append('')
                                    csvrecord.append(partner.name.encode('cp1252'))
                                    csvrecord.append(country_expertise.encode('cp1252'))
                                    csvrecord.append((partner.website or '').encode('cp1252'))
                                    csvrecord.append((partner.title or '').encode('cp1252'))
                                    csvrecord.append(get_address_name(addr.name).encode('cp1252'))
                                    csvrecord.append((addr.street or '' ).encode('cp1252'))
                                    csvrecord.append((addr.street2 or '').encode('cp1252'))
                                    if addr.zip_id:
                                        csvrecord.append(addr.zip_id.name.encode('cp1252'))
                                        csvrecord.append(addr.zip_id.city.encode('cp1252'))
                                    else:
                                        csvrecord.append('')
                                        csvrecord.append('')
                                    if addr.country_id and addr.country_id.name.lower() != 'belgique':
                                        csvrecord.append(addr.country_id.name.encode('cp1252'))
                                    else:
                                        csvrecord.append('')
                                    csvrecord.append((addr.email or '').encode('cp1252')) # addresse email
                                    csvrecord.append(convert_phone(PHONE_COUNTRY_PREFIXES,addr.phone or '').encode('cp1252'))
                                    csvrecord.append(convert_phone(PHONE_COUNTRY_PREFIXES,addr.fax or '').encode('cp1252'))
                                    if len(sel_contacts) > 1:
                                        sel_contacts.sort(cmp_contacts)
                                    for iCont in range(0,chapter['max_contacts']):
                                        if iCont < len(sel_contacts):
                                            cont = sel_contacts[iCont]
                                            csvrecord.append(cont['job_id'])
                                            csvrecord.append(cont['contact_id'])
                                            csvrecord.append(cont['title'].encode("cp1252"))
                                            csvrecord.append(cont['name'].encode('cp1252'))
                                            csvrecord.append(cont['first_name'].encode('cp1252'))
                                            csvrecord.append(cont['contact_email'].encode('cp1252'))
                                            csvrecord.append(cont['job_email'].encode('cp1252'))
                                            csvrecord.append((cont['function_label'] or '').replace(u'\u202a','').encode('cp1252'))
                                            csvrecord.append(cont['sequence_yearbook'])
                                            csvrecord.append((cont['info_sup'] or '').encode('cp1252'))
                                            csvrecord.append((cont['parti'] or '').encode('cp1252'))
                                        else:
                                            csvrecord.append(0)
                                            csvrecord.append(0)
                                            csvrecord.append('')
                                            csvrecord.append('')
                                            csvrecord.append('')
                                            csvrecord.append('')
                                            csvrecord.append('')
                                            csvrecord.append('')
                                            csvrecord.append(0)
                                            csvrecord.append('')
                                            csvrecord.append('')
                                    csvrecord.append('')
                                    hfCSV.writerow(csvrecord)
                        else:
                            # we output the isolated partner to show we don't have any address
                            # this is a different case of having a partner without any GOOD address
                            csvrecord = []
                            csvrecord.append(partner.id)
                            csvrecord.append(0)
                            csvrecord.append(categ_id_found)
                            csvrecord.append(chapter['name'].encode('cp1252'))
                            csvrecord.append(chapter_categs[categ_id_found].encode('cp1252'))
                            csvrecord.append('')
                            csvrecord.append(partner.name.encode('cp1252'))
                            csvrecord.append(country_expertise.encode('cp1252'))
                            csvrecord.append((partner.website or '').encode('cp1252'))
                            csvrecord.append((partner.title or '').encode('cp1252'))
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('')
                            csvrecord.append('') # addresse email
                            csvrecord.append('')
                            csvrecord.append('')
                            for iCont in range(0,chapter['max_contacts']):
                                csvrecord.append(0)
                                csvrecord.append(0)
                                csvrecord.append('') # contact courtesy
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append('')
                                csvrecord.append(0)
                                csvrecord.append('')
                                csvrecord.append('')
                            csvrecord.append('no address')
                            hfCSV.writerow(csvrecord)
            # we present the result to the user : one CSV file by chapter
            hfFile.close()
            result_file = open(filename,'rb').read()
#             self.filename = base64.encodestring(result_file)
            ctx.update({chapter['filebase']:base64.encodestring(result_file)})
            
        msg = "Save, one by one, the files with '.csv' extension."
        ctx.update({'msg':msg})
        return {
            'view_type':'form',
            'view_mode':'form',
            'res_model':'cci.yearbook.msg',
            'view_id':False,
            'type':'ir.actions.act_window',
            'target':'new',
            'context':ctx,
        }
    
class cci_yearbook_msg(models.TransientModel):
    
    _name = 'cci.yearbook.msg'

    msg =  fields.Text(string = 'File created', size = 100, readonly = True)
    annu_ccilvn = fields.Binary(string = 'CCILVN', readonly = True)
    annu_cci = fields.Binary(string = 'CCI Belges',readonly = True)
    annu_relint = fields.Binary(string = 'Relations internationales',readonly = True)
    annu_awex = fields.Binary(string = 'AWEX',readonly = True)
    annu_executifs = fields.Binary(string = 'Exécutifs Régionaux et Communautaires',readonly = True)
    annu_centre_recherche = fields.Binary(string = 'Centres de recherche',readonly = True)
    annu_mediateurs = fields.Binary(string = 'Médiateurs',readonly = True)
    annu_justice = fields.Binary(string = 'Justice',readonly = True)
    annu_provinces = fields.Binary(string = 'Province',readonly = True)
    annu_communes_lg = fields.Binary(string = 'Bourgmestres et Communes de la Province de Liège',readonly = True)
    annu_communes_nam = fields.Binary(string = 'Bourgmestres et Communes de la Province de Namur',readonly = True)
    annu_enseignement_lg = fields.Binary(string = 'Etablissements d\'enseignement supérieur de la Province de Liège',readonly = True)
    annu_enseignement_nam = fields.Binary(string = 'Etablissements d\'enseignement supérieur de la Province de Namur',readonly = True)
    annu_organismes_eco_wallon = fields.Binary(string = 'Organismes économiques multi-province',readonly = True)
    annu_organismes_eco_lg = fields.Binary(string = 'Organismes économiques Liège',readonly = True)
    annu_organismes_eco_nam = fields.Binary(string = 'Organismes économiques Namur',readonly = True)
    annu_presse = fields.Binary(string = 'Presse',readonly = True)
    annu_presse_nam = fields.Binary(string = 'Presse Namuroise',readonly = True)
    annu_presse_lg = fields.Binary(string = 'Presse Liégeoise',readonly = True)
    annu_federal_lg = fields.Binary(string = 'Ministères et Cabinets Fédéraux',readonly = True)

    @api.model
    def default_get(self, fields):
        res = super(cci_yearbook_msg, self).default_get(fields)
        ctx = self.env.context.copy()
        res.update({
                    'msg': ctx.get('msg',''),
                    'annu_ccilvn': ctx.get('annu_ccilvn',''),
                    'annu_cci' : ctx.get('annu_cci',''),
                    'annu_relint': ctx.get('annu_relint',False),
                    'annu_awex' : ctx.get('annu_awex',False),
                    'annu_executifs': ctx.get('annu_executifs',False),
                    'annu_centre_recherche': ctx.get('annu_centre_recherche',False),
                    'annu_mediateurs': ctx.get('annu_mediateurs',False),
                    'annu_justice': ctx.get('annu_justice',False),
                    'annu_provinces': ctx.get('annu_provinces',False),
                    'annu_communes_lg': ctx.get('annu_communes_lg',False),
                    'annu_communes_nam': ctx.get('annu_communes_nam',False),
                    'annu_enseignement_lg': ctx.get('annu_enseignement_lg',False),
                    'annu_enseignement_nam': ctx.get('annu_enseignement_nam',False),
                    'annu_organismes_eco_wallon': ctx.get('annu_organismes_eco_wallon',False),
                    'annu_organismes_eco_lg': ctx.get('annu_organismes_eco_lg',False),
                    'annu_organismes_eco_nam': ctx.get('annu_organismes_eco_nam',False),
                    'annu_presse': ctx.get('annu_presse',False),
                    'annu_presse_nam': ctx.get('annu_presse_nam',False),
                    'annu_presse_lg': ctx.get('annu_presse_lg',False),
                    'annu_federal_lg': ctx.get('annu_federal_lg',False),
                    })
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
