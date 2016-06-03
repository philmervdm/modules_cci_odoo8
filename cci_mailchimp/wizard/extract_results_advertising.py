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
# Version 1.0 Philmer
# This wizard searchs for emails addresses in a list of given table

import time
import datetime
#import mailchimp
import base64
from xlwt import *

from openerp import models, fields, api, _ 

def french_date(string):
    return string[8:10] + "/" + string[5:7] + '/' + string[0:4]
    
class cci_mailchimp_results_adv(models.TransientModel):
    _name = 'cci.mailchimp.results.adv'
    
    url = fields.Char(string='URL of the advertising', help='You can give also only a part of the complete URL.\nAll URL containing this part will be taken into account.', required=True)
    from_date = fields.Date(string='From', help='Date of the first Revue de Presse', required=True)
    to_date = fields.Date(string='To', help='Date of the last Revue de Presse', required=True)
    
    @api.multi
    def extract(self):
        # Initialisation of result file
        wb1 = Workbook()
        ws1 = wb1.add_sheet(u'Résultats')
        ws1.write(0, 0, u'URL :')
        ws1.write(1, 0, u'De :')
        ws1.write(2, 0, u'à :')
        ws1.write(3, 0, u'Seules les dates et les régions où l\'URL a été utilisée avec un tracking activé apparaissent ici.')
        ws1.write(0, 1, data['form']['url'])
        ws1.write(1, 1, french_date(self.from_date))
        ws1.write(2, 1, french_date(self.to_date))
        ws1.write(3, 0, u'Seules les revue de presse ayant au moins un résultat sont présentées ici')
        ws1.write(5, 0, u'RDP envoyées :')
        ws1.write(6, 0, u'Moyenne Uniques clicks/jour :')
        ws1.write(9, 0, u'Date')
        ws1.write(8, 1, u'Total')
        ws1.write(9, 1, u'Envois')
        ws1.write(9, 2, u'Ouverts')
        ws1.write(9, 3, u'Ouv. uniques')
        ws1.write(9, 4, u'Clicks')
        ws1.write(9, 5, u'Cl. uniques')
        ws1.write(9, 6, u'URL clicks')
        ws1.write(9, 7, u'URL Cl. Uniques')
        xls_line = 10
        # Possibles revue de presse
        rdps = {}
        rdps[1] = {'name':u'- BW', 'count':0}
        rdps[2] = {'name':u'- Hainaut', 'count':0}
        rdps[3] = {'name':u'- Liège Verviers', 'count':0}
        rdps[4] = {'name':u'- Namur', 'count':0}
        rdps[5] = {'name':u'- Wapi', 'count':0}
        rdps[6] = {'name':u'- VL', 'count':0}
        rdps[7] = {'name':u'- Inconnue', 'count':0}
        # connections to mailchimp
        # We get the API key
        parameter_obj = self.env['ir.config_parameter']
        param_values = parameter_obj.get_param(['MailChimpAPIKey'])
        if param_values.has_key('MailChimpAPIKey'):
            mailchimp_server = mailchimp.Mailchimp(param_values['MailChimpAPIKey'], False)
            mailchimp_campaigns = mailchimp.Campaigns(mailchimp_server)
            mailchimp_reports = mailchimp.Reports(mailchimp_server)
            start = 0
            limit = 25
            result = mailchimp_campaigns.list({'status':'sent'}, start, limit, 'send_time', 'DESC')
            total = result['total']
            url = self.url
            date_from = self.from_date
            date_to = self.to_date
            final_count = 0
            dates = []
            dResults = {}
            while start <= ((total / limit) + 1):
                result = mailchimp_campaigns.list({'status':'sent'}, start, limit, 'send_time', 'DESC')
                for line in result['data']:
                    if line['emails_sent'] and line['send_time'][0:10] >= date_from and line['send_time'][0:10] <= date_to:
                        if line['tracking']['html_clicks']:
                            result = mailchimp_reports.clicks(line['id'])
                            for click in result['total']:
                                if url in click['url']:
                                    rdp_id = False
                                    for (key, rdp) in rdps.items():
                                        if rdp['name'] in line['title']:
                                            rdp_id = key
                                            break
                                    if not rdp_id:
                                        rdp_id = 6
                                    rdps[rdp_id]['count'] += 1
                                    resu = {
                                        'date': line['send_time'][0:10],
                                        'rdp_id': rdp_id,
                                        'sendings': line['emails_sent'],
                                        'opens': line['summary']['opens'],
                                        'u_opens': line['summary']['unique_opens'],
                                        'clicks': line['summary']['clicks'],
                                        'u_clicks': line['summary']['unique_clicks'],
                                        'url_clicks': click['clicks'],
                                        'u_url_clicks': click['unique']
                                    }
                                    if line['send_time'][0:10] not in dates:
                                        dates.append(line['send_time'][0:10])
                                    if dResults.has_key((line['send_time'][0:10], rdp_id)):
                                        # dResults[(line['send_time'][0:10],rdp_id)]['opens'] += line['summary']['opens']
                                        # dResults[(line['send_time'][0:10],rdp_id)]['u_opens'] += line['summary']['unique_opens']
                                        # dResults[(line['send_time'][0:10],rdp_id)]['clicks'] += line['summary']['clicks']
                                        # dResults[(line['send_time'][0:10],rdp_id)]['u_clicks'] += line['summary']['unique_clicks']
                                        dResults[(line['send_time'][0:10], rdp_id)]['url_clicks'] += click['clicks']
                                        dResults[(line['send_time'][0:10], rdp_id)]['u_url_clicks'] += click['unique']
                                    else:
                                        dResults[(line['send_time'][0:10], rdp_id)] = resu
                                        final_count += 1
                start += 1
            final_rdps = []
            for (key, rdp) in rdps.items():
                if rdp['count'] > 0:
                    final_rdps.append(key)
            final_rdps.sort()
            index = 1
            for rdp_id in final_rdps:
                ws1.write(8, (index * 7) + 1, rdps[rdp_id]['name'][2:])
                ws1.write(9, (index * 7) + 1, u'Envois')
                ws1.write(9, (index * 7) + 2, u'Ouverts')
                ws1.write(9, (index * 7) + 3, u'Ouv. uniques')
                ws1.write(9, (index * 7) + 4, u'Clicks')
                ws1.write(9, (index * 7) + 5, u'Cl. uniques')
                ws1.write(9, (index * 7) + 6, u'URL clicks')
                ws1.write(9, (index * 7) + 7, u'URL Cl. Uniques')
                index += 1
            dates.sort(reverse=True)
            final_results = {}
            full_list = [0, ]
            full_list.extend(final_rdps)
            for rdp_id in full_list:  # ## 0 will serve for totals
                final_results[rdp_id] = {'sendings':0, 'opens':0, 'u_opens':0, 'clicks':0, 'u_clicks':0, 'url_clicks':0, 'u_url_clicks':0}
            for date in dates:
                ws1.write(xls_line, 0, french_date(date))
                index = 1
                total_sendings = 0
                total_opens = 0
                total_u_opens = 0
                total_clicks = 0
                total_u_clicks = 0
                total_url_clicks = 0
                total_u_url_clicks = 0
                for rdp_id in final_rdps:
                    if dResults.has_key((date, rdp_id)):
                        ws1.write(xls_line, (index * 7) + 1, dResults[(date, rdp_id)]['sendings'])
                        ws1.write(xls_line, (index * 7) + 2, dResults[(date, rdp_id)]['opens'])
                        ws1.write(xls_line, (index * 7) + 3, dResults[(date, rdp_id)]['u_opens'])
                        ws1.write(xls_line, (index * 7) + 4, dResults[(date, rdp_id)]['clicks'])
                        ws1.write(xls_line, (index * 7) + 5, dResults[(date, rdp_id)]['u_clicks'])
                        ws1.write(xls_line, (index * 7) + 6, dResults[(date, rdp_id)]['url_clicks'])
                        ws1.write(xls_line, (index * 7) + 7, dResults[(date, rdp_id)]['u_url_clicks'])
                        total_sendings += dResults[(date, rdp_id)]['sendings']
                        total_opens += dResults[(date, rdp_id)]['opens']
                        total_u_opens += dResults[(date, rdp_id)]['u_opens']
                        total_clicks += dResults[(date, rdp_id)]['clicks']
                        total_u_clicks += dResults[(date, rdp_id)]['u_clicks']
                        total_url_clicks += dResults[(date, rdp_id)]['url_clicks']
                        total_u_url_clicks += dResults[(date, rdp_id)]['u_url_clicks']
                        # cumulates for final line
                        for col in [0, rdp_id]:
                            for column_name in ['sendings', 'opens', 'u_opens', 'clicks', 'u_clicks', 'url_clicks', 'u_url_clicks']:
                                final_results[col][column_name] += dResults[(date, rdp_id)][column_name]
                    else:
                        ws1.write(xls_line, (index * 7) + 1, 0)
                        ws1.write(xls_line, (index * 7) + 2, 0)
                        ws1.write(xls_line, (index * 7) + 3, 0)
                        ws1.write(xls_line, (index * 7) + 4, 0)
                        ws1.write(xls_line, (index * 7) + 5, 0)
                        ws1.write(xls_line, (index * 7) + 6, 0)
                        ws1.write(xls_line, (index * 7) + 7, 0)
                    index += 1
                ws1.write(xls_line, 1, total_sendings)
                ws1.write(xls_line, 2, total_opens)
                ws1.write(xls_line, 3, total_u_opens)
                ws1.write(xls_line, 4, total_clicks)
                ws1.write(xls_line, 5, total_u_clicks)
                ws1.write(xls_line, 6, total_url_clicks)
                ws1.write(xls_line, 7, total_u_url_clicks)
                xls_line += 1
            ws1.write(5, 1, final_count)
            ws1.write(6, 1, '%.2f' % ((final_results[0]['u_url_clicks'] * 1.0) / len(dates)))
            ws1.write(xls_line, 0, u'Totaux')
            index = 0
            for rdp_id in full_list:
                ws1.write(xls_line, (index * 7) + 1, final_results[rdp_id]['sendings'])
                ws1.write(xls_line, (index * 7) + 2, final_results[rdp_id]['opens'])
                ws1.write(xls_line, (index * 7) + 3, final_results[rdp_id]['u_opens'])
                ws1.write(xls_line, (index * 7) + 4, final_results[rdp_id]['clicks'])
                ws1.write(xls_line, (index * 7) + 5, final_results[rdp_id]['u_clicks'])
                ws1.write(xls_line, (index * 7) + 6, final_results[rdp_id]['url_clicks'])
                ws1.write(xls_line, (index * 7) + 7, final_results[rdp_id]['u_url_clicks'])
                index += 1
            # save the final result file
            wb1.save('res_advert.xls')
            result_file = open('res_advert.xls', 'rb').read()

            # give the result to the user
            msg = u'Save the File with \'.xls\' extension.'
            res_advert_xls = base64.encodestring(result_file)
        else:
            msg = u'The parameter MailChimpAPIKey is missing !\nImpossible to extract something.'
            
        ctx = self.env.context.copy()
        ctx.update({'msg': msg, 'res_advert_xls': res_advert_xls})
        view = self.env.ref('cci_mailchimp.view_cci_mailchimp_results_adv_msg')
        
        return {
            'name': _('Notification'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'cci.mailchimp.results.adv.msg',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': ctx,
        }

class cci_mailchimp_results_adv_msg(models.TransientModel):
    _name = 'cci.mailchimp.results.adv.msg'
    
    msg = fields.Text(string='File created', readonly=True)
    res_advert_xls = fields.Binary(string='Prepared file', readonly=True)
    
    @api.model
    def default_get(self, fields):
        rec = super(cci_mailchimp_results_adv_msg, self).default_get(fields)
        if self.env.context.get('msg'):
            rec['msg'] = self.env.context['msg']
        if self.env.context.get('res_advert_xls'):
            rec['res_advert_xls'] = self.env.context['res_advert_xls']
        return rec

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
