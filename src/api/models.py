from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request chat ke agent."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Pesan ke agent"
    )
    session_id: str = Field(
        default="",
        pattern=r"^[a-f0-9-]{0,36}$",
        description="Session ID (UUID format)"
    )
    customer_name: str = Field(default="", max_length=100)

    model_config = {"json_schema_extra": {"examples": [{"message": "Cari produk polo"}]}}


class ChatResponse(BaseModel):
    """Response dari chat endpoint."""
    response: str = Field(description="Respons dari agent")
    session_id: str = Field(description="ID sesi percakapan")
    request_id: str = Field(description="ID unik request")


class CreateSessionRequest(BaseModel):
    """Request buat session baru."""
    customer_name: str = Field(default="", max_length=100)


class SessionResponse(BaseModel):
    """Response session."""
    id: str = Field(description="Session ID")
    customer_name: str = Field(description="Nama customer")
    status: str = Field(description="Status session")


class CreateSessionResponse(BaseModel):
    """Response buat session baru."""
    session_id: str = Field(description="Session ID baru")
    status: str = Field(description="Status session")


class ErrorResponse(BaseModel):
    """Response error unified."""
    success: bool = Field(default=False, description="Status sukses")
    error: str = Field(description="Pesan error")
    detail: str | None = Field(default=None, description="Detail error")
    request_id: str | None = Field(default=None, description="ID request")


class HealthCheckResult(BaseModel):
    """Result dari health check."""
    status: str = Field(description="Status check")
    message: str | None = Field(default=None, description="Pesan tambahan")
    enabled: bool | None = Field(default=None, description="Status enabled")
    model: str | None = Field(default=None, description="Model name")
    products_count: int | None = Field(default=None, description="Jumlah produk")


class HealthResponse(BaseModel):
    """Response health check."""
    status: str = Field(description="Status overall")
    service: str = Field(description="Nama service")
    version: str = Field(description="Versi aplikasi")
    checks: dict[str, HealthCheckResult] = Field(description="Detail checks")
