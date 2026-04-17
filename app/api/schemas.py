"""Pydantic schemas for /api/calculate request and response."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GroupComp(BaseModel):
    """Team composition for a single operational group."""

    gis: int = Field(1, ge=0, description="Number of GIS operators")
    rasr: int = Field(1, ge=0, description="Number of RASR operators")
    fol: int = Field(0, ge=0, description="Number of FOL operators")


class GroupInput(BaseModel):
    """Input data for a single group."""

    name: str
    difKm: float = Field(0.0, ge=0.0, description="Difference km to resolve")
    pmKm: float = Field(0.0, ge=0.0, description="PM network km")
    comp: GroupComp = GroupComp()


class DashboardParams(BaseModel):
    """Global dashboard parameters."""

    vMin: float = Field(1.5, gt=0.0, description="Min correlation rate km/h/person")
    vMax: float = Field(3.0, gt=0.0, description="Max correlation rate km/h/person")
    oreSapt: float = Field(4.0, gt=0.0, description="Hours per week dedicated")
    saptAn: int = Field(47, gt=0, description="Active weeks per year")
    tDif: float = Field(6.0, gt=0.0, description="Target months for differences")
    tPM: float = Field(36.0, gt=0.0, description="Target months for PM network")
    pctFOL: float = Field(0.0, ge=0.0, le=100.0, description="FOL time % for correlation")
    factorC: float = Field(1.0, ge=1.0, description="Complexity factor applied to ETA")


class CalculateRequest(BaseModel):
    """Full payload for /api/calculate."""

    params: DashboardParams = DashboardParams()
    groups: list[GroupInput] = []


class GroupResult(BaseModel):
    """Computed results for one group."""

    name: str
    nr_echipe: int
    ore_an: float
    ore_nec_dif: float
    ore_nec_pm: float
    luni_dif: float
    luni_pm: float
    ok_dif: bool
    ok_pm: bool


class ScenarioResult(BaseModel):
    """ETA at a specific rate (worst / medium / best)."""

    rate: float
    max_eta_dif_years: float
    max_eta_pm_years: float


class CalculateResponse(BaseModel):
    """Full response from /api/calculate."""

    rata_medie: float
    groups: list[GroupResult]
    scenarios: list[ScenarioResult]
