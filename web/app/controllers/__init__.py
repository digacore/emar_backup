# flake8: noqa F401
from .alert import check_and_alert
from .database import create_superuser, init_db, empty_to_stable
from .stat_company_location import update_companies_locations_statistic
