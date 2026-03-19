"""Pydantic schemas for the core tenant backbone."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AddressCreate(BaseModel):
    street_line_1: str
    street_line_2: str | None = None
    postal_code: str
    city: str
    state: str | None = None
    country_code: str = Field(min_length=2, max_length=2)


class AddressRead(AddressCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str


class TenantCreate(BaseModel):
    code: str
    name: str
    legal_name: str | None = None
    default_locale: str = "de"
    default_currency: str = "EUR"
    timezone: str = "Europe/Berlin"


class TenantOnboardingCreate(BaseModel):
    tenant: TenantCreate
    initial_branch: "BranchCreate"
    initial_mandate: "MandateCreate"
    initial_settings: list["TenantSettingCreate"] = Field(default_factory=list)


class TenantUpdate(BaseModel):
    name: str | None = None
    legal_name: str | None = None
    default_locale: str | None = None
    default_currency: str | None = None
    timezone: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class TenantListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    code: str
    name: str
    status: str
    version_no: int


class TenantRead(TenantListItem):
    legal_name: str | None
    default_locale: str
    default_currency: str
    timezone: str
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class TenantStatusUpdate(BaseModel):
    status: str


class BranchCreate(BaseModel):
    tenant_id: str
    code: str
    name: str
    address_id: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class BranchUpdate(BaseModel):
    name: str | None = None
    address_id: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class BranchListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    code: str
    name: str
    status: str
    version_no: int


class BranchRead(BranchListItem):
    address_id: str | None
    contact_email: str | None
    contact_phone: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class MandateCreate(BaseModel):
    tenant_id: str
    branch_id: str
    code: str
    name: str
    external_ref: str | None = None
    notes: str | None = None


class MandateUpdate(BaseModel):
    name: str | None = None
    external_ref: str | None = None
    notes: str | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class MandateListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    branch_id: str
    code: str
    name: str
    status: str
    version_no: int


class MandateRead(MandateListItem):
    external_ref: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class TenantSettingCreate(BaseModel):
    tenant_id: str
    key: str
    value_json: dict[str, object]


class TenantSettingUpdate(BaseModel):
    value_json: dict[str, object] | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class TenantSettingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    key: str
    status: str
    version_no: int


class TenantSettingRead(TenantSettingListItem):
    value_json: dict[str, object]
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class LookupValueCreate(BaseModel):
    tenant_id: str | None = None
    domain: str
    code: str
    label: str
    description: str | None = None
    sort_order: int = 100


class LookupValueUpdate(BaseModel):
    label: str | None = None
    description: str | None = None
    sort_order: int | None = None
    status: str | None = None
    archived_at: datetime | None = None
    version_no: int | None = None


class LookupValueListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str | None
    domain: str
    code: str
    label: str
    status: str
    version_no: int


class LookupValueRead(LookupValueListItem):
    description: str | None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    created_by_user_id: str | None
    updated_by_user_id: str | None
    archived_at: datetime | None


class TenantOnboardingRead(BaseModel):
    tenant: TenantRead
    initial_branch: BranchRead
    initial_mandate: MandateRead
    initial_settings: list[TenantSettingRead]


TenantOnboardingCreate.model_rebuild()
