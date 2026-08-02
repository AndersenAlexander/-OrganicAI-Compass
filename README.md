# OrganicAI Compass

## 1. Project Overview

OrganicAI Compass is a human-centred AI platform designed to help people discover their native talents, understand artificial intelligence without fear, and build a personal roadmap for positive human–AI collaboration.

The platform transforms fear and uncertainty about AI, robots, and automation into clarity, creativity, and meaningful contribution.

## Visual Concept

OrganicAI Compass is visually inspired by organic architecture and human-centred technology. The interface uses flowing shapes, soft gradients, glass panels, natural colors, and connected visual nodes to express the transition from fear and scarcity toward creativity, collaboration, contribution, and purpose.

The design direction is based on the concept of Organic Human-AI Symbiosis:

- The old paradigm: fear, repetitive work, competition, scarcity.
- The new paradigm: creativity, abundance, collaboration, contribution.
- The platform core: human diagnostic, talent map, fear transformation, AI coach, personal roadmap.

## 2. Thesis Context

This project is developed as a Master’s thesis in Software Engineering. It follows an engineering project approach, focused on designing, implementing, and testing a functional MVP.

Thesis title:

OrganicAI Compass: Design and Implementation of a Human-Centred AI Platform for Talent Discovery, Purpose Alignment, and Positive Human–Machine Collaboration.

## 3. Problem Statement

As AI, robotics, and automation evolve, many people feel uncertain about their role in the future. Existing career and learning platforms often focus on job matching or technical skills, but they rarely address fear, purpose, native talents, creativity, and positive human–AI collaboration.

OrganicAI Compass addresses this gap by helping users understand themselves and explore how AI can amplify their abilities rather than replace their human value.

## 4. Main Objective

The objective of the project is to design, implement, and evaluate an MVP of an AI-powered platform that helps users:

- identify native talents;
- transform fear about AI into constructive perspectives;
- interact with an AI Coach;
- generate a personal roadmap for learning, creativity, and contribution;
- explore positive human–AI collaboration.

## 5. Core MVP Features

### 5.1 Human Diagnostic

A multi-step questionnaire that collects information about the user’s interests, values, fears, learning style, and relationship with AI.

### 5.2 Talent Map

An AI-generated profile that identifies the user’s primary and secondary archetypes, strengths, values, contribution domains, and AI collaboration style.

### 5.3 Fear-to-Creativity Transformer

A module that allows users to input a fear about AI, automation, robots, or the future and receive a balanced, realistic, and constructive response.

### 5.4 AI Coach

A conversational assistant that helps users understand AI, explore their potential, and identify concrete ways to collaborate with technology.

### 5.5 Personal Roadmap

A personalized plan divided into 7-day, 30-day, and 6-month actions.

### 5.6 Voice Interaction

A voice layer that allows users to speak to the platform using speech-to-text and receive spoken responses using text-to-speech.

## 6. Technology Stack

### Frontend

- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Framer Motion

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Alembic

### AI and Voice

- LLM API integration
- Speech-to-text using Whisper or OpenAI transcription models
- Text-to-speech using ElevenLabs
- Optional RAG module using Chroma, FAISS, or pgvector

## 7. System Architecture

The platform follows a client-server architecture.

Frontend:

- user interface;
- diagnostic wizard;
- talent map visualization;
- chat interface;
- voice recorder;
- roadmap display.

Backend:

- API endpoints;
- database operations;
- AI prompt orchestration;
- speech-to-text;
- text-to-speech;
- roadmap generation.

Database:

- users;
- diagnostics;
- profiles;
- fear transformations;
- conversations;
- messages;
- roadmaps;
- voice files.

## 8. Main User Flow

1. The user opens the landing page.
2. The user starts the diagnostic.
3. The platform generates a human potential profile.
4. The user explores the talent map.
5. The user transforms a fear into a constructive perspective.
6. The user talks to the AI Coach.
7. The platform generates a personal roadmap.
8. The user can export or review the final report.

## 9. Environment Variables

Create a `.env` file in the backend folder:

```env
OPENAI_API_KEY=
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
DATABASE_URL=
```

## Voice Chat Integration

OrganicAI Compass includes an optional voice interaction layer.

The voice flow is:

1. The user records a voice message in the browser.
2. The frontend sends the audio file to the backend.
3. The backend transcribes the message using OpenAI transcription / Whisper.
4. The user confirms or edits the transcript.
5. The transcript is sent to the AI Coach.
6. The AI response is converted into speech using ElevenLabs.
7. The frontend plays the generated voice response.

Required backend environment variables:

```env
OPENAI_API_KEY=
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

The system never exposes API keys in the frontend. For local development, set `VITE_API_BASE_URL=http://localhost:8000/api` in the frontend environment if the FastAPI backend runs on port `8000`.

## RAG Knowledge Base

OrganicAI Compass includes a local retrieval-augmented generation layer for the AI Coach. Markdown sources live in `backend/knowledge_base` and cover AI literacy, responsible AI, privacy and voice data, human-AI collaboration, robotics awareness, talent discovery, future of work, and the OrganicAI methodology.

Backend services:

- `knowledge_loader.py` loads and chunks markdown documents.
- `embedding_service.py` generates OpenAI embeddings with `text-embedding-3-small` when `OPENAI_API_KEY` is available, with a local deterministic fallback for development.
- `rag_service.py` stores embeddings in a local JSON vector cache and performs cosine similarity search.

Endpoints:

- `POST /api/rag/reindex`
- `GET /api/rag/search?query=...`
- `POST /api/rag/ask`

