# ADR — Beta uses gizmo backend

- status: confirmed

## 제약 (machine-readable)
@constraint DONT_BREAK | target=beta-api | rule=keep v1 response contract stable | adr=[[adr1]] | severity=warn
@constraint FIXED_ORDER | target=pipeline | rule=ingest before index | adr=[[adr1]] | severity=info
