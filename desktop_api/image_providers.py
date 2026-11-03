"""
Cadena de Proveedores de Generación de Imágenes para Parma (Image Provider Resilience Chain).
Permite generar retratos de personajes con tolerancia a fallos: si un proveedor gratuito
falla, está saturado o limitado por IP, conmuta automáticamente al siguiente proveedor
sin interrumpir la experiencia del usuario.
"""
import os
import time
import json
import base64
import random
import socket
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List


class ImageProviderResult:
    def __init__(self, success: bool, image_base64: str = "", provider: str = "", error: str = ""):
        self.success = success
        self.image_base64 = image_base64
        self.provider = provider
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "success": self.success,
            "provider": self.provider,
        }
        if self.success:
            d["image_base64"] = self.image_base64
        else:
            d["error"] = self.error
        return d


class BaseImageProvider:
    name: str = "base"

    def is_available(self) -> bool:
        return True

    def generate(self, prompt: str, **kwargs) -> ImageProviderResult:
        raise NotImplementedError


class PollinationsProvider(BaseImageProvider):
    name = "Pollinations.ai"
    _last_request_time: float = 0.0
    MIN_INTERVAL_SECONDS: float = 12.0  # Control de ritmo para evitar saturación de IP

    def generate(self, prompt: str, **kwargs) -> ImageProviderResult:
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.MIN_INTERVAL_SECONDS:
            sleep_needed = self.MIN_INTERVAL_SECONDS - elapsed
            if sleep_needed > 2.0:
                time.sleep(2.0)  # Pequeña espera de cortesía

        clean_prompt = prompt.strip()[:1800]
        encoded_prompt = urllib.parse.quote(clean_prompt)
        seed = random.randint(1, 99999999)
        model = kwargs.get("model", "flux")
        poll_model = model if model in ("flux", "turbo", "flux-real", "flux-anime") else "flux"

        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width=512&height=512&model={poll_model}&enhance=false&nologo=true&seed={seed}"
        )
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Parma/1.0"}
        )

        try:
            self.__class__._last_request_time = time.time()
            with urllib.request.urlopen(req, timeout=30) as resp:
                img_bytes = resp.read()
                if len(img_bytes) < 1000:
                    return ImageProviderResult(False, provider=self.name, error="Respuesta vacía de Pollinations")
                b64 = base64.b64encode(img_bytes).decode("ascii")
                return ImageProviderResult(True, image_base64=f"data:image/jpeg;base64,{b64}", provider=self.name)
        except Exception as e:
            return ImageProviderResult(False, provider=self.name, error=f"Fallo en Pollinations: {e}")


