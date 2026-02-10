# Use a slim Python base image compatible with your project's 3.12 requirement
FROM python:3.12-slim

# Copy uv directly from the official image for a faster, more reliable installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy the dependency definition files first to leverage Docker layer caching
COPY pyproject.toml uv.lock .python-version ./

# Install dependencies using the lock file for reproducible builds
# 'uv sync' is used here to match the Google Cloud recommended workflow
RUN uv sync --frozen --no-cache

# Copy the rest of the application source code
COPY . .

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED=1

# Set the server port to 8000 to avoid conflicts with other containers using 8080
ENV PORT=8000
EXPOSE 8000

# The command to run the application using uv to ensure the virtual environment is used
CMD ["uv", "run", "server.py"]