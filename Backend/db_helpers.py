import mysql.connector
from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, DB_PORT
print(f"Connecting to MySQL database at {DB_HOST}:{DB_PORT} with user {DB_USER} and database {DB_NAME}")

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        # MySQL TIMESTAMP values are displayed in the session time zone.
        cursor = connection.cursor()
        cursor.execute("SET time_zone = '+05:30'")
        cursor.close()
        return connection
    except Exception as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def insert_into_visitors(name, address, email, purpose):
    connection = get_db_connection()
    if connection is None:
        return False
    cursor = None
    try:
        cursor = connection.cursor()
        query = "INSERT INTO visitors (name, address, email, purpose) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, address, email, purpose))
        connection.commit()
        print(f"Inserted visitor: {name}, {address}, {email}, {purpose}")
        return True
    except Exception as e:
        print(f"Error while inserting into visitors table: {e}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def store_email_otp(email, otp):
    """Store an OTP by email with a five-minute expiry."""
    connection = get_db_connection()
    if connection is None:
        return False
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO email_otps (email, otp_code, expires_at) "
            "VALUES (%s, %s, DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 5 MINUTE))",
            (email, otp),
        )
        connection.commit()
        return True
    except Exception as exc:
        connection.rollback()
        print(f"Error while storing email OTP: {exc}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def check_email_otp(email, otp):
    """Check the latest OTP and its expiry using the database clock."""
    connection = get_db_connection()
    if connection is None:
        return False
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT o.id "
            "FROM email_otps o "
            "WHERE o.email = %s "
            "ORDER BY o.created_at DESC, o.id DESC LIMIT 1 FOR UPDATE",
            (email,),
        )
        record = cursor.fetchone()
        if record is None:
            connection.commit()
            return False

        otp_id = record[0]
        cursor.execute(
            "SELECT id FROM email_otps "
            "WHERE id = %s AND otp_code = %s "
            "AND expires_at > CURRENT_TIMESTAMP AND verified_at IS NULL",
            (otp_id, otp),
        )
        if cursor.fetchone() is None:
            connection.commit()
            return False

        cursor.execute(
            "UPDATE email_otps SET verified_at = CURRENT_TIMESTAMP WHERE id = %s",
            (otp_id,),
        )
        connection.commit()
        return True
    except Exception as exc:
        connection.rollback()
        print(f"Error while checking email OTP: {exc}")
        return False
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()

