import pytest
from HardwareTester.forms import UploadSpecSheetForm, UploadTestPlanForm, AddValveForm, RunTestPlanForm

def test_upload_spec_sheet_form():
    form = UploadSpecSheetForm(data={"valve_id": 1})
    assert form.validate() is False  # File is missing
    form.spec_sheet.data = "dummy_file.pdf"
    assert form.validate() is True

def test_add_valve_form():
    form = AddValveForm(data={"name": "Valve A", "valve_type": "Mixing"})
    assert form.validate() is True
    form = AddValveForm(data={"name": "", "valve_type": "Mixing"})
    assert form.validate() is False

