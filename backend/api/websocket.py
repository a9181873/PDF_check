import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.task_store import TASK_STORE

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/compare/{task_id}")
async def compare_progress_socket(websocket: WebSocket, task_id: str):
    await websocket.accept()

    last_signature: tuple[str, int, str, str | None] | None = None
    try:
        while True:
            state = TASK_STORE.get(task_id)
            if not state:
                await websocket.send_json({"event": "error", "data": {"message": "Task not found"}})
                break

            signature = (
                state.status,
                state.progress_percent,
                state.current_step,
                state.error_message,
            )
            if signature != last_signature:
                await websocket.send_json(
                    {
                        "event": "progress",
                        "data": {
                            "status": state.status,
                            "step": state.current_step,
                            "percent": state.progress_percent,
                        },
                    }
                )
                last_signature = signature

            if state.status == "done" and state.result:
                await websocket.send_json(
                    {
                        "event": "complete",
                        "data": state.result.model_dump(mode="json"),
                    }
                )
                break

            if state.status == "error":
                await websocket.send_json(
                    {
                        "event": "error",
                        "data": {
                            "message": state.error_message or "Unknown processing error",
                        },
                    }
                )
                break

            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return
