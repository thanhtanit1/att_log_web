from datetime import datetime
import socket
from time import monotonic

from flask import current_app


PLACEHOLDER_VALUES = {"change-me", "your-password", "replace-me", "password"}
BASELINE_ATTENDANCE_DATE = datetime(2026, 1, 1)
DEVICE_OPTIONS_CACHE_SECONDS = 300
_device_options_cache = {"expires_at": 0.0, "options": []}


def _escape_odbc_value(value):
    return "{" + str(value).replace("}", "}}") + "}"


def _build_connection_string(config):
    return ";".join(
        (
            f"DRIVER={_escape_odbc_value(config['DB_DRIVER'])}",
            f"SERVER={_escape_odbc_value(config['DB_SERVER'])}",
            f"DATABASE={_escape_odbc_value(config['DB_DATABASE'])}",
            f"UID={_escape_odbc_value(config['DB_UID'])}",
            f"PWD={_escape_odbc_value(config['DB_PWD'])}",
            f"Encrypt={_escape_odbc_value(config['DB_ENCRYPT'])}",
            f"TrustServerCertificate={_escape_odbc_value(config['DB_TRUST_CERT'])}",
            f"Connection Timeout={_escape_odbc_value(config['DB_TIMEOUT'])}",
        )
    ) + ";"


def _parse_server_endpoint(server_value):
    raw_value = str(server_value or "").strip()
    if not raw_value:
        return None, None

    if "," in raw_value:
        host, port_text = raw_value.rsplit(",", 1)
        try:
            return host.strip(), int(port_text.strip())
        except ValueError:
            return raw_value, None

    return raw_value, 1433


def _check_server_reachability(config):
    host, port = _parse_server_endpoint(config.get("DB_SERVER"))
    if not host or not port:
        return

    timeout = max(1, min(int(config.get("DB_TIMEOUT", 10)), 5))
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return
    except OSError as exc:
        raise RuntimeError(
            f"Khong mo duoc ket noi TCP toi SQL Server {host}:{port}. Kiem tra firewall, NAT port, whitelist IP cua Render va dam bao SQL Server cho phep ket noi tu Internet. Chi tiet: {exc}"
        ) from exc


def _validate_db_settings(config):
    missing_settings = [
        key for key in ("DB_SERVER", "DB_DATABASE", "DB_UID", "DB_PWD") if not config.get(key)
    ]
    if missing_settings:
        missing_text = ", ".join(missing_settings)
        raise RuntimeError(f"Thieu bien moi truong DB: {missing_text}")

    password = str(config.get("DB_PWD", "")).strip().lower()
    if password in PLACEHOLDER_VALUES:
        raise RuntimeError(
            "DB_PWD dang la gia tri mau trong file .env. Cap nhat mat khau SQL Server thuc te truoc khi chay app."
        )


def get_connection():
    _validate_db_settings(current_app.config)
    _check_server_reachability(current_app.config)

    try:
        import pyodbc
    except Exception as exc:
        raise RuntimeError(f"Khong the import pyodbc: {exc}") from exc

    conn_str = _build_connection_string(current_app.config)
    try:
        connection = pyodbc.connect(conn_str, timeout=current_app.config.get("DB_TIMEOUT", 10))
        timeout = current_app.config.get("DB_TIMEOUT")
        if timeout:
            try:
                connection.timeout = timeout
            except Exception:
                pass
        return connection
    except pyodbc.Error as exc:
        error_text = str(exc)
        if "Login failed for user" in error_text:
            raise RuntimeError(
                f"Dang nhap SQL Server that bai cho tai khoan '{current_app.config['DB_UID']}'. Kiem tra lai DB_UID/DB_PWD trong file .env."
            ) from exc
        if "Login timeout expired" in error_text:
            host, port = _parse_server_endpoint(current_app.config.get("DB_SERVER"))
            raise RuntimeError(
                f"Ket noi toi SQL Server {host}:{port or 'default'} bi timeout. Kha nang cao Render khong truy cap duoc server/port nay hoac SQL Server phan hoi qua cham."
            ) from exc
        raise RuntimeError(f"Khong the ket noi SQL Server: {exc}") from exc


def _apply_cursor_timeout(cursor):
    return None


def _fetch_device_options(cursor):
    cursor.execute(
        """
         SELECT DISTINCT de.DevName
        FROM dbo.tbl_3_Device de
        WHERE de.DevName IN
			('Hà Nam 01',
			'Hà Nam 02',
			'Kho heo Dak Lak',
			'VP Biên Hoà',
			'VP Bình Dương',
			'VP Đồng Nai',
			'VP Long An',
			'VP Nha Trang',
			'VP Sale Ha Noi')
        ORDER BY de.DevName
        """
    )
    return [row[0] for row in cursor.fetchall()]


def _get_cached_device_options(cursor):
    now = monotonic()
    if _device_options_cache["expires_at"] > now:
        return list(_device_options_cache["options"])

    options = _fetch_device_options(cursor)
    _device_options_cache["options"] = list(options)
    _device_options_cache["expires_at"] = now + DEVICE_OPTIONS_CACHE_SECONDS
    return options


