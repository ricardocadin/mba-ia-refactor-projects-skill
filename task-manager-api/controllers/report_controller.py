from flask import jsonify

from views.report_view import summary_to_dict, user_report_to_dict


class ReportController:
    def __init__(self, service):
        self._service = service

    def summary(self):
        return jsonify(summary_to_dict(self._service.summary())), 200

    def user(self, user_id):
        user, statistics = self._service.user_report(user_id)
        return jsonify(user_report_to_dict(user, statistics)), 200