Environment variables:

```env
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
RAG_TOP_K=4
```

The AI Coach searches the OrganicAI Knowledge Base before answering. When relevant sources are found, responses include `sources_used`, `confidence_note`, and `ethical_note`, and the frontend displays grounded-answer source chips.

## 3D Organic Visual Layer

The frontend uses React Three Fiber for lightweight procedural visuals:

- `OrganicSceneCanvas` enhances the landing hero with an organic human-AI scene.
- `HumanPotentialGlobe` provides a 3D Human Potential Map with selectable nodes.
- `AICoachOrb3D` reacts to coach states such as idle, listening, thinking, speaking, and error.

The 3D layer uses simple procedural geometry, no heavy imported models, and is lazy-loaded with React `Suspense`. Reduced-motion users receive the existing CSS/SVG fallback visuals.

## Visual Design System

The frontend uses CSS variables and shared `.organic-*` classes for light/dark parity, glass panels, rounded floating headers, luminous teal/green/cyan accents, premium cards, metric panels, chips, icon orbs, and 3D surfaces. Light mode uses cream, mist, sky, teal, and green; dark mode uses deep navy glass, cyan glow, and stronger holographic outlines.

## RAG UI

Grounded AI Coach answers display a visible grounded-answer label, source chips returned by the backend, a confidence note, and an ethical note. If no sources are returned, the UI avoids claiming knowledge-base grounding.

## 3D Components

React Three Fiber components provide the landing organic scene, Human Potential Globe, and AI Coach Orb. They are lazy-loaded and use procedural geometry, particles, glowing rings, and reduced-motion fallbacks.

## Voice Navigation

The AI Coach surfaces voice navigation examples such as Open Diagnostic, Show Roadmap, Open Human Potential Map, Switch Theme, Open Knowledge Base, Start Diagnostic, and Generate Report. The frontend includes visual confirmation messaging for recognized demo commands.

## User Accounts

OrganicAI Compass supports user accounts using email, password, and JWT authentication. Logged-in users can save diagnostics, profiles, roadmaps, and AI Coach conversations.

For the MVP, authentication uses:

- email and password registration;
- password hashing in the backend;
- JWT bearer tokens;
- frontend session persistence through localStorage;
- protected access to `/my-journey`.

## Floating Voice Chat

The platform includes a floating AI Coach widget available across all pages. Users can interact through text or voice.

Voice flow:

1. The user records a voice message.
2. The audio is transcribed using OpenAI transcription / Whisper.
3. The user confirms or edits the transcript.
4. The message is sent to OrganicAI Coach.
5. The AI response is converted to speech using ElevenLabs.
6. The audio response is played in the browser.

Required environment variables:

```env
OPENAI_API_KEY=
OPENAI_TRANSCRIPTION_MODEL=gpt-4o-mini-transcribe
ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
SECRET_KEY=
DATABASE_URL=sqlite:///./organicai.db
```

The floating widget is an MVP companion experience: it supports anonymous chat in the frontend and saves conversations when a valid JWT is present.

## Advanced Platform Modules

OrganicAI Compass includes several advanced modules designed to transform the platform from a simple AI assistant into a human-centred growth ecosystem.

### Human Potential Graph
A living visual map connecting talents, values, transformed fears, AI collaboration styles, contribution domains, learning paths, and next steps.

### Fear-to-Creativity Engine
A structured framework that turns anxiety about AI into clarity, agency, and small creative actions.

### AI Collaboration Style
A module that identifies how users work best with AI: as a mirror, co-creator, mentor, research assistant, builder assistant, or ethical challenger.

### Future Scenario Simulator
An interactive space for exploring possible futures shaped by AI, robotics, automation, and human choices.

### Human Contribution Projects
A project generator that helps users turn their profile into practical ideas for education, community, sustainability, design, robotics awareness, and ethical technology.

### Voice Companion
A voice-enabled AI Coach that supports different conversation modes and voice personalities.

### Memory of Growth
A timeline that tracks the user's journey from fear to clarity, from diagnosis to contribution.

### Ethical Reflection Layer
A cross-platform ethical note system that keeps human agency, verification, privacy, and responsible AI use visible.

### Community of Contribution
A future-oriented mock/demo space for matching complementary human roles around meaningful projects.

### AI Literacy Learning Paths
Personalized learning tracks for beginners, creatives, teachers, entrepreneurs, designers, and users who feel uncertain about technology.

### Visual Co-Creation Studio
A visual workspace for generating maps, boards, and concepts related to human-AI collaboration.

### Personal AI Constitution
A guided charter that helps users define their own values, boundaries, verification rules, and ethical principles for working with AI.

## Animation System

The frontend uses Motion for React to create calm, organic, accessible animations:
- scroll reveal;
- radial node animation;
- wizard transitions;
- chat popup animation;
- voice waveform pulse;
- roadmap timeline drawing;
- hover and tap micro-interactions;
- reduced-motion support.

## Visual Design System

OrganicAI Compass follows a visual design system inspired by organic architecture, human-AI symbiosis, and calm future-oriented interfaces.

The design references include:
- Landing Page Reference
- Human Diagnostic Reference
- Talent Map Reference
- AI Coach Reference
- Human-AI Roadmap Reference

The platform uses:
- deep navy navigation;
- warm cream backgrounds;
- teal and leaf green accents;
- rounded glassmorphism cards;
- organic SVG connections;
- radial human potential maps;
- animated roadmap timelines;
- voice-enabled AI coaching interface.

---