def _fetch_data(cursor, resolved_page_size, offset, devname=None, start_date=None, end_date=None):
    where_conditions, params, filter_error = build_filter_conditions(
        devname=devname,
        start_date=start_date,
        end_date=end_date,
    )
    if filter_error:
        return [], [], 0, str(filter_error)

    where_clause = " AND ".join(where_conditions)
    query = f"""
    SELECT
        de.DevName AS [Vi Tri may cham cong],
        att.[PIN] AS [ID cham cong],
        CONVERT(varchar(10), att.[AttTime], 23) AS [Ngay cham cong],
        CONVERT(varchar(8), att.[AttTime], 108) AS [Gio cham cong]
    FROM dbo.tbl_3_AttLog att
    JOIN dbo.tbl_3_Device de
        ON de.DevSN = att.DevSN
    WHERE {where_clause}
    ORDER BY att.AttTime DESC
    OFFSET {offset} ROWS FETCH NEXT {resolved_page_size + 1} ROWS ONLY;
    """

    cursor.execute(query, params)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    has_next = len(rows) > resolved_page_size
    visible_rows = rows[:resolved_page_size]
    return columns, visible_rows, has_next, None


def get_device_options():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        _apply_cursor_timeout(cursor)
        options = _fetch_device_options(cursor)
        cursor.close()
        conn.close()
        return options, None
    except Exception as exc:
        return [], str(exc)


def build_filter_conditions(devname=None, start_date=None, end_date=None):
    conditions = ["att.AttTime >= ?"]
    params = [BASELINE_ATTENDANCE_DATE]

    if devname and devname.lower() != "all":
        conditions.append("de.DevName = ?")
        params.append(devname)

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            conditions.append("att.AttTime >= ?")
            params.append(start_dt)
        except ValueError:
            return None, None, f"Ngay bat dau khong hop le: {start_date}"

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            conditions.append("att.AttTime <= ?")
            params.append(end_dt)
        except ValueError:
            return None, None, f"Ngay ket thuc khong hop le: {end_date}"

    return conditions, params, None


def get_data(page=1, page_size=None, devname=None, start_date=None, end_date=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        _apply_cursor_timeout(cursor)
    except Exception as exc:
        return [], [], 0, str(exc)

    resolved_page_size = page_size or current_app.config["PAGE_SIZE"]
    page = max(page, 1)
    offset = (page - 1) * resolved_page_size

    try:
        columns, rows, has_next, error = _fetch_data(
            cursor,
            resolved_page_size,
            offset,
            devname=devname,
            start_date=start_date,
            end_date=end_date,
        )
        if error:
            cursor.close()
            conn.close()
            return [], [], 0, error
    except Exception as exc:
        cursor.close()
        conn.close()
        return [], [], 0, str(exc)

    cursor.close()
    conn.close()
    total_rows = offset + len(rows) + (1 if has_next else 0)
    return columns, rows, total_rows, None


def get_export_data(devname=None, start_date=None, end_date=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        _apply_cursor_timeout(cursor)
    except Exception as exc:
        return [], [], str(exc)

    where_conditions, params, filter_error = build_filter_conditions(
        devname=devname,
        start_date=start_date,
        end_date=end_date,
    )
    if filter_error:
        cursor.close()
        conn.close()
        return [], [], str(filter_error)

    where_clause = " AND ".join(where_conditions)
    query = f"""
    SELECT
        att.[PIN] AS [ID cham cong],
        CONVERT(varchar(10), att.[AttTime], 23) AS [Ngay cham cong],
        CONVERT(varchar(5), att.[AttTime], 108) AS [Gio cham cong]
    FROM dbo.tbl_3_AttLog att
    JOIN dbo.tbl_3_Device de
        ON de.DevSN = att.DevSN
    WHERE {where_clause}
    ORDER BY att.AttTime DESC
    """

    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
    except Exception as exc:
        cursor.close()
        conn.close()
        return [], [], str(exc)

    cursor.close()
    conn.close()
    return columns, rows, None


def get_dashboard_data(page=1, page_size=None, devname=None, start_date=None, end_date=None):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        _apply_cursor_timeout(cursor)
    except Exception as exc:
        return [], [], [], 0, False, str(exc)

    resolved_page_size = page_size or current_app.config["PAGE_SIZE"]
    page = max(page, 1)
    offset = (page - 1) * resolved_page_size

    try:
        device_options = _get_cached_device_options(cursor)
        columns, rows, has_next, error = _fetch_data(
            cursor,
            resolved_page_size,
            offset,
            devname=devname,
            start_date=start_date,
            end_date=end_date,
        )
        if error:
            cursor.close()
            conn.close()
            return [], [], [], 0, False, error
    except Exception as exc:
        cursor.close()
        conn.close()
        return [], [], [], 0, False, str(exc)

    cursor.close()
    conn.close()
    total_rows = offset + len(rows) + (1 if has_next else 0)
    return device_options, columns, rows, total_rows, has_next, None
