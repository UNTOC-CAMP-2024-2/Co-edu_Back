import logging
import logging.config
import logging.handlers

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s - %(name)s - %(message)s",
        },
    },
    "handlers": {
        "user_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "user.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "default",
        },
        "assignment_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "assignment.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "default",
        },
        "classroom_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "classroom.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "default",
        },
        "live_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "live.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "default",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "user": {
            "handlers": ["user_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "assignment": {
            "handlers": ["assignment_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "classroom": {
            "handlers": ["classroom_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "live": {
            "handlers": ["live_file", "console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
