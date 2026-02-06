# Use a slim Python base image based on the project's requirements
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Install uv, the package manager used in the project, which is faster than pip
RUN pip install uv

# Copy the dependency definition files
COPY pyproject.toml uv.lock .python-version ./

# Install dependencies using the lock file for reproducible builds
RUN uv pip sync --no-cache uv.lock

# Copy the rest of the application source code
COPY . .

# Expose the port that the API server will run on
EXPOSE 8080

# The command to run the Uvicorn server for the FastAPI application
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
