import logging
import psycopg2 as psql

logging.basicConfig(
    filename="app.log",
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

severity_to_logging_level = {
    "NOTSET": 0,
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
}


def error_handling(e: psql.Error):
    severity = getattr(e.diag, "severity", "UNKNOWN")
    if isinstance(e, psql.InterfaceError):
        logging.log(
            level=int(severity_to_logging_level[str(severity)]),
            msg=f"DatabaseError: InterfaceError occurred.\nMessage:{e.diag.message_primary}",
        )
    elif isinstance(e, psql.DatabaseError):
        if isinstance(e, psql.DataError):
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: DataError occurred.\nMessage:{e.diag.message_primary}",
            )
        elif isinstance(e, psql.OperationalError):
            lpogging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: OperationalError occurred.\nMessage:{e.diag.message_primary}",
            )
        elif isinstance(e, psql.IntegrityError):
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: IntegrityError occurred.\nMessage:{e.diag.message_primary}",
            )
        elif isinstance(e, psql.InternalError):
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: InternalError occurred.\nMessage:{e.diag.message_primary}",
            )
        elif isinstance(e, psql.ProgrammingError):
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: ProgrammingError occurred.\nMessage:{e.diag.message_primary}",
            )
        elif isinstance(e, psql.NotSupportedError):
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError: NotSupportedError occurred.\nMessage:{e.diag.message_primary}",
            )
        else:
            logging.log(
                level=int(severity_to_logging_level[str(severity)]),
                msg=f"DatabaseError occurred of no particular type.\nMessage:{e.diag.message_primary}",
            )
    elif isinstance(e, psql.Warning):
        logging.log(
            level=int(severity_to_logging_level[str(severity)]),
            msg=f"Warning occured occurred.\nMessage:{e.diag.message_primary}",
        )
    else:
        logger.log(f"Other error occurred: {type(e)}")