class AIHordeProvider(BaseImageProvider):
    name = "AI Horde (Respaldo Comunitario)"
    API_KEY = "0000000000"  # Clave anónima pública oficial

    def generate(self, prompt: str, **kwargs) -> ImageProviderResult:
        clean_prompt = prompt.strip()[:1000]
        payload = {
            "prompt": clean_prompt,
            "params": {
                "sampler_name": "k_euler",
                "cfg_scale": 7.5,
                "steps": 20,
                "width": 512,
                "height": 512,
                "n": 1,
            },
            "nsfw": False,
            "censor_nsfw": True,
            "models": ["ICBINP - I Can't Believe It's Not Photography", "stable_diffusion"],
        }

        submit_url = "https://aihorde.net/api/v2/generate/async"
        headers = {
            "Content-Type": "application/json",
            "apikey": self.API_KEY,
            "Client-Agent": "Parma:1.0.4:github.com/NMullerSM/Parma",
        }

        try:
            req = urllib.request.Request(submit_url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                req_id = res_data.get("id")

            if not req_id:
                return ImageProviderResult(False, provider=self.name, error="AI Horde no retornó ID de tarea")

            # Esperar resultado hasta 35 segundos
            status_url = f"https://aihorde.net/api/v2/generate/status/{req_id}"
            for _ in range(7):
                time.sleep(5.0)
                stat_req = urllib.request.Request(status_url, headers=headers)
                with urllib.request.urlopen(stat_req, timeout=15) as stat_resp:
                    stat_data = json.loads(stat_resp.read().decode("utf-8"))
                    if stat_data.get("done") and stat_data.get("generations"):
                        gen = stat_data["generations"][0]
                        img_str = gen.get("img")
                        if img_str:
                            if img_str.startswith("http"):
                                # Descargar imagen web
                                with urllib.request.urlopen(img_str, timeout=15) as img_resp:
                                    b64 = base64.b64encode(img_resp.read()).decode("ascii")
                                    return ImageProviderResult(True, image_base64=f"data:image/webp;base64,{b64}", provider=self.name)
                            else:
                                return ImageProviderResult(True, image_base64=f"data:image/webp;base64,{img_str}", provider=self.name)

            return ImageProviderResult(False, provider=self.name, error="Tiempo de espera agotado en la cola de AI Horde")
        except Exception as e:
            return ImageProviderResult(False, provider=self.name, error=f"Fallo en AI Horde: {e}")


class SDLocalProvider(BaseImageProvider):
    name = "Stable Diffusion WebUI Local"
    HOST = "127.0.0.1"
    PORT = 7860

    def is_available(self) -> bool:
        """Comprueba de inmediato si el puerto local de SD WebUI está abierto sin bloquear."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                return s.connect_ex((self.HOST, self.PORT)) == 0
        except Exception:
            return False

    def generate(self, prompt: str, **kwargs) -> ImageProviderResult:
        if not self.is_available():
            return ImageProviderResult(False, provider=self.name, error="Servidor SD WebUI local no detectado en puerto 7860")

        url = f"http://{self.HOST}:{self.PORT}/sdapi/v1/txt2img"
        payload = {
            "prompt": prompt,
            "steps": 20,
            "width": 512,
            "height": 512,
        }
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=40) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                images = data.get("images", [])
                if images:
                    return ImageProviderResult(True, image_base64=f"data:image/png;base64,{images[0]}", provider=self.name)
            return ImageProviderResult(False, provider=self.name, error="SD WebUI no generó ninguna imagen")
        except Exception as e:
            return ImageProviderResult(False, provider=self.name, error=f"Error conectando a SD WebUI: {e}")


class GoogleImagenProvider(BaseImageProvider):
    name = "Google Imagen 3 / Gemini"

    def generate(self, prompt: str, **kwargs) -> ImageProviderResult:
        clean_key = (kwargs.get("api_key") or "").strip()
        clean_url = (kwargs.get("api_url") or "").strip()

        endpoint = clean_url or "https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict"
        if "?" not in endpoint and clean_key:
            endpoint = f"{endpoint}?key={clean_key}"

        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "outputOptions": {"mimeType": "image/png"}
            }
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                preds = res_data.get("predictions", [])
                if preds and "bytesBase64Encoded" in preds[0]:
                    b64 = preds[0]["bytesBase64Encoded"]
                    return ImageProviderResult(True, image_base64=f"data:image/png;base64,{b64}", provider=self.name)
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            # Intento de fallback OpenAI-compatible de Google
            oa_endpoint = "https://generativelanguage.googleapis.com/v1beta/openai/images/generations"
            for fb_model in ["imagen-3.0-generate-002", "gemini-2.5-flash-image"]:
                try:
                    oa_payload = {"model": fb_model, "prompt": prompt, "n": 1, "response_format": "b64_json"}
                    oa_req = urllib.request.Request(
                        oa_endpoint,
                        data=json.dumps(oa_payload).encode("utf-8"),
                        headers={"Content-Type": "application/json", "Authorization": f"Bearer {clean_key}"}
                    )
                    with urllib.request.urlopen(oa_req, timeout=60) as resp2:
                        res_data2 = json.loads(resp2.read().decode("utf-8"))
                        if res_data2.get("data") and res_data2["data"][0].get("b64_json"):
                            b64 = res_data2["data"][0]["b64_json"]
                            return ImageProviderResult(True, image_base64=f"data:image/png;base64,{b64}", provider=self.name)
                except Exception:
                    continue
            return ImageProviderResult(False, provider=self.name, error=f"Google Imagen 3 (Error {he.code}): {err_body[:250]}")
        except Exception as e:
            return ImageProviderResult(False, provider=self.name, error=f"Error en Google AI: {e}")

        return ImageProviderResult(False, provider=self.name, error="Google AI no devolvió imagen válida")


class OpenAIImageProvider(BaseImageProvider):
    name = "OpenAI DALL-E"

    def generate(self, prompt: str, **kwargs) -> ImageProviderResult:
        clean_key = (kwargs.get("api_key") or "").strip()
        clean_url = (kwargs.get("api_url") or "").strip()
        model = kwargs.get("model") or "dall-e-3"

        endpoint = clean_url or "https://api.openai.com/v1/images/generations"
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "response_format": "b64_json"
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {clean_key}"}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                if res_data.get("data") and res_data["data"][0].get("b64_json"):
                    b64 = res_data["data"][0]["b64_json"]
                    return ImageProviderResult(True, image_base64=f"data:image/png;base64,{b64}", provider=self.name)
                elif res_data.get("data") and res_data["data"][0].get("url"):
                    return ImageProviderResult(True, image_base64=res_data["data"][0]["url"], provider=self.name)
            return ImageProviderResult(False, provider=self.name, error="OpenAI no retornó imagen")
        except Exception as e:
            return ImageProviderResult(False, provider=self.name, error=f"Error en OpenAI DALL-E: {e}")


class ImageProviderChain:
    """
    Cadena resiliente de resolución de retratos:
    1. Si se configuró clave del usuario (Google o OpenAI), intenta ese proveedor primero.
    2. Si es modo gratuito o falla el proveedor de pago: Pollinations -> AI Horde -> SD Local.
    """

    def __init__(self):
        self.pollinations = PollinationsProvider()
        self.ai_horde = AIHordeProvider()
        self.sd_local = SDLocalProvider()
        self.google = GoogleImagenProvider()
        self.openai = OpenAIImageProvider()

    def generate(
        self,
        prompt: str,
        provider: str = "pollinations",
        api_key: str = "",
        api_url: str = "",
        model: str = "",
    ) -> Dict[str, Any]:
        clean_key = (api_key or "").strip()
        p = (provider or "").lower().strip()

        # Detección de claves de usuario
        if clean_key.startswith("AIzaSy") or p == "google":
            res = self.google.generate(prompt, api_key=clean_key, api_url=api_url, model=model)
            if res.success:
                return res.to_dict()
            # Si falla Google, continuar con la cadena de respaldo gratuita
            print(f"[ImageChain] Google falló ({res.error}). Conmutando a cadena de respaldo gratuita...")

        elif clean_key.startswith("sk-") or p == "openai":
            res = self.openai.generate(prompt, api_key=clean_key, api_url=api_url, model=model)
            if res.success:
                return res.to_dict()
            print(f"[ImageChain] OpenAI falló ({res.error}). Conmutando a cadena de respaldo gratuita...")

        # Cadena gratuita: 1. Pollinations -> 2. AI Horde -> 3. SD Local
        errors = []

        # Paso 1: Pollinations
        res_poll = self.pollinations.generate(prompt, model=model)
        if res_poll.success:
            return res_poll.to_dict()
        errors.append(f"{res_poll.provider}: {res_poll.error}")

        # Paso 2: SD Local (si está activo localmente, es más rápido que AI Horde)
        if self.sd_local.is_available():
            res_sd = self.sd_local.generate(prompt)
            if res_sd.success:
                return res_sd.to_dict()
            errors.append(f"{res_sd.provider}: {res_sd.error}")

        # Paso 3: AI Horde
        res_horde = self.ai_horde.generate(prompt)
        if res_horde.success:
            return res_horde.to_dict()
        errors.append(f"{res_horde.provider}: {res_horde.error}")

        return {
            "success": False,
            "error": "Todos los proveedores de retratos fallaron: " + " | ".join(errors),
        }
