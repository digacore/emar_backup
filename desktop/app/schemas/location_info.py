from pydantic import BaseModel, ConfigDict


class LocationInfo(BaseModel):
    name: str
    company_name: str | None

    total_computers: int
    total_computers_offline: int
    primary_computers_offline: int
    default_sftp_path: str | None = None
    pcc_fac_id: int | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )
