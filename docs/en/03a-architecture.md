# 3a. Architecture

- Origin: Comes from requirements — how many moving parts does the system need?
- Purpose: Define the high-level structure of services and how they communicate
- Without it: Developers make local decisions that conflict with each other, creating integration nightmares

---

## System Overview

```mermaid
flowchart TD
    Client([API Client\ncurl / Postman])

    subgraph ResearchOS
        API[api\nFlask REST API]
        DB[(db\nPostgreSQL)]
        VOL[(storage\nLocal Volume)]
    end

    OldServer([old_server\nSSH])
    TargetSSH([target_server\nSSH])
    TargetS3([target_server\nS3 / Bucket])

    Client -->|HTTP requests| API
    API -->|read/write metadata| DB
    API -->|read/write blobs| VOL
    OldServer -->|pull file via SSH| API
    API -->|push file via SSH| TargetSSH
    API -->|push file via S3 SDK| TargetS3
```

---

## File Transfer Flow

- Origin: Core feature requirement — old_server → our_app → target_server
- Purpose: Show how ResearchOS acts as a relay between source and destination
- Without it: The transfer feature has no clear ownership of each step

```mermaid
sequenceDiagram
    participant C as Client
    participant A as ResearchOS API
    participant O as old_server (SSH)
    participant T as target_server (SSH / S3)

    C->>A: POST /transfers (source, destination config)
    A->>O: Connect via SSH, pull file (chunked)
    O-->>A: File chunks
    A->>A: Reassemble + store temporarily
    A->>T: Push file (SSH SCP or S3 SDK)
    T-->>A: Ack
    A-->>C: Transfer complete + document metadata
```

---

## Services

- Origin: Derived from tech stack decisions and deployment requirements
- Purpose: Define what each container does and its boundaries
- Without it: Responsibilities overlap and services become tightly coupled

| Service | Image | Responsibility |
|---------|-------|----------------|
| api | python:3.11 (custom) | Flask REST API, business logic, SSH/S3 transfer |
| db | postgres:15 | Persistent metadata storage |
| storage | local volume | File blob storage (temp chunks + final files) |
