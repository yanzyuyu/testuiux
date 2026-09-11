import asyncio
import shutil
import subprocess
from rich.console import Console
import httpx

console = Console()


async def check_ollama_alive(api_base: str = "http://localhost:11434") -> bool:
    host = api_base.replace("/v1", "")
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(f"{host}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False


async def start_ollama_daemon() -> bool:
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        return False

    try:
        subprocess.Popen(
            [ollama_bin, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for _ in range(12):
            await asyncio.sleep(0.5)
            if await check_ollama_alive():
                return True
    except Exception:
        return False

    return False


async def ensure_model_pulled(api_base: str, model_name: str) -> bool:
    host = api_base.replace("/v1", "")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{host}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                installed = [m.get("name", "") for m in data.get("models", [])]
                installed_bases = [n.split(":")[0] for n in installed] + installed
                if model_name in installed or model_name in installed_bases:
                    return True

                with console.status(f"[bold cyan]Auto-pulling required model '{model_name}' from Ollama registry..."):
                    pull_resp = await client.post(
                        f"{host}/api/pull",
                        json={"name": model_name, "stream": False},
                        timeout=900.0,
                    )
                    return pull_resp.status_code == 200
    except Exception:
        return False
    return False


async def ensure_runtime_environment(
    api_base: str = "http://localhost:11434/v1",
    vision_model: str = "qwen2.5-vl:3b",
    triage_model: str = "qwen2.5:1.5b",
) -> str:
    is_alive = await check_ollama_alive(api_base)
    if not is_alive:
        console.print("[yellow]Ollama service is not running. Attempting auto-start...[/yellow]")
        is_alive = await start_ollama_daemon()

    if not is_alive:
        console.print("[yellow]Ollama not detected or not installed. Running in heuristic fallback mode.[/yellow]")
        return "mock"

    console.print("[green]Ollama service active.[/green]")
    await ensure_model_pulled(api_base, vision_model)
    await ensure_model_pulled(api_base, triage_model)
    return "api"
