"""DC bias calculation for an NPN common-emitter voltage-divider bias circuit.

Pure engineering module: no Flask, no HTTP, no HTML.
All values are SI units (volts, ohms, amperes); beta is dimensionless.
"""


def _require_positive(name, value):
    if value <= 0:
        raise ValueError(f"{name} ต้องมากกว่า 0")


def calculate_dc_bias(vcc, r1, r2, rc, re, beta, vbe):
    """Return the DC operating point under the forward-active approximation.

    vcc, vbe in volts; r1, r2, rc, re in ohms; beta dimensionless.
    Raises ValueError with a Thai message when an input is out of range.
    """
    _require_positive("VCC", vcc)
    _require_positive("R1", r1)
    _require_positive("R2", r2)
    _require_positive("RC", rc)
    _require_positive("RE", re)
    _require_positive("β", beta)
    if not 0 <= vbe < vcc:
        raise ValueError("VBE ต้องอยู่ระหว่าง 0 ถึง VCC")

    vth = vcc * r2 / (r1 + r2)
    rth = r1 * r2 / (r1 + r2)

    ib = (vth - vbe) / (rth + (beta + 1) * re)
    ic = beta * ib
    ie = (beta + 1) * ib

    ve = ie * re
    vb = ve + vbe
    vc = vcc - ic * rc
    vce = vc - ve

    ic_sat = vcc / (rc + re)
    warnings = []

    if vth <= vbe:
        region = "cutoff"
        ib = ic = ie = 0.0
        ve = 0.0
        vb = vth
        vc = vcc
        vce = vcc
        warnings.append(
            f"VTH ({vth:.3f} V) ≤ VBE ({vbe:.2f} V): ทรานซิสเตอร์อยู่ในช่วง "
            "Cutoff ค่าที่แสดงเป็นการประมาณ ไม่ใช่ผลจำลองที่แม่นยำ"
        )
    elif vce <= 0:
        region = "saturation"
        warnings.append(
            f"VCE ที่คำนวณได้ ({vce:.3f} V) ≤ 0 V: สมการ Forward-Active ใช้ไม่ได้ "
            f"ทรานซิสเตอร์อิ่มตัว (IC(sat) ≈ {ic_sat * 1e3:.3f} mA) "
            "ค่าที่แสดงไม่ควรนำไปใช้โดยไม่ตรวจสอบเพิ่มเติม"
        )
    else:
        region = "active"

    return {
        "vth": vth,
        "rth": rth,
        "ib": ib,
        "ic": ic,
        "ie": ie,
        "vb": vb,
        "ve": ve,
        "vc": vc,
        "vce": vce,
        "ic_sat": ic_sat,
        "region": region,
        "warnings": warnings,
    }
