
import os
import itertools
import traceback
from flask import Flask, Blueprint, jsonify, request, abort, current_app
from werkzeug.exceptions import default_exceptions, HTTPException

from minimailgun.store import store, MailLookupError, UnablToAddMessageError
from minimailgun.tasks import handle_new_message


mailgun_api = Blueprint('mini-mailgun', __name__)


@mailgun_api.route('/mail', methods=['POST'])
def create_mail():
    if request.content_type != 'application/json':
        abort(415, 'This api does not support content-type {mime}. Accepted mime-type: application/json'.format(
            mime=request.mimetype))
    if not request.accept_mimetypes.accept_json:
        abort(406, 'This api only responds in application/json')
    request_data = request.get_json()
    if not request_data.get('from'):
        abort(400, 'The from address is required.')
    # other payload validation goes here.

    recipient_set = set(itertools.chain(
        request_data.get('to', []),
        request_data.get('cc', []),
        request_data.get('bcc', [])
    ))
    if not recipient_set:
        abort(400, 'Need at least one recipient for mail.')

    # insert the message in db
    message = store.add_mail(request_data, recipient_set)
    # trigger a task for it and pass message-id
    handle_new_message.delay(message['_id'])
    return jsonify(message)


@mailgun_api.route('/mail/<uuid:id>')
def get_mail_status(id):
    message = store.get_mail_by_id(id)
    return jsonify(message)


@mailgun_api.errorhandler(MailLookupError)
def handle_mail_lookup_error(exc):
    current_app.logger.info(str(exc))
    abort(404, str(exc))


@mailgun_api.errorhandler(UnablToAddMessageError)
def handle_unable_to_add(exc):
    current_app.logger.warn('Unable to add mail to DB. Exception: {}'.format(exc))
    abort(500, str(exc))


def make_json_error(exc):
    if not isinstance(exc, HTTPException):
        code = 500
        message = str(exc)
        description = repr(exc)
        current_app.logger.error(traceback.print_exc())
    else:
        code = exc.code
        message = exc.name
        description = getattr(exc, 'description', None)

    response = jsonify(code=code, message=message, description=description)
    response.status_code = code
    return response


def create_mailgun_api(
        app_name=__name__,
        debug=None,
        JSONIFY_PRETTYPRINT_REGULAR=False,
        JSON_AS_ASCII=False,):
    app = Flask(app_name)
    if debug is None:
        debug = bool(os.environ.get('MINI_MAILGUN_DEBUG'))
    app.debug = debug
    app.config.update(JSONIFY_PRETTYPRINT_REGULAR=JSONIFY_PRETTYPRINT_REGULAR, JSON_AS_ASCII=JSON_AS_ASCII)
    for code in default_exceptions.keys():
        app.error_handler_spec[None][code] = make_json_error
    app.register_blueprint(mailgun_api)
    return app

# Create the app handle
app = create_mailgun_api()


if __name__ == '__main__':
    app.run()
