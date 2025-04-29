from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.publications import router as publications_router
from api.routes.scripts import router as scripts_router
from api.routes.researchers import router as researchers_router
import uvicorn

app = FastAPI(
    title="Pub-it API",
    description="API for managing research publications",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(publications_router)
app.include_router(scripts_router)
app.include_router(researchers_router)

# Health check endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to Pub-it API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001) 