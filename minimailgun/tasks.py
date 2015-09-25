
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
    sendmail_jobs = group(sendmail.si(message, value['email']) for recipient, value in message['_recipients'].items())
    sendmail_jobs()


@celery.task(
    ignore_result=True,
    bind=True,
    default_retry_delay=config['mail_properties']['retry_time'],
    max_retries=config['mail_properties']['max_retry']
)
def sendmail(self, message, rcpt):
    log_message = 'MailID:{id} to:{rcpt} Try#:{count} Status:'.format(
        rcpt=rcpt,
        id=message['_id'],
        count=self.request.retries,
    )

    status = None
    domain = rcpt.split('@')[-1]
    try:
        mx_records = dns.resolver.query(domain, 'MX')
        mx_records = {rdata.exchange: rdata.preference for rdata in mx_records}
        if not mx_records:
            status = 'No MX records found for {domain}'.format(**locals())
            raise DNSLookupError(status)

        # sort by distance of MX record and use the 1st one (closest one)
        mx_records = sorted(mx_records.items(), key=operator.itemgetter(1))
        mx_host = str(mx_records[0][0])
        mx_port = socket.getservbyname('smtp')
        log.debug('MailID:{id} to:{rcpt} Try#:{count} Using MX:{host}'.format(
            id=message['_id'],
            rcpt=rcpt,
            count=self.request.retries,
            host=mx_host,
        ))
        with SMTP(host=mx_host, port=mx_port) as smtp:
            smtp.set_debuglevel(0)
            result = smtp.sendmail(message['from'], rcpt, message['message'])
            status = result or 'Delivered'
    except (Timeout, NoAnswer, NXDOMAIN, YXDOMAIN, NoNameservers, DNSLookupError) as exc:
        status = str(exc) or 'DNS Error ' + str(type(exc))
        raise self.retry()
    except SMTPException as exc:
        status = str(exc)
        raise self.retry()
    finally:
        log_message += status
        log.info(log_message)
        store.update_status(message['_id'], rcpt, status)
