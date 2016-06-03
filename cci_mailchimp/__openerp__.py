# -*- encoding: utf-8 -*-
{
    'name': 'CCI MailChimp',
    'category': 'CCI,email',
    'description': '''
        Module to synchronize emails list of subscriber of 'Revue de Presse' with MailChimp email service.
        This module uses the MailChimp API wrapper : mailchimp-api-python
            https://bitbucket.org/mailchimp/mailchimp-api-python
    ''',
    'author': 'CCI Liege Verviers Namur - Philmer',
    'depends': ['cci_partner_extend', 'cci_newsletter', 'cci_premium'], #'cci_parameters',  'cci_logs', 
    'version': '1.2',
    'data': [	
        'security/security.xml',
        'security/ir.model.access.csv',
        'cci_mailchimp_view.xml',
        'wizard/correct_emails_view.xml',
        'wizard/delete_emails_view.xml',
        'wizard/extract_results_advertising_view.xml',
        'wizard/extract_results_rdp_view.xml',
        'wizard/mail_usage_show_record_view.xml',
        'wizard/resubscribe_view.xml',
        'wizard/search_email_view.xml',
        'wizard/unsubscribe_emails_view.xml',
	],
    'demo': [],
    'installable': True,
}

