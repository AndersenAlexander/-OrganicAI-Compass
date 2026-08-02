from fastapi import APIRouter

router = APIRouter()


@router.post("/projects/generate")
async def generate_project(payload: dict) -> dict:
    return {"status": "mock", "request": payload}


@router.get("/projects")
async def list_projects() -> list[dict]:
    return []


@router.get("/growth")
async def list_growth() -> list[dict]:
    return []


@router.post("/growth")
async def create_growth_event(payload: dict) -> dict:
    return {"status": "mock", "event": payload}


@router.get("/learning-paths")
async def list_learning_paths() -> list[dict]:
    return []


@router.post("/learning-paths/recommend")
async def recommend_learning_paths(payload: dict) -> dict:
    return {"status": "mock", "request": payload, "recommendations": []}


@router.post("/constitution/generate")
async def generate_constitution(payload: dict) -> dict:
    return {"status": "mock", "request": payload}


@router.get("/constitution/me")
async def get_constitution() -> dict:
    return {"status": "mock"}


@router.get("/scenarios")
async def list_scenarios() -> list[dict]:
    return []


@router.post("/scenarios/compare")
async def compare_scenarios(payload: dict) -> dict:
    return {"status": "mock", "request": payload}
