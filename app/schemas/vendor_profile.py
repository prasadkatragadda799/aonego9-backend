import json

from pydantic import BaseModel, Field


class CompCardOut(BaseModel):
    height: str = ""
    weight: str = ""
    bust: str = ""
    chest: str = ""
    waist: str = ""
    hip: str = ""
    shoe: str = ""
    age: int | None = None
    hair: str = ""
    eye: str = ""
    skin: str = ""


class CompCardUpdate(BaseModel):
    height: str | None = None
    weight: str | None = None
    bust: str | None = None
    chest: str | None = None
    waist: str | None = None
    hip: str | None = None
    shoe: str | None = None
    age: int | None = None
    hair: str | None = None
    eye: str | None = None
    skin: str | None = None


class VendorProfileDetailsOut(BaseModel):
    vendor_id: str
    experience: str = ""
    training: str = ""
    languages: str = ""
    overview: str = ""
    comp_card: CompCardOut = Field(default_factory=CompCardOut)
    stats: list[dict] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    services: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)
    availability: list[str] = Field(default_factory=list)
    scene_data: list[dict] = Field(default_factory=list)
    spaces: list[dict] = Field(default_factory=list)
    equipment: list[dict] = Field(default_factory=list)
    reels: list[dict] = Field(default_factory=list)


class VendorProfileDetailsUpdate(BaseModel):
    experience: str | None = None
    training: str | None = None
    languages: str | None = None
    overview: str | None = None
    comp_card: CompCardUpdate | None = None
    stats: list[dict] | None = None
    tags: list[str] | None = None
    services: list[str] | None = None
    amenities: list[str] | None = None
    availability: list[str] | None = None
    scene_data: list[dict] | None = None
    spaces: list[dict] | None = None
    equipment: list[dict] | None = None
    reels: list[dict] | None = None


def _loads(raw: str, fallback):
    if not raw:
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def details_to_out(row) -> VendorProfileDetailsOut:
    return VendorProfileDetailsOut(
        vendor_id=row.vendor_id,
        experience=row.experience,
        training=row.training,
        languages=row.languages,
        overview=row.overview,
        comp_card=CompCardOut(
            height=row.height,
            weight=row.weight,
            bust=row.bust,
            chest=row.chest,
            waist=row.waist,
            hip=row.hip,
            shoe=row.shoe,
            age=row.age,
            hair=row.hair,
            eye=row.eye,
            skin=row.skin,
        ),
        stats=_loads(row.stats_json, []),
        tags=_loads(row.tags_json, []),
        services=_loads(row.services_json, []),
        amenities=_loads(row.amenities_json, []),
        availability=_loads(row.availability_json, []),
        scene_data=_loads(row.scene_data_json, []),
        spaces=_loads(row.spaces_json, []),
        equipment=_loads(row.equipment_json, []),
        reels=_loads(row.reels_json, []),
    )


def apply_update(row, body: VendorProfileDetailsUpdate) -> None:
    data = body.model_dump(exclude_none=True)
    comp = data.pop("comp_card", None)
    if comp:
        for key, value in comp.items():
            setattr(row, key, value)

    json_map = {
        "stats": "stats_json",
        "tags": "tags_json",
        "services": "services_json",
        "amenities": "amenities_json",
        "availability": "availability_json",
        "scene_data": "scene_data_json",
        "spaces": "spaces_json",
        "equipment": "equipment_json",
        "reels": "reels_json",
    }
    for key, value in data.items():
        if key in json_map:
            setattr(row, json_map[key], json.dumps(value))
        else:
            setattr(row, key, value)
