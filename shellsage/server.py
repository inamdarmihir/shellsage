"""ShellSage MCP server + Anthropic API proxy.

Two integration modes on the same port:

  MCP (Claude Code tool registration):
    http://HOST:PORT/sse  — register with: claude mcp add --transport sse shellsage <url>

  Anthropic API proxy (intercepts bash commands before the agent sees them):
    Set ANTHROPIC_BASE_URL=http://HOST:PORT and run claude normally.
    All /v1/messages requests are forwarded to api.anthropic.com after
    translating any Bash tool_use commands for the current OS/shell.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import suppress

from shellsage.config import DB_PATH as _DEFAULT_DB
from shellsage.config import SERVER_HOST, SERVER_PORT
from shellsage.models import OS, CommandOutcome, Shell, ShellContext, Translation
from shellsage.translator import store_outcome, translate

try:
    from mcp.server.fastmcp import FastMCP  # type: ignore
except ImportError as e:
    raise ImportError("MCP support requires the 'mcp' extra: pip install 'shellsage[mcp]'") from e

ANTHROPIC_API_BASE = "https://api.anthropic.com"

mcp = FastMCP("shellsage")


# ── MCP tools ─────────────────────────────────────────────────────────────────


@mcp.tool()
def translate_command(command: str, project_root: str = ".") -> dict:
    """
    Translate a shell command for the current OS/shell environment.

    Returns the (possibly rewritten) command and metadata.
    Call this from a PreToolUse hook before executing any bash command.
    """
    ctx = ShellContext.get_cached(project_root=project_root)
    result: Translation = translate(command, ctx)
    return {
        "original": result.original,
        "translated": result.translated,
        "changed": result.was_changed,
        "confidence": round(result.confidence, 3),
        "source": result.source,
        "ref": result.ref,
        "shell": ctx.shell.value,
        "os": ctx.os.value,
    }


@mcp.tool()
def store_command_result(
    original: str,
    translated: str,
    shell: str,
    os_name: str,
    project_type: str,
    exit_code: int,
    error_snippet: str = "",
) -> dict:
    """
    Persist the outcome of a command execution back to local memory.

    Call this from a PostToolUse hook after every bash command runs.
    Successes reinforce translation mappings; failures enrich failure patterns.
    """
    outcome = CommandOutcome(
        original=original,
        translated=translated,
        shell=Shell(shell),
        os=OS(os_name),
        project_type=project_type,
        exit_code=exit_code,
        error_snippet=error_snippet[:300],
    )
    stored = store_outcome(outcome)
    return {"stored": stored, "succeeded": outcome.succeeded}


@mcp.tool()
def get_shell_context(project_root: str = ".") -> dict:
    """Return the detected shell/OS context for the current machine."""
    ctx = ShellContext.detect(project_root=project_root)
    return {
        "os": ctx.os.value,
        "shell": ctx.shell.value,
        "shell_version": ctx.shell_version,
        "project_type": ctx.project_type,
        "needs_translation": ctx.needs_translation,
    }


@mcp.tool()
def get_stats() -> dict:
    """Return collection sizes from local memory — useful for health checks."""
    try:
        from shellsage import store

        counts = store.get_stats()
        return {"status": "ok", "db": _DEFAULT_DB, "counts": counts}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


# ── Anthropic API proxy helpers ───────────────────────────────────────────────


def _translate_bash_input(input_json: str) -> str:
    """Translate the 'command' field in a Bash tool_use input JSON string.

    When a translation fires, appends a ``# shellsage-ref: <url>`` comment to
    the command so the citation travels with the command in agent logs.
    For passthrough commands the ref is added as a comment only when a known
    docs URL exists, keeping the command unchanged for unknown tools.
    """
    try:
        tool_input = json.loads(input_json)
        command = tool_input.get("command", "")
        if not command:
            return input_json
        ctx = ShellContext.get_cached()
        result = translate(command, ctx)
        final_cmd = result.translated
        if result.ref:
            final_cmd = f"{final_cmd}  # shellsage-ref: {result.ref}"
        if final_cmd != command:
            tool_input["command"] = final_cmd
            return json.dumps(tool_input)
    except Exception:
        pass
    return input_json


def _translate_tool_uses_in_response(response: dict) -> dict:
    """Translate Bash commands in a non-streaming Anthropic API response."""
    try:
        for block in response.get("content", []):
            if block.get("type") == "tool_use" and block.get("name") in ("Bash", "bash"):
                command = block.get("input", {}).get("command", "")
                if command:
                    ctx = ShellContext.get_cached()
                    result = translate(command, ctx)
                    final_cmd = result.translated
                    if result.ref:
                        final_cmd = f"{final_cmd}  # shellsage-ref: {result.ref}"
                    if final_cmd != command:
                        block["input"]["command"] = final_cmd
    except Exception:
        pass
    return response


async def _translate_sse_stream(upstream_resp, client) -> AsyncIterator[str]:
    """Yield SSE lines from *upstream_resp*, translating Bash tool_use commands.

    Bash tool input deltas are buffered until content_block_stop, then the
    assembled command is translated and re-emitted as a single delta.
    """
    # index -> list of partial_json fragments
    bash_buffers: dict[int, list[str]] = {}

    try:
        async for raw_line in upstream_resp.aiter_lines():
            if not raw_line:
                yield "\n"
                continue

            if not raw_line.startswith("data:"):
                yield raw_line + "\n"
                continue

            data_str = raw_line[5:].strip()
            if data_str == "[DONE]":
                yield "data: [DONE]\n\n"
                continue

            if not data_str:
                # Empty data field — skip rather than forward, as the client
                # would try JSON.parse("") → "Unexpected EOF".
                continue

            try:
                event = json.loads(data_str)
            except json.JSONDecodeError:
                # Malformed JSON from upstream; forward as-is and let the
                # client decide what to do with it.
                yield raw_line + "\n"
                continue

            etype = event.get("type", "")
            idx = event.get("index", 0)

            if etype == "content_block_start":
                block = event.get("content_block", {})
                if block.get("type") == "tool_use" and block.get("name") in ("Bash", "bash"):
                    bash_buffers[idx] = []
                yield f"data: {json.dumps(event)}\n\n"

            elif etype == "content_block_delta" and idx in bash_buffers:
                delta = event.get("delta", {})
                if delta.get("type") == "input_json_delta":
                    bash_buffers[idx].append(delta.get("partial_json", ""))
                    # buffered — don't emit yet
                else:
                    yield f"data: {json.dumps(event)}\n\n"

            elif etype == "content_block_stop" and idx in bash_buffers:
                parts = bash_buffers.pop(idx)
                assembled = "".join(parts) or "{}"
                translated = _translate_bash_input(assembled)
                # Re-emit as a single complete delta so the agent gets the translated command
                delta_event = {
                    "type": "content_block_delta",
                    "index": idx,
                    "delta": {"type": "input_json_delta", "partial_json": translated},
                }
                yield f"data: {json.dumps(delta_event)}\n\n"
                yield f"data: {json.dumps(event)}\n\n"

            else:
                yield f"data: {json.dumps(event)}\n\n"
    except Exception:
        # Network/timeout errors mid-stream: close cleanly so the client sees
        # EOF rather than a half-written JSON event.
        pass
    finally:
        await upstream_resp.aclose()
        await client.aclose()


# ── Starlette route handlers ──────────────────────────────────────────────────


async def _health(request):  # type: ignore[no-untyped-def]
    from starlette.responses import JSONResponse

    return JSONResponse({"status": "ok", "service": "shellsage"})


async def _proxy_messages(request):  # type: ignore[no-untyped-def]
    """Forward /v1/messages to Anthropic, intercepting Bash tool commands."""
    from starlette.responses import JSONResponse, Response, StreamingResponse

    try:
        import httpx  # type: ignore[import-untyped]
    except ImportError:
        return JSONResponse(
            {"error": "httpx is required for proxy mode: pip install 'shellsage[mcp]'"},
            status_code=500,
        )

    body = await request.body()
    try:
        body_json = json.loads(body)
    except json.JSONDecodeError:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)

    # Strip hop-by-hop headers before forwarding
    _hop_by_hop = {
        "host",
        "content-length",
        "transfer-encoding",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "upgrade",
    }
    forward_headers = {k: v for k, v in request.headers.items() if k.lower() not in _hop_by_hop}

    upstream_url = f"{ANTHROPIC_API_BASE}/v1/messages"
    stream = body_json.get("stream", False)

    if not stream:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(upstream_url, content=body, headers=forward_headers)
        resp_headers = {k: v for k, v in resp.headers.items() if k.lower() not in _hop_by_hop}
        try:
            result = _translate_tool_uses_in_response(resp.json())
            return JSONResponse(result, status_code=resp.status_code, headers=resp_headers)
        except Exception:
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                media_type=resp.headers.get("content-type", "application/json"),
                headers=resp_headers,
            )
    else:
        client = httpx.AsyncClient(timeout=120)
        req = client.build_request("POST", upstream_url, content=body, headers=forward_headers)
        upstream_resp = await client.send(req, stream=True)

        # Error responses have a JSON body, not an SSE stream.  Returning them
        # as text/event-stream would make the client try to JSON-parse raw JSON
        # lines → "Unexpected EOF".
        if upstream_resp.status_code >= 400:
            error_body = await upstream_resp.aread()
            await upstream_resp.aclose()
            await client.aclose()
            err_headers = {
                k: v for k, v in upstream_resp.headers.items() if k.lower() not in _hop_by_hop
            }
            return Response(
                content=error_body,
                status_code=upstream_resp.status_code,
                media_type=upstream_resp.headers.get("content-type", "application/json"),
                headers=err_headers,
            )

        resp_headers = {
            k: v
            for k, v in upstream_resp.headers.items()
            if k.lower() not in {*_hop_by_hop, "content-encoding"}
        }
        return StreamingResponse(
            _translate_sse_stream(upstream_resp, client),
            status_code=upstream_resp.status_code,
            media_type="text/event-stream",
            headers=resp_headers,
        )


# ── Server entrypoint ─────────────────────────────────────────────────────────


def run(transport: str = "stdio", port: int = SERVER_PORT, host: str = SERVER_HOST) -> None:
    if transport == "http":
        _run_http(host, port)
    else:
        mcp.run()


def _run_http(host: str, port: int) -> None:
    try:
        import uvicorn  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError("HTTP mode requires uvicorn: pip install 'shellsage[mcp]'") from None

    app = _build_app()
    uvicorn.run(app, host=host, port=port, log_level="error")


def _build_app():
    """Return an ASGI app combining the MCP server and the Anthropic proxy."""
    from starlette.applications import Starlette
    from starlette.routing import BaseRoute, Mount, Route

    # Try to get the MCP ASGI app from FastMCP
    mcp_app = None
    try:
        mcp_app = mcp.streamable_http_app()  # type: ignore[attr-defined]
    except AttributeError:
        with suppress(AttributeError):
            mcp_app = mcp.sse_app()  # type: ignore[attr-defined]

    routes: list[BaseRoute] = [
        Route("/v1/messages", endpoint=_proxy_messages, methods=["POST"]),
        Route("/health", endpoint=_health, methods=["GET"]),
    ]
    if mcp_app is not None:
        routes.append(Mount("/", app=mcp_app))

    return Starlette(routes=routes)


if __name__ == "__main__":
    run()
