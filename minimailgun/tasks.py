"""
Implements Celery interface and tasks that celery can execute.
"""

import dns.resolver
import operator
import socket
from celery import Celery, group
from celery.utils.log import get_task_logger
from dns.resolver import Timeout, NoAnswer, NXDOMAIN, YXDOMAIN, NoNameservers
from smtplib import SMTP, SMTPException
from minimailgun.config import config
from minimailgun.store import store


celery = Celery(__name__, include=['minimailgun.tasks'])
celery.conf.update({key.upper(): value for key, value in config['celery'].items()})
log = get_task_logger(__name__)


class DNSLookupError(LookupError):
    pass


@celery.task(ignore_result=True)
def handle_new_message(id):
    message = store.get_mail_by_id(id)
    sendmail_jobs = group(sendmail.si(message, rcpt_id) for rcpt_id in message['_recipients'].keys())
    sendmail_jobs()


@celery.task(
    ignore_result=True,
    bind=True,
    default_retry_delay=config['mail_properties']['retry_time'],
    max_retries=config['mail_properties']['max_retry']
)
def sendmail(self, message, rcpt_id):
    '''
    Send a message to give email address
    :param message: The message to deliver
    :param rcpt_id: Recipient id in the message we are handling.
    :return: None

    Does MX lookup
    Delivers email to preferred MX server
    If any failure happens, it retries for upto the configured number of times.
    After each attempt it updates the status for this recipient in the message.
    '''
    status = None
    rcpt = message['_recipients'][rcpt_id]['email']
    try:
        mx_host = lookup_mx_record(rcpt)
        mx_port = socket.getservbyname('smtp')
        with SMTP(host=mx_host, port=mx_port) as smtp:
            smtp.set_debuglevel(0)
            result = smtp.sendmail(message['from'], rcpt, message['message'])
            status = result or 'Delivered'
    except (NXDOMAIN, DNSLookupError) as exc:
        status = 'Fatal DNS Error. No Retry ' + (str(exc) or str(type(exc)))
    except (Timeout, NoAnswer, YXDOMAIN, NoNameservers) as exc:
        status = str(exc) or 'DNS Error ' + str(type(exc))
        raise self.retry()
    except (SMTPException, Exception) as exc:
        status = str(exc)
        raise self.retry()
    finally:
        log.info('MailID:{id} to:{rcpt} Try#:{count} Status:{status}'.format(
            rcpt=rcpt,
            id=message['_id'],
            count=self.request.retries,
            status=status
        ))
        store.update_status(message['_id'], rcpt_id, status)


def lookup_mx_record(email):
    '''
    Do a MX lookup for the domain the provided email belongs to.
    Return the closet MX host name.
    :param email: The email address for which MX record is to be looked up
    :return: hostname for the closes MX server

    Can raise variable exceptions
    DNXLookupError - if nameserver returns no MX servers
    NXDOMAIN - non-existent domain
    Timeout - if look up timesout
    NoAnswer - if no answer received from DNS server.
    NoNameservers - If no name servers are reachable/configured
    '''
    domain = email.split('@')[-1]
    mx_records = dns.resolver.query(domain, 'MX')
    mx_records = {rdata.exchange: rdata.preference for rdata in mx_records}
    if not mx_records:
        status = 'No MX records found for {domain}'.format(**locals())
        raise DNSLookupError(status)

    # sort by distance of MX record and use the 1st one (closest one)
    mx_records = sorted(mx_records.items(), key=operator.itemgetter(1))
    mx_host = str(mx_records[0][0])
    return mx_host
