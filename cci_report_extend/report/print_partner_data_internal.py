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

import time
from openerp.osv import osv
from openerp.report import report_sxw

class partner_internal(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(partner_internal, self).__init__(cr, uid, name, context)
        self.localcontext.update( {
            'time': time,
            'get_products': self._get_products,
            'get_orders' : self._get_orders,
            'get_pipe' : self._get_pipe,
            'get_part' : self._get_participations,
            'get_interest' : self._get_interest,
            'get_histo' : self._get_histo,
        })

    def _get_products(self,partner_id):
        return [{'name':'test1' + str(partner_id),'current':0.0,'past1':500.0,'past2':155.0},{'name':'test other','current':200.0,'past1':0.0,'past2':-155.0},]

    def _get_orders(self,partner_id):
        self.cr.execute("SELECT so.name as num, sol.expected_invoice_date as datefact, sol.name as product, (sol.price_unit*sol.product_uom_qty) as value " \
                "FROM sale_order AS so, sale_order_line AS sol " \
                "WHERE so.id = sol.order_id AND NOT sol.invoiced AND so.state <> 'cancel' AND so.state <> 'draft' AND so.partner_id = %s " \
                "ORDER BY sol.expected_invoice_date", (partner_id,) )
        lines = self.cr.dictfetchall()
        result = []
        for line in lines:
            values = {}
            values['num'] = line['num'] or '-nonum-'
            if line['datefact']:
                values['datefact'] = line['datefact'][8:10]+'/'+line['datefact'][5:7]+'/'+line['datefact'][0:4]
            else:
                values['datefact'] = ''
            values['product'] = line['product'] or ''
            values['value'] = line['value'] or 0.0
            result.append( values )
        return result

    def _get_pipe(self,partner_id):
        self.cr.execute("SELECT cp.name as product, cpc.name as category, ccase.date_deadline as deadline, ruser.name as contact, ccase.name as desc " \
                "FROM crm_case AS ccase " \
                "LEFT OUTER JOIN cci_product AS cp ON ( ccase.product = cp.id ) " \
                "LEFT OUTER JOIN cci_product_category AS cpc ON ( ccase.product_category = cpc.id ) " \
                "LEFT OUTER JOIN res_users AS ruser ON ( ccase.user_id = ruser.id ) " \
                "WHERE ccase.state <> 'cancel' AND ccase.state <> 'done' AND ccase.partner_id = %s " \
                "ORDER BY ccase.date_deadline", (partner_id,) )
        lines = self.cr.dictfetchall()
        result = []
        for line in lines:
            values = {}
            if line['product'] and line['category']:
                values['product'] = line['product'] + ' / ' + line['category']
            elif line['product']:
                values['product'] = line['product']
            else:
                values['product'] = '-aucun-'
            if line['deadline']:
                values['deadline'] = line['deadline'][8:10]+'/'+line['deadline'][5:7]+'/'+line['deadline'][0:4]
            else:
                values['deadline'] = ''
            values['contact'] = line['contact'] or ''
            values['desc'] = line['desc'] or ''
            result.append( values )
        return result

    def _get_participations(self,partner_id):
        result = []
        self.cr.execute("SELECT cl.name as name, p.date_in, p.forced_date_out, c.name || ' ' || c.first_name as who, " \
                               "pstate.name as state_name, pstate.current as state_current, cl.date_end " \
                "FROM cci_club_participation AS p, cci_club_club as cl, res_partner_contact AS c, cci_club_participation_state as pstate " \
                "WHERE p.partner_id = %s AND p.contact_id = c.id AND p.state_id = pstate.id AND p.group_id = cl.id " \
                "ORDER BY p.date_in", (partner_id,) )
        lines = self.cr.dictfetchall()
        for line in lines:
            values = {}
            values['name'] = line['name'] or 'Club sans nom'
            if line['date_in'] and (line['forced_date_out'] or line['date_end']):
                date_out = line['forced_date_out'] or line['date_end']
                values['dates'] = line['date_in'][8:10]+'/'+line['date_in'][5:7]+'/'+line['date_in'][0:4] + ' -> ' + date_out[8:10]+'/'+date_out[5:7]+'/'+date_out[0:4]
            elif line['date_in']:
                values['dates'] = line['date_in'][8:10]+'/'+line['date_in'][5:7]+'/'+line['date_in'][0:4] + ' -> ?'
            else:
                values['dates'] = ''
            values['who'] = line['who'] or ''
            if not line['state_current'] and line['state_name']:
                values['who'] += ' (' + line['state_name'] + ')'
            result.append( values )
        self.cr.execute("SELECT e.name_on_site AS name_on_site, pt.name AS event_name, e.date_begin, c.name || ' ' || c.first_name AS who " \
                "FROM event_registration AS reg, event_event AS e, crm_case AS ccase, res_partner_contact AS c, product_product AS p, product_template AS pt " \
                "WHERE reg.event_id = e.id AND reg.contact_id = c.id AND reg.case_id = ccase.id AND reg.partner_invoice_id = %s AND " \
                   "ccase.state <> 'cancel' AND e.product_id = p.id AND p.product_tmpl_id = pt.id AND " \
                   "date_part( 'year', e.date_begin ) BETWEEN (date_part( 'year', now() )-2) AND date_part( 'year', now() ) " \
                "ORDER BY e.date_begin", (partner_id,) )
        lines = self.cr.dictfetchall()
        for line in lines:
            values = {}
            if line['name_on_site']:
                values['name'] = line['name_on_site']
            else:
                values['name'] = line['event_name']
            if line['date_begin']:
                values['dates'] = line['date_begin'][8:10]+'/'+line['date_begin'][5:7]+'/'+line['date_begin'][0:4]
            else:
                values['dates'] = ''
            values['who'] = line['who'] or ''
            result.append( values )
        return result

    def _get_interest(self,partner_id):
        self.cr.execute("SELECT mi.date as date, cp.name as product, cpc.name as subproduct, cc.name as contact, mi.description as desc, mi.turnover_hoped " \
                "FROM res_partner_interest AS mi " \
                "LEFT OUTER JOIN cci_contact AS cc ON ( mi.cci_contact = cc.id ) " \
                "LEFT OUTER JOIN cci_product AS cp ON ( mi.product = cp.id ) " \
                "LEFT OUTER JOIN cci_product_category AS cpc ON ( mi.category = cpc.id ) " \
                "WHERE mi.active AND mi.partner = %s " \
                "ORDER BY mi.date", (partner_id,) )
        lines = self.cr.fetchall()
        result = []
        for line in lines:
            values = {}
            if line[1] and line[2]:
                values['product'] = line[1] + ' / ' + line[2]
            elif line[1]:
                values['product'] = line[1]
            else:
                values['product'] = '-aucun-'
            if line[0]:
                values['date'] = line[0][8:10]+'/'+line[0][5:7]+'/'+line[0][0:4]
            else:
                values['date'] = ''
            values['contact'] = line[3] or ''
            values['desc'] = line[4] or ''
            values['turnover'] = line[5] or 0.0
            result.append( values )
        return result
    def _get_histo(self,partner_id):
        self.cr.execute("SELECT histo.date as date, cp.name as product, cpc.name as subproduct, cc.name as contact, histo.description as desc " \
                "FROM res_partner_history AS histo " \
                "LEFT OUTER JOIN cci_contact AS cc ON ( histo.cci_contact = cc.id ) " \
                "LEFT OUTER JOIN cci_product AS cp ON ( histo.product = cp.id ) " \
                "LEFT OUTER JOIN cci_product_category AS cpc ON ( histo.category = cpc.id ) " \
                "WHERE histo.partner = %s " \
                "ORDER BY histo.date", (partner_id,) )
        lines = self.cr.fetchall()
        result = []
        for line in lines:
            values = {}
            if line[1] and line[2]:
                values['product'] = line[1] + ' / ' + line[2]
            elif line[1]:
                values['product'] = line[1]
            else:
                values['product'] = '-aucun-'
            if line[0]:
                values['date'] = line[0][8:10]+'/'+line[0][5:7]+'/'+line[0][0:4]
            else:
                values['date'] = ''
            values['contact'] = line[3] or ''
            values['desc'] = line[4] or ''
            result.append( values )
        return result

class report_partner_internal(osv.AbstractModel):
    _name = "report.cci_report_extend.report_partner_internal"
    _inherit = "report.abstract_report"
    _template = "cci_report_extend.report_partner_internal"
    _wrapped_report_class = partner_internal
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

