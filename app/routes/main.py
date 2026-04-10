from datetime import datetime

from flask import Blueprint, Response, current_app, jsonify, render_template, request, url_for

from app.services.attendance_service import get_dashboard_data, get_export_data

main_bp = Blueprint("main", __name__)


def _get_default_filter_date() -> str:
    return datetime.now().strftime("%Y-%m-%d")


@main_bp.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200


@main_bp.route("/")
def index():
    page = max(request.args.get("page", default=1, type=int), 1)
    devname = request.args.get("devname", "all")
    default_date = _get_default_filter_date()
    start_date = request.args.get("start_date") or default_date
    end_date = request.args.get("end_date") or default_date
    device_options, columns, data, total_rows, has_next, error = get_dashboard_data(
        page=page,
        page_size=current_app.config["PAGE_SIZE"],
        devname=devname,
        start_date=start_date,
        end_date=end_date,
    )

    return render_template(
        "index.html",
        columns=columns,
        data=data,
        page=page,
        devname=devname,
        start_date=start_date,
        end_date=end_date,
        error=error,
        device_options=device_options,
        total_rows=total_rows,
        current_row_count=len(data),
        has_next=has_next,
        export_url=url_for(
            "main.export_txt",
            devname=devname,
            start_date=start_date or "",
            end_date=end_date or "",
        ),
    )


@main_bp.route("/export/txt")
def export_txt():
    devname = request.args.get("devname", "all")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    columns, rows, error = get_export_data(
        devname=devname,
        start_date=start_date,
        end_date=end_date,
    )
    if error:
        return Response(
            f"Loi export du lieu: {error}",
            status=500,
            content_type="text/plain; charset=utf-8",
        )

    lines = ["\t".join(columns)]
    for row in rows:
        lines.append("\t".join("" if value is None else str(value) for value in row))

    content = "\n".join(lines)
    filename = f"cham_cong_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    return Response(
        content.encode("utf-8-sig"),
        content_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
