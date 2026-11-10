from flask import Flask, render_template

app = Flask(__name__)

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


@app.route("/")
def index():
    return _render()
