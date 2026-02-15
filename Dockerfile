# Use a Python image with uv pre-installed or copy it
FROM python:3.12-slim-bookworm

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: sync based on lockfile
# --no-dev: exclude dev dependencies
# --no-install-project: strictly install dependencies, not the project itself yet
RUN uv sync --frozen --no-dev --no-install-project

# Copy the rest of the application
COPY . .

# Place the virtual environment in the path
ENV PATH="/app/.venv/bin:$PATH"

# Streamlit-specific environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Expose port
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "app.py"]
