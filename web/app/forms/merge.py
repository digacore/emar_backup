from flask_wtf import FlaskForm
from wtforms import StringField, SelectMultipleField
from wtforms.validators import DataRequired


class CompanyMergeFirstStepForm(FlaskForm):
    secondary_company = StringField("Secondary company for merge", [DataRequired()])


class CompanyMergeSelectForm(FlaskForm):
    name = StringField("Name", [DataRequired()])
    default_sftp_username = StringField("Default SFTP Username")
    default_sftp_password = StringField("Default SFTP Password")
    pcc_org_id = StringField("PCC Org ID")
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
