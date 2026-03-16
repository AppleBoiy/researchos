# 3b. Database Schema

- ที่มา: มาจาก data requirements ในขั้นตอนการวิเคราะห์ความต้องการ
- จุดประสงค์: กำหนดโครงสร้างของข้อมูลถาวรและความสัมพันธ์ระหว่าง entities
- ถ้าไม่มี: นักพัฒนาสร้าง table แบบ ad-hoc ทำให้ data model ไม่สอดคล้องกันและ migration วุ่นวาย

---

## Entity Relationship Diagram

```mermaid
erDiagram
    USER {
        uuid id PK
        varchar email
        varchar password_hash
        timestamp created_at
    }

    DOCUMENT {
        uuid id PK
        uuid user_id FK
        varchar title
        text description
        varchar file_path
        enum file_type
        bigint file_size
        varchar category
        timestamp created_at
        timestamp updated_at
    }

    TAG {
        uuid id PK
        varchar name
    }

    DOCUMENT_TAG {
        uuid document_id FK
        uuid tag_id FK
        bool accepted
    }

    UPLOAD_CHUNK {
        uuid id PK
        uuid document_id FK
        int chunk_index
        int total_chunks
        varchar temp_path
        timestamp created_at
    }

    TRANSFER_JOB {
        uuid id PK
        uuid document_id FK
        enum source_type
        varchar source_host
        varchar source_path
        enum dest_type
        varchar dest_host
        varchar dest_path
        enum status
        timestamp created_at
        timestamp updated_at
    }

    USER ||--o{ DOCUMENT : owns
    DOCUMENT ||--o{ DOCUMENT_TAG : has
    TAG ||--o{ DOCUMENT_TAG : used_in
    DOCUMENT ||--o{ UPLOAD_CHUNK : has
    DOCUMENT ||--o{ TRANSFER_JOB : has
```

---

## หมายเหตุ

- `file_type` enum: `pdf`, `latex`, `dataset`, `other`
- `source_type` / `dest_type` enum: `ssh`, `s3`, `local`
- `status` enum: `pending`, `in_progress`, `completed`, `failed`
- `DOCUMENT_TAG.accepted` ติดตามว่าผู้ใช้ยอมรับหรือปฏิเสธ tag ที่ LLM แนะนำ
- `UPLOAD_CHUNK` จะถูกลบหลังจาก reassembly เสร็จสมบูรณ์
