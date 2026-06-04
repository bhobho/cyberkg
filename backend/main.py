"""
main.py — FastAPI application entry point.

Starts the REST API that the React frontend calls.
Run with:  uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import close
from routes.graph import router as graph_router
from routes.attack_paths import router as attack_router
from routes.vulnerabilities import router as vuln_router

app = FastAPI(
    title="Cybersecurity Attack Knowledge Graph API",
    description="Explore malware, attack techniques, CVEs, and their relationships.",
    version="1.0.0",
)

# Allow the React dev server (port 5173) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graph_router)
app.include_router(attack_router)
app.include_router(vuln_router)


@app.get("/")
def root():
    return {"message": "Cybersecurity Knowledge Graph API is running. Visit /docs for the API explorer."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("shutdown")
def shutdown():
    close()
