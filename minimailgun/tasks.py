
import dns.resolver
import operator
import socket
from celery import Celery, group
from celery.utils.log import get_task_logger
from smtplib import SMTP, SMTPException
from minimailgun.config import config
from minimailgun.store import store


celery = Celery(__name__, include=['minimailgun.tasks'])
celery.conf.update({key.upper(): value for key, value in config['celery'].items()})
log = get_task_logger(__name__)


@celery.task(ignore_result=True)
def handle_new_message(id):
    message = store.get_mail_by_id(id)
    sendmail_jobs = group(sendmail.si(message, recipient) for recipient in message['recipients'].keys())
    sendmail_jobs()


@celery.task(
    ignore_result=True,
    bind=True,
    default_retry_delay=config['mail_properties']['retry_time'],
    max_retries=config['mail_properties']['max_retry']
)
def sendmail(self, message, recipient):
    rcpt = message['recipients'][recipient]['email']
    log_message = 'MailID: {id} to:{rcpt} Try# {count} Status: '.format(
        rcpt=rcpt,
        id=message['_id'],
        count=self.request.retries
    )

    domain = rcpt.split('@')[-1]
    try:
        mx_records = dns.resolver.query(domain, 'MX')
        mx_records = {rdata.exchange: rdata.preference for rdata in mx_records}
        if not mx_records:
            pass
            # raise some exception if no records in the answer.
    except Exception:
        raise self.retry()

    # sort by distance of MX record and use the 1st one (closest one)
    mx_records = sorted(mx_records.items(), key=operator.itemgetter(1))
    mx_host = str(mx_records[0][0])
    mx_port = socket.getservbyname('smtp')
    log.debug('MX Record: {} Port {}'.format(mx_host, mx_port))
    with SMTP(host=mx_host, port=mx_port) as smtp:
        smtp.set_debuglevel(1)
        try:
            smtp.sendmail(message['from'], rcpt, message['message'])
            message['recipients'][recipient]['status'] = 'Delivered'
            log_message += 'Delivered'
        except SMTPException as exc:
            message['recipients'][recipient]['status'] = 'Failed'
            log_message += str(exc)
            raise self.retry()
        finally:
            log.info(log_message)
