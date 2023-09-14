from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SelectMultipleField
from wtforms.validators import DataRequired


class MergeFirstStepForm(FlaskForm):
    secondary_company = StringField("Secondary company for merge", [DataRequired()])


class MainMergeForm(FlaskForm):
    name = StringField("Name", [DataRequired()])
    use_secondary_name = BooleanField("Use secondary company name")
    default_sftp_username = StringField("Default SFTP Username")
    use_secondary_sftp_username = BooleanField(
        "Use secondary company default SFTP Username"
    )
    default_sftp_password = StringField("Default SFTP Password")
    use_secondary_sftp_password = BooleanField(
        "Use secondary company default SFTP Password"
    )
    pcc_org_id = StringField("PCC Org ID")
    use_secondary_pcc_org_id = BooleanField("Use secondary company PCC Org ID")
    locations_list = SelectMultipleField("Locations")
    computers_list = SelectMultipleField("Computers")

    def __init__(self, *args, **kwargs):
        super(MainMergeForm, self).__init__(*args, **kwargs)
        self.locations_list.choices = [
            location.name for location in kwargs["locations"]
        ]
        self.computers_list.choices = [
            computer.computer_name for computer in kwargs["computers"]
        ]
