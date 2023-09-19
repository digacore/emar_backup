from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField, BooleanField
from wtforms.validators import DataRequired


class CompanyMergeSelectForm(FlaskForm):
    name = StringField("Name", [DataRequired()])
    default_sftp_username = StringField(
        "Default SFTP Username", default=None, filters=[lambda x: x or None]
    )
    default_sftp_password = StringField(
        "Default SFTP Password", default=None, filters=[lambda x: x or None]
    )
    pcc_org_id = StringField("PCC Org ID", default=None, filters=[lambda x: x or None])
    merged_locations_list = SelectMultipleField("Locations")
    merged_computers_list = SelectMultipleField("Computers")

    def __init__(self, *args, **kwargs):
        super(CompanyMergeSelectForm, self).__init__(*args, **kwargs)
        self.merged_locations_list.choices = [
            str(location.id) for location in kwargs["locations"]
        ]
        self.merged_computers_list.choices = [
            str(computer.id) for computer in kwargs["computers"]
        ]


class LocationMergeSelectForm(FlaskForm):
    name = StringField("Name", [DataRequired()])
    company_name = StringField(
        "Company Name", default=None, filters=[lambda x: x or None]
    )
    default_sftp_path = StringField(
        "Default SFTP Username", default=None, filters=[lambda x: x or None]
    )
    pcc_fac_id = StringField(
        "Default SFTP Password", default=None, filters=[lambda x: x or None]
    )
    use_pcc_backup = BooleanField("Use PCC Backup", default=False)
    merged_computers_list = SelectMultipleField("Computers")

    def __init__(self, *args, **kwargs):
        super(LocationMergeSelectForm, self).__init__(*args, **kwargs)
        self.merged_computers_list.choices = [
            str(computer.id) for computer in kwargs["computers"]
        ]
