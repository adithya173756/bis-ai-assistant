# BIS AI Assistant

## AI-powered Intelligent Assistant for Indian Standards and BIS Services

An AI-powered knowledge assistant designed to help industries, manufacturers,
and consumers understand Indian Standards and Bureau of Indian Standards (BIS)
services through natural-language interaction.

The system uses Retrieval-Augmented Generation (RAG) to retrieve relevant
information from official BIS knowledge sources before generating an answer.

---

## SIH 2026 Problem Statement

**Problem Statement ID:** PS 26107

**Title:** AI-powered Intelligent Assistant for Indian Standards and BIS
Services for Industries and Consumers

**Category:** Software

**Theme:** Smart Automation

**Sponsoring Authority:** Bureau of Indian Standards (BIS), Department of
Consumer Affairs, Ministry of Consumer Affairs, Food & Public Distribution.

---

## Problem

Information related to Indian Standards, BIS certification, testing
laboratories, hallmarking, and conformity assessment is distributed across
different BIS resources.

Users may find it difficult to:

- Identify the applicable Indian Standard
- Understand BIS certification requirements
- Understand the certification process
- Find relevant testing laboratories
- Understand hallmarking requirements
- Determine whether certification is compulsory
- Navigate BIS terminology and procedures
- Find trustworthy information quickly

---

## Proposed Solution

BIS AI Assistant provides a natural-language interface through which users
can ask questions about Indian Standards and BIS services.

Instead of relying only on a general-purpose language model, the system first
retrieves relevant information from a curated BIS knowledge base.

The retrieved information is then supplied to the language model so that the
generated response remains grounded in the available BIS sources.

---

## Key Features

### 1. Indian Standards Assistance

Users can ask questions about available Indian Standards and related
information.

Example:

> What is IS 456:2000?

---

### 2. BIS Certification Guidance

The assistant can explain BIS product certification processes and
requirements using retrieved BIS information.

Example:

> What is the BIS certification process?

---

### 3. Testing Laboratory Guidance

Users can ask about BIS-recognized testing laboratories.

Example:

> Where can I find BIS recognized laboratories?

---

### 4. Hallmarking Guidance

The assistant provides information related to BIS hallmarking resources.

Example:

> What are the requirements for hallmarking?

---

### 5. Compulsory Certification

Users can ask about products and situations involving compulsory BIS
certification.

Example:

> What products require compulsory BIS certification?

---

### 6. Multilingual Interaction

The assistant can respond in the language used by the user.

Currently demonstrated with:

- English
- Hindi
- Telugu

Technical terminology, BIS terminology, and standard numbers are preserved
where appropriate.

---

### 7. Source-backed Responses

Responses include source information retrieved from BIS resources.

The interface provides:

- Standard / knowledge area
- Clause where reliably identified
- Page or web-page reference
- Official BIS source link

This improves transparency and helps users verify information.

---

## System Architecture

```text
                 USER
                   |
                   v
          Next.js Web Interface
                   |
                   v
             FastAPI Backend
                   |
                   v
          Natural Language Query
                   |
                   v
          Topic-aware Retrieval
                   |
                   v
          BIS Knowledge Base
                   |
          +--------+--------+
          |                 |
          v                 v
       PDF Sources       Web Sources
          |                 |
          +--------+--------+
                   |
                   v
             Relevant Chunks
                   |
                   v
              Gemini LLM
                   |
                   v
          Grounded AI Answer
                   |
                   v
        Sources / References
                   |
                   v
                  USER