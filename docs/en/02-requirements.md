# 2. Requirements Analysis

- Origin: Comes after Planning, translates business needs into structured requirements
- Purpose: Define exactly what the system must do before any design decisions are made
- Without it: Developers build based on assumptions, leading to a system that doesn't solve the actual problem

---

## Stakeholders

- Origin: Identifying who is affected by or has influence over the system
- Purpose: Ensure requirements are gathered from the right people
- Without it: Requirements reflect only one perspective and miss critical needs

- Primary user: Researcher (solo, self-hosted)
- External dependency: LLM API provider (OpenAI / Gemini)

---

## Functional Requirements

- Origin: Derived from user stories — what the system must do
- Purpose: Define the capabilities the system must provide
- Without it: No clear contract between what's built and what's needed

| ID | Requirement |
|----|-------------|
| FR-01 | User can register and login via JWT |
| FR-02 | User can upload a file with metadata (title, description, category, tags) |
| FR-03 | User can list documents filtered by tag, category, or file type |
| FR-04 | User can download a file by document ID |
| FR-05 | User can delete a document |
| FR-06 | User can transfer files from old_server (SSH) through our_app to target_server (SSH or S3/bucket) |
| FR-07 | System supports SSH as both source and destination for file transfer |
| FR-08 | System supports S3-compatible bucket as transfer destination |
| FR-09 | User can upload large files via chunked multipart POST (max 10MB per chunk) |
| FR-10 | System reassembles chunks and stores the complete file |
| FR-11 | User can check upload/transfer status via status endpoint |
| FR-12 | User can view and add tags to a document |
| FR-13 | System can extract text from PDF and suggest tags via LLM API |
| FR-14 | User can accept or reject each suggested tag |

---

## Non-Functional Requirements

- Origin: Derived from operational and quality expectations
- Purpose: Define how well the system must perform, not just what it does
- Without it: A system can be functionally correct but unusable in practice

| ID | Requirement |
|----|-------------|
| NFR-01 | All services run via Docker Compose with a single `docker compose up` |
| NFR-02 | CI pipeline runs lint and pytest on every push |
| NFR-03 | Pytest coverage >= 80% on API layer |
| NFR-04 | System handles files of any size via chunked upload |
| NFR-05 | Auth is JWT-based |

---

## User Stories

- Origin: Written from the user's perspective to capture intent and value
- Purpose: Keep requirements grounded in real usage, not just technical features
- Without it: Requirements become abstract and disconnected from actual user needs

```
As a researcher,
I want to upload a PDF with metadata,
So that I can find and retrieve it later.

As a researcher,
I want to transfer files from an old SSH server through ResearchOS to a target server (SSH or S3),
So that I can move research data between environments without manual SCP or AWS CLI commands.

As a researcher,
I want the system to suggest tags from my document content,
So that I don't have to categorize everything manually.

As a researcher,
I want to transfer large files reliably,
So that uploads don't fail due to network interruptions.
```

---

## Constraints

- Origin: External limitations that shape what's possible
- Purpose: Set boundaries that the design must work within
- Without it: Design may propose solutions that are technically or practically impossible

- 1 developer, ~4–6 weeks
- Must run entirely on Docker, no managed cloud services required
- SSH credentials for source/target servers must be stored securely
- S3/bucket credentials managed via environment variables
- LLM API calls are external and incur cost — must be used sparingly
