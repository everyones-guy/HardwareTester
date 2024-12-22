from HardwareTester.extensions import db
from HardwareTester.models import Peripheral

def save_peripheral(name, properties):
    try:
        peripheral = Peripheral(name=name, properties=properties)
        db.session.add(peripheral)
        db.session.commit()
        return {"success": True, "message": f"Peripheral '{name}' saved successfully."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}
