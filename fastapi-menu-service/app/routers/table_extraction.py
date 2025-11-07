"""Table Extraction Router using Qwen models."""

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime

from app.services.qwen_table_extractor import QwenTableExtractor
from app.services.supabase_client import SupabaseClient
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/table-extraction", tags=["Table Extraction"])


# Pydantic models
class TableExtractionRequest(BaseModel):
    """Request model for table extraction."""
    text: str = Field(..., description="Text containing table data to extract")
    format: str = Field("markdown", description="Output format: markdown, json, csv, html")
    source: Optional[str] = Field(None, description="Source of the text (ocr, manual, etc.)")
    image_url: Optional[str] = Field(None, description="Original image URL if from OCR")


class TableExtractionResponse(BaseModel):
    """Response model for table extraction."""
    success: bool
    raw_table: str
    format: str
    model_used: str
    tokens_used: int
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    processing_time_ms: Optional[int] = None
    timestamp: str
    error: Optional[str] = None
    table_id: Optional[str] = None


class BatchTableExtractionRequest(BaseModel):
    """Request model for batch table extraction."""
    items: List[TableExtractionRequest] = Field(..., description="List of table extraction requests")


class BatchTableExtractionResponse(BaseModel):
    """Response model for batch table extraction."""
    results: List[TableExtractionResponse]
    total_tokens: int
    processing_time_ms: int


# Dependency injection
def get_qwen_extractor() -> QwenTableExtractor:
    """Get Qwen table extractor instance."""
    # This would typically come from settings
    import os
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Qwen API key not configured")
    return QwenTableExtractor(api_key)


def get_supabase_client() -> SupabaseClient:
    """Get Supabase client instance."""
    return SupabaseClient()


