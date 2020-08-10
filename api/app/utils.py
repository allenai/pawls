from pythonjsonlogger import jsonlogger

class StackdriverJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom log JSON log formatter that adds the severity member, allowing
    end users to filter logs by the level of the log message emitted.

    TODO: Parse request logs and add fields for each request element (user-agent
    processing time, etc)

    TODO:Add a timestamp that's used in place of Stackdriver's records (which
    reflect the time the log was written to Stackdriver, I think).
    """
    def add_fields(self, log_record, record, message_dict):
        super(StackdriverJsonFormatter, self).add_fields(log_record, record,
            message_dict)
        log_record['severity'] = record.levelname
