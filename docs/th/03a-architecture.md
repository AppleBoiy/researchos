# 3a. สถาปัตยกรรมระบบ

- ที่มา: มาจาก requirements — ระบบต้องการส่วนประกอบกี่ส่วน?
- จุดประสงค์: กำหนดโครงสร้างระดับสูงของ services และการสื่อสารระหว่างกัน
- ถ้าไม่มี: นักพัฒนาตัดสินใจแยกกัน ทำให้เกิดความขัดแย้งตอน integrate

---

## ภาพรวมระบบ

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

## Flow การถ่ายโอนไฟล์

- ที่มา: requirement หลัก — old_server → our_app → target_server
- จุดประสงค์: แสดงให้เห็นว่า ResearchOS ทำหน้าที่เป็น relay ระหว่าง source และ destination
- ถ้าไม่มี: feature การถ่ายโอนไม่มีความชัดเจนว่าแต่ละขั้นตอนเป็นของใคร

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

- ที่มา: มาจากการตัดสินใจเรื่อง tech stack และ deployment requirements
- จุดประสงค์: กำหนดว่าแต่ละ container ทำอะไรและมีขอบเขตอย่างไร
- ถ้าไม่มี: ความรับผิดชอบทับซ้อนกัน services ผูกติดกันแน่นเกินไป

| Service | Image | หน้าที่ |
|---------|-------|---------|
| api | python:3.11 (custom) | Flask REST API, business logic, SSH/S3 transfer |
| db | postgres:15 | จัดเก็บ metadata แบบถาวร |
| storage | local volume | จัดเก็บ file blobs (temp chunks + final files) |