@router.post("/extract", response_model=TableExtractionResponse)
async def extract_table(
    request: TableExtractionRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    extractor: QwenTableExtractor = Depends(get_qwen_extractor),
    supabase: SupabaseClient = Depends(get_supabase_client)
) -> TableExtractionResponse:
    """
    Extract table data from text using Qwen model.

    - Validates input text
    - Uses Qwen model for extraction
    - Stores result in Supabase
    - Returns formatted table data
    """
    try:
        logger.info(f"Extracting table from text (length: {len(request.text)}) for user {current_user.get('id')}")

        # Extract table data
        result = await extractor.extract_table_data(
            text=request.text,
            table_format=request.format
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=f"Table extraction failed: {result.get('error', 'Unknown error')}")

        # Store in Supabase
        table_record = {
            "user_id": current_user["id"],
            "source_text": request.text,
            "extracted_table": result["raw_table"],
            "format": result["format"],
            "model_used": result["model_used"],
            "tokens_used": result["tokens_used"],
            "source": request.source or "manual",
            "image_url": request.image_url,
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            response = supabase.client.table("extracted_tables").insert(table_record).execute()
            table_id = response.data[0]["id"] if response.data else None
        except Exception as e:
            logger.warning(f"Failed to store table in Supabase: {e}")
            table_id = None

        return TableExtractionResponse(
            **result,
            table_id=table_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in table extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Table extraction failed: {str(e)}")


@router.post("/extract-from-ocr", response_model=TableExtractionResponse)
async def extract_table_from_ocr(
    ocr_text: str = Query(..., description="OCR text from image"),
    image_url: Optional[str] = Query(None, description="Original image URL"),
    format: str = Query("markdown", description="Output format"),
    current_user: dict = Depends(get_current_user),
    extractor: QwenTableExtractor = Depends(get_qwen_extractor),
    supabase: SupabaseClient = Depends(get_supabase_client)
) -> TableExtractionResponse:
    """
    Extract table data specifically from OCR text.

    Optimized for menu/document OCR results.
    """
    try:
        logger.info(f"Extracting table from OCR text for user {current_user.get('id')}")

        # Use OCR-specific extraction
        result = await extractor.extract_tables_from_image_ocr(
            ocr_text=ocr_text,
            image_url=image_url
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=f"OCR table extraction failed: {result.get('error', 'Unknown error')}")

        # Store in Supabase
        table_record = {
            "user_id": current_user["id"],
            "source_text": ocr_text,
            "extracted_table": result["raw_table"],
            "format": result["format"],
            "model_used": result["model_used"],
            "tokens_used": result["tokens_used"],
            "source": "ocr_image",
            "image_url": image_url,
            "created_at": datetime.utcnow().isoformat()
        }

        try:
            response = supabase.client.table("extracted_tables").insert(table_record).execute()
            table_id = response.data[0]["id"] if response.data else None
        except Exception as e:
            logger.warning(f"Failed to store OCR table in Supabase: {e}")
            table_id = None

        return TableExtractionResponse(
            **result,
            table_id=table_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in OCR table extraction: {e}")
        raise HTTPException(status_code=500, detail=f"OCR table extraction failed: {str(e)}")


@router.post("/extract-batch", response_model=BatchTableExtractionResponse)
async def extract_tables_batch(
    request: BatchTableExtractionRequest,
    current_user: dict = Depends(get_current_user),
    extractor: QwenTableExtractor = Depends(get_qwen_extractor),
    supabase: SupabaseClient = Depends(get_supabase_client)
) -> BatchTableExtractionResponse:
    """
    Extract tables from multiple text sources in batch.

    Processes multiple extraction requests efficiently.
    """
    import time
    start_time = time.time()

    try:
        logger.info(f"Batch extracting {len(request.items)} tables for user {current_user.get('id')}")

        results = []
        total_tokens = 0

        for item in request.items:
            try:
                result = await extractor.extract_table_data(
                    text=item.text,
                    table_format=item.format
                )

                if result["success"]:
                    # Store in Supabase
                    table_record = {
                        "user_id": current_user["id"],
                        "source_text": item.text,
                        "extracted_table": result["raw_table"],
                        "format": result["format"],
                        "model_used": result["model_used"],
                        "tokens_used": result["tokens_used"],
                        "source": item.source or "batch",
                        "image_url": item.image_url,
                        "created_at": datetime.utcnow().isoformat()
                    }

                    try:
                        response = supabase.client.table("extracted_tables").insert(table_record).execute()
                        table_id = response.data[0]["id"] if response.data else None
                        result["table_id"] = table_id
                    except Exception as e:
                        logger.warning(f"Failed to store batch table in Supabase: {e}")

                    total_tokens += result["tokens_used"]

                results.append(TableExtractionResponse(**result))

            except Exception as e:
                logger.error(f"Error processing batch item: {e}")
                results.append(TableExtractionResponse(
                    success=False,
                    raw_table="",
                    format=item.format,
                    model_used=extractor.model,
                    tokens_used=0,
                    error=str(e),
                    timestamp=datetime.utcnow().isoformat()
                ))

        processing_time = int((time.time() - start_time) * 1000)

        return BatchTableExtractionResponse(
            results=results,
            total_tokens=total_tokens,
            processing_time_ms=processing_time
        )

    except Exception as e:
        logger.error(f"Unexpected error in batch table extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Batch table extraction failed: {str(e)}")


@router.get("/history", response_model=List[Dict[str, Any]])
async def get_table_extraction_history(
    limit: int = Query(50, description="Maximum number of results"),
    offset: int = Query(0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
) -> List[Dict[str, Any]]:
    """
    Get user's table extraction history.

    Returns previously extracted tables with metadata.
    """
    try:
        response = supabase.client.table("extracted_tables").select("*").eq("user_id", current_user["id"]).order("created_at", desc=True).range(offset, offset + limit - 1).execute()

        return response.data or []

    except Exception as e:
        logger.error(f"Error fetching table extraction history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@router.delete("/history/{table_id}")
async def delete_extracted_table(
    table_id: str,
    current_user: dict = Depends(get_current_user),
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """
    Delete a previously extracted table.

    Only allows deletion of user's own tables.
    """
    try:
        # First check if the table belongs to the user
        response = supabase.client.table("extracted_tables").select("user_id").eq("id", table_id).execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Table not found")

        if response.data[0]["user_id"] != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to delete this table")

        # Delete the table
        supabase.client.table("extracted_tables").delete().eq("id", table_id).execute()

        return {"success": True, "message": "Table deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting extracted table: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete table: {str(e)}")