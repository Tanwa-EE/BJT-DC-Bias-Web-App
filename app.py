import math

from flask import Flask, render_template, request

from dc_bias import calculate_dc_bias

app = Flask(__name__)

FIELD_LABELS = {
    "vcc": "VCC",
    "r1": "R1",
    "r2": "R2",
    "rc": "RC",
    "re": "RE",
    "beta": "β",
    "vbe": "VBE",
}

LENGTH_FIELDS = ("r1", "r2", "rc", "re")

SAMPLE_DEFAULTS = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rc": "2.2",
    "re": "1",
    "beta": "100",
    "vbe": "0.7",
}

DEFAULT_UNITS = {
    "unit_r1": "kohm",
    "unit_r2": "kohm",
    "unit_rc": "kohm",
    "unit_re": "kohm",
}


def _parse_float(form, name):
    raw = (form.get(name) or "").strip()
    label = FIELD_LABELS[name]
    if not raw:
        raise ValueError(f"กรุณากรอกค่า {label}")
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(f"ค่า {label} ไม่ใช่ตัวเลข") from None
    if not math.isfinite(value):
        raise ValueError(f"ค่า {label} ไม่ใช่ตัวเลข")
    return value


def _parse_number(form, name):
    return _parse_float(form, name)


def _parse_length(form, name):
    value = _parse_float(form, name)
    label = FIELD_LABELS[name]
    if value <= 0:
        raise ValueError(f"ค่า {label} ต้องมากกว่า 0")
    unit = form.get(f"unit_{name}", "kohm")
    if unit == "kohm":
        return value * 1000.0
    if unit == "ohm":
        return value
    raise ValueError(f"หน่วยของ {label} ไม่ถูกต้อง")


def _render(result=None, form_values=None, errors=None):
    values = dict(SAMPLE_DEFAULTS)
    values.update(DEFAULT_UNITS)
    if form_values:
        values.update(form_values)
    return render_template(
        "index.html",
        values=values,
        result=result,
        errors=errors or [],
    )


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return _render()

    form_values = {name: request.form.get(name, "") for name in FIELD_LABELS}
    form_values.update(
        {f"unit_{name}": request.form.get(f"unit_{name}", "kohm") for name in LENGTH_FIELDS}
    )

    errors = []
    parsed = {}
    for name in FIELD_LABELS:
        parser = _parse_length if name in LENGTH_FIELDS else _parse_number
        try:
            parsed[name] = parser(request.form, name)
        except ValueError as exc:
            errors.append(str(exc))

    result = None
    if not errors:
        try:
            result = calculate_dc_bias(**parsed)
        except ValueError as exc:
            errors.append(str(exc))

    return _render(result, form_values, errors)
