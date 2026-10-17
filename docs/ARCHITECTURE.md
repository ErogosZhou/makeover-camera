# 换装相机 Architecture

## Overview

换装相机 is an AI-powered interior design application. It allows users to upload a photo of a room and generates a redesigned version of that room, along with a shopping list of items found in the new design.

## Core Components

### 1. Frontend (Mini Program)
- Built with WeChat Mini Program framework.
- Handles user image uploads, displays generation progress, and presents the final design and shopping list.

### 2. Backend (FastAPI)
- Built with Python and FastAPI.
- Orchestrates the AI generation process.
- **Key Modules:**
  - `api/routes.py`: Defines API endpoints for uploading images, starting generation tasks, and polling task status.
  - `services/image_generator.py`: Handles the core logic of calling AI models (VLLM for prompt generation, Seedream for image generation) to create the redesigned room.
  - `services/product_service.py`: Matches identified items in the generated image with real-world products.
  - `services/cos_storage.py`: Handles uploading images to Tencent Cloud Object Storage (COS).

## Generation Workflow (V2)

1. **Upload:** User uploads an image via the Mini Program. The backend saves it (locally or to COS) and returns an `image_id`.
2. **Start Task:** Frontend calls `/v2/transform` with the `image_id`. Backend creates a task and starts background processing.
3. **Prompt & Item Generation (VLLM):** The backend sends the original image to a Vision LLM (e.g., Qwen-VL). The LLM analyzes the room and generates:
   - A detailed prompt for the image generation model.
   - A design description (design brief).
   - A list of key furniture/decor items to include in the new design.
4. **Image Generation (Seedream):** Concurrently, the generated prompt is sent to an image generation model (e.g., Seedream) to create the new room image.
5. **Product Matching:** As the LLM identifies items (step 3), the backend immediately starts matching them with real products using `ProductMatcherService`.
6. **Polling:** The frontend polls `/task/{task_id}` to get progress updates, the design description (for a typewriter effect), and eventually the final image and shopping list.

## Data Models

- `GenerationResult`: Represents the state and result of a generation task.
- `ShoppingItem`: Represents an item identified in the design and its matched real-world products.
